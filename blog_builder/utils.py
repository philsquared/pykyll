import markdown
import bleach

allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p', 'hr']

def render_markdown( text ):
    if text is None:
        return text
    else:
        return bleach.linkify(
                bleach.clean(
                    markdown.markdown( text, extensions=['fenced_code'], output_format='html' ),
                    tags=allowed_tags
                )
            )