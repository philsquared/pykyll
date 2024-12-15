import os
from datetime import datetime
from pykyll.blog_builder import Post
from pykyll.templater import Templater
from pykyll.utils import format_datetime_for_rss


def build_rss(templater: Templater,
              all_posts: [Post],
              rss_filename: str,
              template_name=os.path.join(os.path.dirname(__file__), "_templates/rss.template.html")):
    last_build_date = format_datetime_for_rss(datetime.now())
    rootdir = templater.site.public_url + "/"
    post_data = [(post.metadata, templater.render_from_string(post.html_content, rootdir=rootdir, metadata=post.metadata))
                 for post in all_posts]

    templater.render_to_file(
        template_name,
        rss_filename,
        post_data=post_data,
        last_build_date=last_build_date,
        rootdir="/")
