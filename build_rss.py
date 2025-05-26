import codecs
import os
from datetime import datetime

import yaml

from pykyll.blog_builder import Post
from pykyll.templater import Templater
from pykyll.utils import format_datetime_for_rss, reduce_text_to


def _get_social_media_template(link: str) -> str:
    return f"""%%%%

{link}
"""

def get_sm_content(post: Post, link: str, max_len: int) -> str:
    summary = post.metadata.twitter or post.description
    sm_template = _get_social_media_template(link)

    try:
        content_max_len = max_len - (len(sm_template) - 4)
        content = reduce_text_to(summary, content_max_len)
    except Exception as e:
        print(e)
        print(f"while processing episode: {post.metadata.filename}")
        os.abort()

    return sm_template.replace("%%%%", content)

def build_rss(templater: Templater,
              all_posts: [Post],
              rss_filename: str,
              template_name=os.path.join(os.path.dirname(__file__), "_templates/rss.template.xml")):
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


def build_posterchild(site_name: str,
                      public_url: str,
                      all_posts: [Post],
                      posterchild_filename: str):
    last_build_date = format_datetime_for_rss(datetime.now())

    items = []
    for post in all_posts:
        link, _ = os.path.splitext(post.metadata.public_url)

        tweet = get_sm_content(post, link, 280)
        toot = get_sm_content(post, link, 512)

        item = {
            "title": post.metadata.title,
            "description": post.description,
            "link": link,
            "guid": post.metadata.guid,
            "last_updated": post.metadata.rss_formatted_timestamp,
            "twitter": tweet,
            "mastodon": toot
        }
        items.append(item)

    data = {
        "channel_name": site_name,
        "link": public_url,
        "last_build_date": last_build_date,
        "items": items
    }
    with codecs.open(posterchild_filename, "w", "utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

