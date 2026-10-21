import markdown
import bleach
from pygments.formatters import HtmlFormatter

from pykyll.allowed_tags import allowed_tags_with_links, allowed_tags
from pykyll.html import strip_p_tag


class CodeHtmlFormatter(HtmlFormatter):
    """
    Pygments formatter that keeps the language class (e.g. "language-c++") on the <code> element,
    so blocks can still be styled per language
    """
    def __init__(self, lang_str="", **options):
        super().__init__(**options)
        self.lang_str = lang_str

    def _wrap_code(self, source):
        yield 0, f'<code class="{self.lang_str}">' if self.lang_str else '<code>'
        yield from source
        yield 0, '</code>'


def render_markdown(
        text: str,
        linkify=False,
        clean=False,
        strip_outer_p_tag=False,
        embedded_code=True,
        remove_elements: [str] = []) -> str:
    if not text:
        return ""

    extensions = ['extra']
    extension_configs = {}
    if embedded_code:
        extensions.append('fenced_code')
        # Syntax highlighting markup would just be stripped by cleaning, so only highlight uncleaned output
        if not clean:
            extensions.append('codehilite')
            extension_configs['codehilite'] = {
                'guess_lang': False,
                'pygments_formatter': CodeHtmlFormatter,
            }
    html = markdown.markdown(text, extensions=extensions, extension_configs=extension_configs, output_format='html')
    if strip_outer_p_tag:
        html = strip_p_tag(html)
    if clean:
        if linkify:
            tags = allowed_tags_with_links
        else:
            tags = allowed_tags

        if remove_elements:
            tags = tags.copy()
            for e in remove_elements:
                tags.remove(e)

        html = bleach.clean(html, tags=tags)
    if linkify:
        return bleach.linkify(html)
    else:
        return html


def read_markdown(markdown_path: str) -> str:
    with open(markdown_path, 'r') as f:
        md = f.read()
    return markdown.markdown(md)
