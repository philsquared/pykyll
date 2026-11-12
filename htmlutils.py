from pykyll.utils import exhaustive_replace, truncate_text_by_sentence
import re
import html_text
import nh3
from linkify_it import LinkifyIt

img_parser = re.compile(r'.*?<img (.*?)\s*class\s*=\s*\"(.*?)\"(.*?)>.*', re.DOTALL)
img_src_parser = re.compile(r'.*?src\s*=\s*\"(.*?)\".*', re.DOTALL)

# Comments, and tags (allowing for quoted attribute values containing >)
tag_parser = re.compile(r'(<!--.*?-->|<[^>"\']*(?:(?:"[^"]*"|\'[^\']*\')[^>"\']*)*>)', re.DOTALL)
a_tag_parser = re.compile(r'<(/?)a[\s>]', re.IGNORECASE)

# Bare email addresses aren't linked (as with bleach, which this replaces)
linkifier = LinkifyIt(options={"fuzzy_email": False})

# Same as bleach's defaults
clean_attributes = {"a": {"href", "title"}, "abbr": {"title"}, "acronym": {"title"}}
clean_url_schemes = {"http", "https", "mailto"}


def clean_html(html: str, tags: [str]) -> str:
    """
    Sanitises html, keeping only the given tags (others are removed, but their text content is kept)
    """
    return nh3.clean(html, tags=set(tags), attributes=clean_attributes, url_schemes=clean_url_schemes, link_rel=None)


def linkify_text(text: str) -> str:
    """
    Turns any URLs in a run of text (which may contain entities, but no tags) into links
    """
    matches = linkifier.match(text)
    if not matches:
        return text
    parts = []
    last = 0
    for match in matches:
        url = match.url.replace('"', "&quot;")
        parts.append(text[last:match.index])
        parts.append(f'<a href="{url}">{text[match.index:match.last_index]}</a>')
        last = match.last_index
    parts.append(text[last:])
    return "".join(parts)


def linkify(html: str) -> str:
    """
    Turns any URLs in the text of html into links (but not within existing links)
    """
    parts = tag_parser.split(html)
    link_depth = 0
    # split() alternates text and tags, starting (and ending) with text
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if link_depth == 0 and part:
                parts[i] = linkify_text(part)
        elif m := a_tag_parser.match(part):
            link_depth = max(0, link_depth - 1) if m.group(1) else link_depth + 1
    return "".join(parts)


def strip_tag(html: str, tag_name: str) -> str:
    """
    Removes html tag from start and end of string (closing tag at the end), if present
    """
    return html.strip().removeprefix(f"<{tag_name}>").removesuffix(f"</{tag_name}>")


def strip_p_tag(html: str) -> str:
    """
    Removes p tag from start and end of string (closing tag at the end), if present
    """
    return strip_tag(html, "p")


url_replacements = {
    "\t": " ",
    "\n": " ",
    "\r": " ",
    "<em>": "",
    "</em>": "",
    "<code>": "",
    "</code>": "",
    " ": "-",
    "/": "-",
    "\\": "-",
    "&amp;": "and",
    "+": "p",
    ";": "-",
    ":": "",
    ",": "-",
    "...": "",
    "..": "",
    "'": "",
    '"': "",
    "`": "",
    "<": "",
    ">": "",
    "!": "",
    "*": "",
    "?": "",
    "&": "and",
    "%": "pc",
    "(": "",
    ")": "",
    "[": "",
    "]": "",
    "{": "",
    "}": "",
    "c#": "csharp",
    "f#": "fsharp",
    '#': ""}


def slugify(text: str) -> str:
    """
    Converts raw text into a string that is valid as part of a URL.
    Converts spaces to underscores, removes punctuation and handles some special characters
    such as + as 'p'
    """
    text = text.encode('ascii', 'ignore').decode("utf-8")
    text = text.strip().lower()
    text = exhaustive_replace(text, url_replacements)

    # Do these separately so multiple dots and dashes are collapsed first
    text = exhaustive_replace(text, {".": "-"})
    text = exhaustive_replace(text, {"--": "-"})
    return text.strip("-")


def make_description(html: str, attribute_safe=True, allow_sentence_to_be_cut=True, wrap_in_p_tags=False, max_length=300) -> str:
    # soup = BeautifulSoup(html, features="html.parser")
    # text = soup.get_text().strip("/n").strip()

    text = html_text.extract_text(html)

    if attribute_safe:
        # remove anything that shouldn't be in an attribute
        text = exhaustive_replace(text, {
            '"': "'",
            "\n": " ",
            "\t": " ",
            "  ": " ",
            "!": ".",
            "?": "."})
    truncated = truncate_text_by_sentence(text.strip(), max_length, allow_sentence_to_be_cut=allow_sentence_to_be_cut)
    if wrap_in_p_tags:
        lines = truncated.splitlines()
        return "\n".join(f"<p>{line}</p>" for line in lines)
    else:
        return truncated


def find_image_with_class(html: str, class_name: str) -> str | None:
    """
    Finds an image file within an img tag with a given class name
    """
    for img_match in img_parser.finditer(html):
        classes = img_match.group(2).split(" ")
        for cls in classes:
            if cls == class_name:
                img_attrs = img_match.group(1) + " " + img_match.group(3)
                if m := img_src_parser.match(img_attrs):
                    return m.group(1)
    return None
