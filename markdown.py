import markdown
import bleach

from pykyll.html import strip_p_tag

allowed_tags = ['abbr', 'acronym', 'b', 'blockquote', 'code',
                'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                'h1', 'h2', 'h3', 'p', 'hr', 'br']

allowed_tags_with_links = allowed_tags + ['a']


def clean_for_attribute(text: str) -> str:
    return bleach.clean(text, tags=allowed_tags).replace('"', "&quot;").replace("'", "&apos;")


def clean_for_block(text: str) -> str:
    html = bleach.clean(text, tags=allowed_tags_with_links)
    return bleach.linkify(html)


def render_markdown(
        text: str,
        linkify=False,
        clean=False,
        strip_outer_p_tag=False,
        embedded_code=True,
        remove_elements: [str] = []) -> str:
    if not text:
        return ""

    if embedded_code:
        html = markdown.markdown(text, extensions=['fenced_code'], output_format='html')
    else:
        html = markdown.markdown(text, output_format='html')
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
