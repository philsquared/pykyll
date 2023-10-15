import os

import yaml
from fontTools.ttLib import TTFont

from pykyll.fileutils import ensure_dirs
from pykyll.html import slugify


class FontInfo:

    def __init__(self, font_dir: str):
        self.font_dir = font_dir
        self.otf_file = None
        info_file = None
        for filename in os.listdir(font_dir):
            _, ext = os.path.splitext(filename)
            match ext:
                case ".otf":
                    self.otf_file = filename
                case ".ttf":
                    pass
                case ".yml":
                    info_file = filename
                case "":
                    pass
                case _:
                    raise Exception(f"Unrecognised file type, {filename} in font directory {font_dir}")
        if not self.otf_file:
            raise Exception(f"No otf file found in {font_dir}")
        if not info_file:
            raise Exception(f"No info.yml file found in {font_dir}")

        with open(os.path.join(font_dir, info_file), 'r') as f:
            data = yaml.safe_load(f)

        self.font_family = data["font-family"]
        self.font_weight = data["font-weight"]
        self.font_style = data["font-style"]
        self.slug = slugify(self.font_family)


class AvailableFonts:
    def __init__(self, fonts_dir: str):

        self.fonts = {}

        for font_dir in os.listdir(fonts_dir):
            font_dir = os.path.join(fonts_dir, font_dir)
            if os.path.isdir(font_dir):
                info = FontInfo(font_dir)
                self.fonts[info.font_family.lower()] = info

    def find_font(self, font_family: str) -> FontInfo | None:
        return self.fonts.get(font_family.lower())

    def sync_font(self, font: FontInfo, target_dir: str, always_copy=False) -> bool:
        otf_path = os.path.join(font.font_dir, font.otf_file)
        target_base_path = os.path.join(target_dir, font.slug)
        woff_path = f"{target_base_path}.woff"
        woff2_path = f"{target_base_path}.woff2"

        woff_exists = os.path.exists(woff_path)
        woff2_exists = os.path.exists(woff2_path)
        if not always_copy and woff_exists and woff2_exists:
            source_mod_time = os.path.getmtime(otf_path)
            target_mod_time = os.path.getmtime(woff_path)
            target2_mod_time = os.path.getmtime(woff2_path)
            if source_mod_time < target_mod_time and source_mod_time < target2_mod_time:
                return False

        print(f"syncing {otf_path} into {target_base_path}.woff/2")
        ensure_dirs(target_dir)
        otf_font = TTFont(otf_path)
        otf_font.flavor = "woff2"
        otf_font.save(woff2_path)
        otf_font.flavor = "woff"
        otf_font.save(woff_path)

        return True
