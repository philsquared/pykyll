from pykyll.utils import exhaustive_replace, truncate_text_by_sentence
from bs4 import BeautifulSoup
import html_text

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
    "(": "",
    ")": "",
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
