import os
import shutil

import yaml

from pykyll.fileutils import ensure_dirs, needs_sync
from pykyll.htmlutils import slugify

# Named unicode ranges that can be given as a font's unicode-range (these match Google Fonts' subsets)
named_unicode_ranges = {
    "latin": "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, "
             "U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
    "latin-ext": "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, "
                 "U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, "
                 "U+A720-A7FF",
}


def parse_unicode_range(unicode_range: str) -> list[int]:
    """
    Parses a CSS unicode-range (e.g. "U+0000-00FF, U+0131, U+4??") into the list of code points it covers
    """
    code_points = []
    for part in unicode_range.split(","):
        part = part.strip().upper().removeprefix("U+")
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-")
        else:
            # A single code point, or a range with wildcards
            start, end = part.replace("?", "0"), part.replace("?", "F")
        code_points.extend(range(int(start, 16), int(end, 16) + 1))
    return code_points


class FontInfo:
    """
    A font face (a font family in one weight and style), from a directory containing a single font file,
    and optionally a yml file of info about it (and a txt file, such as a licence, which is copied alongside)
    """

    def __init__(self, font_dir: str):
        self.font_dir = font_dir
        self.otf_file = None
        self.txt_file = None
        self.info_file = None
        for filename in sorted(os.listdir(font_dir)):
            _, ext = os.path.splitext(filename)
            match ext:
                case ".otf" | ".ttf":
                    if self.otf_file:
                        raise Exception(f"More than one font file ({self.otf_file} and {filename}) in font directory {font_dir}")
                    self.otf_file = filename
                case ".yml":
                    self.info_file = filename
                case ".txt":
                    self.txt_file = filename
                case "":
                    pass
                case _:
                    raise Exception(f"Unrecognised file type, {filename} in font directory {font_dir}")
        if not self.otf_file:
            raise Exception(f"No otf file found in {font_dir}")

        data = {}
        if self.info_file:
            with open(os.path.join(font_dir, self.info_file), 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

        self.font_family = data.get("font-family", os.path.split(font_dir)[-1])
        self.font_weight = str(data.get("font-weight", "normal"))
        self.font_style = str(data.get("font-style", "normal"))
        self.font_display = data.get("font-display", "swap")

        # If given, the font is subset to just these characters (as a CSS unicode-range, or one of the named ranges)
        unicode_range = data.get("unicode-range")
        self.unicode_range = named_unicode_ranges.get(unicode_range, unicode_range)

        # Regular faces are just named after the family, other faces also by their weight and/or style
        self.slug = slugify(self.font_family)
        if self.font_weight not in ("normal", "400"):
            self.slug += f"-{slugify(self.font_weight)}"
        if self.font_style != "normal":
            self.slug += f"-{slugify(self.font_style)}"

    @property
    def source_paths(self) -> list[str]:
        """
        The files that the web font is generated from
        """
        return [os.path.join(self.font_dir, filename) for filename in (self.otf_file, self.info_file) if filename]


class AvailableFonts:
    def __init__(self, fonts_dir: str):

        # All the faces of each family (keyed by lower case family name)
        self.faces: dict[str, list[FontInfo]] = {}

        if os.path.exists(fonts_dir):
            for font_dir in sorted(os.listdir(fonts_dir)):
                font_dir = os.path.join(fonts_dir, font_dir)
                if os.path.isdir(font_dir):
                    info = FontInfo(font_dir)
                    faces = self.faces.setdefault(info.font_family.lower(), [])
                    for face in faces:
                        if face.slug == info.slug:
                            raise Exception(f"Font directories {face.font_dir} and {font_dir} are the same face "
                                            f"({info.font_family}, weight: {info.font_weight}, style: {info.font_style})")
                    faces.append(info)

        # The first face of each family (for compatibility, from when there could only be one)
        self.fonts = {family: faces[0] for family, faces in self.faces.items()}

    def find_fonts(self, font_family: str) -> list[FontInfo]:
        """
        Finds all the faces of a font family
        """
        return self.faces.get(font_family.lower(), [])

    def find_font(self, font_family: str) -> FontInfo | None:
        return self.fonts.get(font_family.lower())

    def sync_font(self, font: FontInfo, target_dir: str, always_copy=False, woff=False) -> bool:
        """
        Generates the woff2 (and optionally woff) web font, if out of date
        """
        target_base_path = os.path.join(target_dir, font.slug)
        flavors = ["woff2", "woff"] if woff else ["woff2"]
        target_paths = {flavor: f"{target_base_path}.{flavor}" for flavor in flavors}

        if font.txt_file:
            txt_source_path = os.path.join(font.font_dir, font.txt_file)
            txt_target_path = os.path.join(target_dir, font.txt_file)
        else:
            txt_source_path = None
            txt_target_path = None

        if not always_copy and \
                not any(needs_sync(source_path, target_path)
                        for source_path in font.source_paths for target_path in target_paths.values()) and \
                not(txt_source_path is not None and needs_sync(txt_source_path, txt_target_path)):
            return False

        try:
            from fontTools.ttLib import TTFont
            from fontTools import subset
        except ImportError as e:
            raise ImportError("Converting fonts needs pykyll's fonts extra (e.g. pykyll[fonts])") from e
        otf_path = os.path.join(font.font_dir, font.otf_file)
        print(f"syncing {otf_path} into {target_base_path}")
        ensure_dirs(target_dir)
        otf_font = TTFont(otf_path)
        if font.unicode_range:
            subsetter = subset.Subsetter()
            subsetter.populate(unicodes=parse_unicode_range(font.unicode_range))
            subsetter.subset(otf_font)
        for flavor, target_path in target_paths.items():
            otf_font.flavor = flavor
            otf_font.save(target_path)
        if txt_source_path:
            shutil.copy2(txt_source_path, txt_target_path)
        return True
