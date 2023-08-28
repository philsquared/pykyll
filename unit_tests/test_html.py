from pykyll.html import strip_tag, strip_p_tag, slugify, make_description


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
