import os
import shutil

import yaml
from fontTools.ttLib import TTFont

from pykyll.fileutils import ensure_dirs, needs_sync
from pykyll.html import slugify


class FontInfo:

    def __init__(self, font_dir: str):
        self.font_dir = font_dir
        self.otf_file = None
        self.txt_file = None
        info_file = None
        for filename in os.listdir(font_dir):
            _, ext = os.path.splitext(filename)
            match ext:
                case ".otf":
                    self.otf_file = filename
                case ".ttf":
                    self.otf_file = filename
                    pass
                case ".yml":
                    info_file = filename
                case ".txt":
                    self.txt_file = filename
                case "":
                    pass
                case _:
                    raise Exception(f"Unrecognised file type, {filename} in font directory {font_dir}")
        if not self.otf_file:
            raise Exception(f"No otf file found in {font_dir}")
        if info_file:
            with open(os.path.join(font_dir, info_file), 'r') as f:
                data = yaml.safe_load(f)

            self.font_family = data["font-family"]
            self.font_weight = data["font-weight"]
            self.font_style = data["font-style"]
        else:
            self.font_family = os.path.split(font_dir)[-1]
            self.font_weight = "normal"
            self.font_style = "normal"

        self.slug = slugify(self.font_family)


class AvailableFonts:
    def __init__(self, fonts_dir: str):

        self.fonts = {}

        if os.path.exists(fonts_dir):
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

        if font.txt_file:
            txt_source_path = os.path.join(font.font_dir, font.txt_file)
            txt_target_path = os.path.join(target_dir, font.txt_file)
        else:
            txt_source_path = None
            txt_target_path = None

        needs_update = always_copy
        if not always_copy and \
                not needs_sync(otf_path, woff_path) and \
                not needs_sync(otf_path, woff2_path) and \
                not(txt_source_path is not None and needs_sync(txt_source_path, txt_target_path)):
            return False

        print(f"syncing {otf_path} into {target_base_path}")
        ensure_dirs(target_dir)
        otf_font = TTFont(otf_path)
        otf_font.flavor = "woff2"
        otf_font.save(woff2_path)
        otf_font.flavor = "woff"
        otf_font.save(woff_path)
        if txt_source_path:
            shutil.copy2(txt_source_path, txt_target_path)
        return True
