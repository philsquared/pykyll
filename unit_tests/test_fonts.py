import os

import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from pykyll.css_processor import CssProcessor
from pykyll.fileutils import sync_files
from pykyll.fonts import AvailableFonts, parse_unicode_range


def make_font(path, chars="AB가"):
    """
    Writes a minimal TrueType font, with a (square) glyph for each of chars
    """
    names = [".notdef"] + [f"uni{ord(c):04X}" for c in chars]
    pen = TTGlyphPen(None)
    pen.moveTo((0, 0)); pen.lineTo((0, 500)); pen.lineTo((500, 500)); pen.lineTo((500, 0)); pen.closePath()
    glyph = pen.glyph()
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap({ord(c): name for c, name in zip(chars, names[1:])})
    fb.setupGlyf({name: glyph for name in names})
    fb.setupHorizontalMetrics({name: (600, 0) for name in names})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Test", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()
    fb.save(str(path))


def add_face(fonts_dir, dir_name, yml=None):
    face_dir = fonts_dir / dir_name
    face_dir.mkdir(parents=True)
    make_font(face_dir / "font.ttf")
    if yml:
        (face_dir / "info.yml").write_text(yml)


@pytest.fixture
def fonts_dir(tmp_path):
    fonts_dir = tmp_path / "_fonts"
    add_face(fonts_dir, "Nanum Gothic", "font-family: Nanum Gothic\nfont-weight: normal\nfont-style: normal\n")
    add_face(fonts_dir, "Nanum Gothic Bold", "font-family: Nanum Gothic\nfont-weight: bold\nfont-style: normal\n")
    add_face(fonts_dir, "Body", "font-family: Body\nfont-weight: 400\nfont-style: italic\nunicode-range: latin\n")
    return fonts_dir


def test_parse_unicode_range():
    assert parse_unicode_range("U+0041") == [0x41]
    assert parse_unicode_range("U+0041-0043, u+0061") == [0x41, 0x42, 0x43, 0x61]
    assert parse_unicode_range("U+004?") == list(range(0x40, 0x50))


def test_multiple_faces_per_family(fonts_dir):
    fonts = AvailableFonts(str(fonts_dir))
    assert [f.slug for f in fonts.find_fonts("nanum gothic")] == ["nanum-gothic", "nanum-gothic-bold"]
    assert [f.slug for f in fonts.find_fonts("Body")] == ["body-italic"]
    assert fonts.find_font("Nanum Gothic").slug == "nanum-gothic"


def test_same_face_twice_is_an_error(fonts_dir):
    add_face(fonts_dir, "Nanum Gothic Again", "font-family: Nanum Gothic\n")
    with pytest.raises(Exception, match="same face"):
        AvailableFonts(str(fonts_dir))


def test_more_than_one_font_file_is_an_error(fonts_dir):
    make_font(fonts_dir / "Body" / "another.ttf")
    with pytest.raises(Exception, match="More than one font file"):
        AvailableFonts(str(fonts_dir))


def test_finds_fonts_in_css(fonts_dir):
    processor = CssProcessor(AvailableFonts(str(fonts_dir)), "fonts")
    css = 'h1 { font-family: "Nanum Gothic", sans-serif; }\np { font: italic 1.2em/1.5 Body, serif; } x { font-size: 2em; }'
    assert [f.slug for f in processor.find_required_fonts(css)] == ["body-italic", "nanum-gothic", "nanum-gothic-bold"]
    assert processor.find_required_fonts(":root {\n  --heading-font: 'Nanum Gothic';\n}") != []
    assert processor.find_required_fonts("p { font-family: Helvetica; }") == []


def test_css_and_fonts_are_generated(fonts_dir, tmp_path):
    static = tmp_path / "static"
    static.mkdir()
    (static / "site.css").write_text('h1 {\n  font-family: "Nanum Gothic", sans-serif;\n}\n')
    (static / "plain.css").write_text('p {\n  color: red;\n}\n')
    out = tmp_path / "web"

    processor = CssProcessor(AvailableFonts(str(fonts_dir)), str(out / "fonts"))
    sync_files(str(static), str(out), processor=processor.process)
    processor.sync_fonts(str(out))

    css = (out / "site.css").read_text()
    assert css.startswith("/* web fonts */\n@font-face {\n  font-family: 'Nanum Gothic';\n  src: url('fonts/nanum-gothic.woff2') format('woff2');\n")
    assert "  font-weight: bold;\n" in css
    assert css.count("font-display: swap;") == 2
    assert "woff'" not in css
    assert css.endswith('/* end of web fonts */\n\nh1 {\n  font-family: "Nanum Gothic", sans-serif;\n}\n')
    assert (out / "plain.css").read_text() == 'p {\n  color: red;\n}\n'
    assert sorted(os.listdir(out / "fonts")) == ["nanum-gothic-bold.woff2", "nanum-gothic.woff2"]


def test_woff_is_optional(fonts_dir, tmp_path):
    static = tmp_path / "static"
    static.mkdir()
    (static / "site.css").write_text('h1 {\n  font-family: "Nanum Gothic";\n}\n')
    out = tmp_path / "web"

    processor = CssProcessor(AvailableFonts(str(fonts_dir)), str(out / "fonts"), woff=True)
    sync_files(str(static), str(out), processor=processor.process)
    processor.sync_fonts(str(out))

    assert "url('fonts/nanum-gothic.woff') format('woff')" in (out / "site.css").read_text()
    assert "nanum-gothic.woff" in os.listdir(out / "fonts")


def test_fonts_are_subset_to_unicode_range(fonts_dir, tmp_path):
    out = tmp_path / "web"
    fonts = AvailableFonts(str(fonts_dir))
    body, = fonts.find_fonts("Body")
    nanum, _ = fonts.find_fonts("Nanum Gothic")
    fonts.sync_font(body, str(out))
    fonts.sync_font(nanum, str(out))

    assert set(TTFont(out / "body-italic.woff2").getBestCmap()) == {ord("A"), ord("B")}
    assert set(TTFont(out / "nanum-gothic.woff2").getBestCmap()) == {ord("A"), ord("B"), ord("가")}

    processor = CssProcessor(fonts, "fonts")
    assert "  unicode-range: U+0000-00FF, U+0131" in "\n".join(processor.process_css_lines(["p { font-family: Body; }"], "site.css"))


def test_unchanged_css_is_still_processed_for_fonts(fonts_dir, tmp_path):
    static = tmp_path / "static"
    static.mkdir()
    (static / "site.css").write_text('h1 {\n  font-family: "Nanum Gothic";\n}\n')
    out = tmp_path / "web"
    sync_files(str(static), str(out), processor=CssProcessor(AvailableFonts(str(fonts_dir)), str(out / "fonts")).process)
    mtime = os.path.getmtime(out / "site.css")

    # A second build, where the CSS is up to date, still finds the fonts it requires (but doesn't rewrite it)
    processor = CssProcessor(AvailableFonts(str(fonts_dir)), str(out / "fonts"))
    sync_files(str(static), str(out), processor=processor.process)
    assert [f.slug for f in processor.all_required_fonts] != []
    assert os.path.getmtime(out / "site.css") == mtime
