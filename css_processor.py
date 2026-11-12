import os
import re

from pykyll.fileutils import path_diff, ensure_parent_dirs
from pykyll.fonts import AvailableFonts, FontInfo
from pykyll.templater import Templater

# font-family, the font shorthand, or a custom property ending in "font" (e.g. --heading-font)
font_declaration_re = re.compile(r"(?:^|[\s;{])(?:font-family|font|--[\w-]*font)\s*:\s*([^;{}]*)")


class CssProcessor:

    def __init__(self, available_fonts : AvailableFonts, fonts_target_dir: str, woff=False, **template_args):
        """
        Adds @font-face rules for any available fonts used, and compiles .scss files.
        Web fonts are generated as woff2 - and also as woff, if woff is True (only needed for very old browsers)
        """
        self.available_fonts = available_fonts
        self.all_required_fonts = set()
        self.fonts_target_dir = fonts_target_dir
        self.woff = woff
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

    # The output also depends on the available fonts, so CSS is processed even if the source hasn't changed
    # (which also finds the fonts it requires, to be synced). The output is only written if it has changed
    process.always_process = True

    def process_css_file(self, source_path: str, target_path: str) -> bool:
        with open(source_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.process_css(content, target_path, always_write=True)

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
            output = "\n".join(lines)
            if not os.path.exists(target_path) or read_file(target_path) != output:
                ensure_parent_dirs(target_path)
                with open(target_path, "w", encoding="utf-8") as of:
                    of.write(output)
                if processed_lines:
                    print(f"Added web fonts to CSS for {target_path}")
        return len(lines) > 0

    def find_required_fonts(self, css: str) -> list[FontInfo]:
        required_fonts = {}
        for match in font_declaration_re.finditer(css):
            for font_family in match.group(1).split(","):
                words = font_family.strip().strip("'").strip('"').split()
                # The font shorthand has other values before the family (e.g. `bold 1.2em "Nanum Gothic"`)
                for i in range(len(words)):
                    for font in self.available_fonts.find_fonts(" ".join(words[i:]).strip("'").strip('"')):
                        required_fonts[font.slug] = font
        return sorted(required_fonts.values(), key=lambda font: font.slug)

    def process_css_lines(self, css_lines: list[str], target_path: str) -> list[str]:
        required_fonts = self.find_required_fonts("\n".join(css_lines))
        if not required_fonts:
            return []

        relative_path_to_fonts = path_diff(os.path.dirname(target_path), self.fonts_target_dir)

        processed_lines = ["/* web fonts */"]
        for font in required_fonts:
            self.all_required_fonts.add(font)
            basename = os.path.join(relative_path_to_fonts, font.slug)
            sources = f"url('{basename}.woff2') format('woff2')"
            if self.woff:
                sources += f",\n       url('{basename}.woff') format('woff')"
            processed_lines += [
                "@font-face {",
                f"  font-family: '{font.font_family}';",
                f"  src: {sources};",
                f"  font-weight: {font.font_weight};",
                f"  font-style: {font.font_style};",
                f"  font-display: {font.font_display};",
            ]
            if font.unicode_range:
                processed_lines.append(f"  unicode-range: {font.unicode_range};")
            processed_lines.append("}")

        processed_lines = processed_lines + ["/* end of web fonts */", ""] + css_lines
        return processed_lines

    def sync_fonts(self, target_root: str):
        for font in sorted(self.all_required_fonts, key=lambda font: font.slug):
            self.available_fonts.sync_font(font, self.fonts_target_dir, woff=self.woff)

    def process_scss(self, source_path: str, target_path: str) -> bool:
        try:
            import sass
        except ImportError as e:
            raise ImportError("Compiling SCSS needs pykyll's scss extra (e.g. pykyll[scss])") from e
        css = sass.compile(filename=source_path)
        self.process_css(css, target_path, always_write=True)
        return True


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
