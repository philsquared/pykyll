import os
import re

import sass

from pykyll.fileutils import path_diff, ensure_parent_dirs
from pykyll.fonts import AvailableFonts

font_re = re.compile(r"\s*font-family\s*:\s*(.*?);")
font_var_re = re.compile(r"\s*--.*?font\s*:\s*(.*?);")


class CssProcessor:

    def __init__(self, available_fonts : AvailableFonts, fonts_target_dir: str):
        self.available_fonts = available_fonts
        self.all_required_fonts = set()
        self.fonts_target_dir = fonts_target_dir

    def process(self, source_path: str, target_path: str) -> bool:
        required_fonts = set()
        path_without_ext, ext = os.path.splitext(target_path)
        match ext:
            case ".css":
                return self.process_css(source_path, target_path)
            case ".scss":
                return self.process_scss(source_path, f"{path_without_ext}.css")
            case _:
                return False

    def process_css(self, source_path: str, target_path: str) -> bool:
        with open(source_path, "r") as f:
            lines = f.readlines()

        processed_lines = self.process_css_lines(lines, target_path)
        if processed_lines:
            ensure_parent_dirs(target_path)
            with open(target_path, "w") as of:
                of.writelines(processed_lines)
            return True
        else:
            return False

    def process_css_lines(self, css_lines: [str], target_path: str) -> [str]:
        # !TBD: rewrite this as a generator
        required_fonts = set()

        for line in css_lines:
            match = font_re.match(line)
            if not match:
                match = font_var_re.match(line)

            if match:
                fonts = [f.strip().strip("'").strip('"') for f in match.group(1).split(",")]
                for font_family in fonts:
                    font = self.available_fonts.find_font(font_family)
                    if font:
                        required_fonts.add(font)
                        self.all_required_fonts.add(font)

        if not required_fonts:
            return []

        relative_path_to_fonts = path_diff(os.path.dirname(target_path), self.fonts_target_dir)

        processed_lines = ["/* web fonts */"]
        for font in required_fonts:
            basename = os.path.join(relative_path_to_fonts, font.slug)
            font_lines = [
                "@font-face {\n",
                f"  font-family: '{font.font_family}';\n",
                f"  src: url('{basename}.woff2') format('woff2'),\n",
                f"       url('{basename}.woff') format('woff');\n",
                f"  font-weight: {font.font_weight};\n",
                f"  font-style: {font.font_style};\n"
                "}\n"
            ]
            processed_lines = processed_lines + font_lines

        processed_lines = processed_lines + ["/* end of web fonts */", ""] + css_lines
        return processed_lines

    def sync_fonts(self, target_root: str):
        for font in self.all_required_fonts:
            self.available_fonts.sync_font(font, self.fonts_target_dir)

    def process_scss(self, source_path: str, target_path: str) -> bool:
        with open(source_path, "r") as f:
            scss = f.read()

        css = sass.compile(string=scss)
        lines = css.split("\n")
        processed_lines = self.process_css_lines(lines, target_path)
        if processed_lines:
            lines = processed_lines

        ensure_parent_dirs(target_path)
        with open(target_path, "w") as of:
            for line in lines:
                of.write(f"{line}\n")
        return True
