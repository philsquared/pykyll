from pykyll.markdownutils import render_markdown


def test_fenced_code_is_highlighted():
    html = render_markdown("```c++\nint x = 42;\n```")
    assert '<div class="codehilite">' in html
    assert '<code class="language-c++">' in html
    assert '<span class="kt">int</span>' in html


def test_cleaned_markdown_is_not_highlighted():
    html = render_markdown("```c++\nint x = 42;\n```", clean=True)
    assert "codehilite" not in html
    assert "<span" not in html


def test_cleaned_and_linkified_markdown():
    html = render_markdown("Some **bold** <span>text</span>, see https://example.com", clean=True, linkify=True)
    assert html == '<p>Some <strong>bold</strong> text, see <a href="https://example.com">https://example.com</a></p>'
