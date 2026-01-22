import markdown
import bleach

from pykyll.allowed_tags import allowed_tags_with_links, allowed_tags
from pykyll.html import strip_p_tag


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
    if embedded_code:
        extensions.append('fenced_code')
    html = markdown.markdown(text, extensions=extensions, output_format='html')
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
