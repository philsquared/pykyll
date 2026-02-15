import os
import re

import sass

from pykyll.fileutils import path_diff, ensure_parent_dirs
from pykyll.fonts import AvailableFonts
from pykyll.templater import Templater

font_re = re.compile(r"\s*font-family\s*:\s*(.*?);")
font_var_re = re.compile(r"\s*--.*?font\s*:\s*(.*?);")


class CssProcessor:

    def __init__(self, available_fonts : AvailableFonts, fonts_target_dir: str, **template_args):
        self.available_fonts = available_fonts
        self.all_required_fonts = set()
        self.fonts_target_dir = fonts_target_dir
        self.template_args = template_args

    def process(self, source_path: str, target_path: str) -> bool:
        path_without_ext, ext = os.path.splitext(target_path)
        match ext:
            case ".css":
                return self.process_css_file(source_path, target_path)
            case ".scss":
                filename = os.path.basename(source_path)
                if filename.startswith("_"):
                    # This is a partial file (to be imported) so shouldn't be synced
                    return True
                return self.process_scss(source_path, f"{path_without_ext}.css")
            case _:
                return False

    def process_css_file(self, source_path: str, target_path: str) -> bool:
        with open(source_path, "r") as f:
            content = f.read()
        return self.process_css(content, target_path)

    def process_css(self, content: str, target_path: str, always_write=False) -> bool:
        if self.template_args:
            content = Templater.render_from_string_raw (content, filters=None, **self.template_args)

        lines = content.split("\n")

        processed_lines = self.process_css_lines(lines, target_path)
        if processed_lines:
            lines = processed_lines
        elif not always_write:
            lines = []
        if lines:
            ensure_parent_dirs(target_path)
            with open(target_path, "w") as of:
                for line in lines:
                    of.write(f"{line}\n")
        return len(processed_lines) > 0

    def process_css_lines(self, css_lines: list[str], target_path: str) -> list[str]:
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
            print(f"Added font {font.font_family} to CSS for {target_path}")

        processed_lines = processed_lines + ["/* end of web fonts */", ""] + css_lines
        return processed_lines

    def sync_fonts(self, target_root: str):
        for font in self.all_required_fonts:
            self.available_fonts.sync_font(font, self.fonts_target_dir)

    def process_scss(self, source_path: str, target_path: str) -> bool:
        css = sass.compile(filename=source_path)
        self.process_css(css, target_path, always_write=True)
        return True
