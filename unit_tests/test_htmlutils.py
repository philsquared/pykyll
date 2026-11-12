from pykyll.htmlutils import strip_tag, strip_p_tag, slugify, make_description, find_image_with_class, clean_html, linkify
from pykyll.allowed_tags import allowed_tags, allowed_tags_with_links


def test_strip_tags():
    assert strip_tag("<div>hello</div>", "div") == "hello"

    assert strip_tag("<div>hello</div>", "p") == "<div>hello</div>"

    assert strip_p_tag("<p>hello</p>") == "hello"
    assert strip_p_tag("<p><p>hello</p></p>") == "<p>hello</p>"
    assert strip_p_tag("<p></p>hello<p></p>") == "</p>hello<p>"

    # Doesn't strip non closing tag from end
    assert strip_tag("<div>hello<div>", "div") == "hello<div>"


def test_slugify():
    assert slugify("once upon a time") == "once-upon-a-time"
    assert slugify("'punctuation', *asterisks* and </tags>?") == "punctuation-asterisks-and-tags"
    assert slugify("  whitespace    \t\n\rremoved   ") == "whitespace-removed"
    assert slugify("C++ on Sea") == "cpp-on-sea"
    assert slugify("C# code") == "csharp-code"
    assert slugify("F# is functional") == "fsharp-is-functional"
    assert slugify("trailing...dots") == "trailingdots"
    assert slugify("make a dash--for it") == "make-a-dash-for-it"
    assert slugify("emojis are 👍") == "emojis-are"


def test_make_description():
    assert make_description("<div>Hello <p>there</p> <b>this is bold</b></div>") == "Hello there this is bold"

    html = """
        <html>
        <head>
            <script>var i = 7</script>
            <style>.css { position: absolute; }</style>
        </head>
        <body>
            <script>var j = 7</script>
            <style>.css { position: relative; }</style>
            Some text            
        </body>
        """
    assert make_description(html) == "Some text"

    assert make_description("<img src='somewhere'>some text") == "some text"

    assert make_description("<p>one.</p><p>two</p>") == "one. two"
    assert make_description("<p>one.</p><p>two</p>", attribute_safe=False) == "one.\ntwo"


def test_make_description_truncated():
    text = "This is a really long sentence. This is an even longer sentence."
    assert make_description(text) == text
    assert make_description(text, max_length=63) == text[:-1]
    assert make_description(text, max_length=62) == "This is a really long sentence"
    assert make_description(text, max_length=40) == "This is a really long sentence"
    assert make_description(text, max_length=10) == "This is a"


def test_image_parser():
    assert find_image_with_class('<img src="xyz.jpg">', "abc") == None
    assert find_image_with_class('<img class="abc" src="xyz.jpg">', "abc") == "xyz.jpg"
    assert find_image_with_class('<img src="xyz.jpg" class="abc">', "abc") == "xyz.jpg"
    assert find_image_with_class('<img  src="xyz.jpg"   class="abc" >', "abc") == "xyz.jpg"
    assert find_image_with_class('<img  src = "xyz.jpg" alt="hello"  class = "abc" >', "abc") == "xyz.jpg"

    assert find_image_with_class('<img src="xyz.jpg" class="abc">\n<img src="ijk.png" class="abc">', "abc") == "xyz.jpg"


def test_clean_html():
    # Allowed tags are kept, others removed (but not their text)
    assert clean_html("<p><b>bold</b> <span>plain</span></p>", allowed_tags) == "<p><b>bold</b> plain</p>"
    assert clean_html('<a href="https://example.com">link</a>', allowed_tags) == "link"
    assert clean_html('<a href="https://example.com" onclick="x()">link</a>', allowed_tags_with_links) == '<a href="https://example.com">link</a>'

    # Scripts are removed entirely, and unsafe links lose their href
    assert clean_html("<script>alert(1)</script>text", allowed_tags) == "text"
    assert clean_html('<a href="javascript:alert(1)">link</a>', allowed_tags_with_links) == "<a>link</a>"

    # Text is escaped
    assert clean_html("1 < 2 & 3", allowed_tags) == "1 &lt; 2 &amp; 3"


def test_linkify():
    assert linkify("see https://example.com/page.") == 'see <a href="https://example.com/page">https://example.com/page</a>.'
    assert linkify("<p>at example.com</p>") == '<p>at <a href="http://example.com">example.com</a></p>'

    # Entities in the URL are left as they are (so it's still valid in the href)
    assert linkify("https://example.com/?a=1&amp;b=2") == '<a href="https://example.com/?a=1&amp;b=2">https://example.com/?a=1&amp;b=2</a>'

    # Existing links, and urls in attributes, are left alone
    existing = '<a href="https://example.com">https://example.com</a> <abbr title="https://example.com">x</abbr>'
    assert linkify(existing) == existing

    # Bare email addresses aren't linked
    assert linkify("me@example.com") == "me@example.com"

    assert linkify("no links here") == "no links here"
