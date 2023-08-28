import markdown
import bleach

from pykyll.html import strip_p_tag

allowed_tags = ['abbr', 'acronym', 'b', 'blockquote', 'code',
                'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                'h1', 'h2', 'h3', 'p', 'hr', 'br']

allowed_tags_with_links = allowed_tags + ['a']


def render_markdown(text: str, linkify=False, clean=False, strip_outer_p_tag=False) -> str:
    if not text:
        return ""

    if linkify:
        tags = allowed_tags_with_links
    else:
        tags = allowed_tags
    html = markdown.markdown(text, extensions=['fenced_code'], output_format='html')
    if strip_outer_p_tag:
        html = strip_p_tag(html)
    if clean:
        html = bleach.clean(html, tags=tags)
    if linkify:
        return bleach.linkify(html)
    else:
        return html


def read_markdown(markdown_path: str) -> str:
    with open(markdown_path, 'r') as f:
        md = f.read()
    return markdown.markdown(md)
