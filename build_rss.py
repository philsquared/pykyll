import codecs
import os
from datetime import datetime

import yaml

from pykyll.blog_builder import Post
from pykyll.templater import Templater
from pykyll.utils import format_datetime_for_rss, reduce_text_to


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
        summary = post.metadata.twitter or post.description

        link, _ = os.path.splitext(post.metadata.public_url)

        tweet_len = 280

        tweet_template = f"""%%%%

{link}
"""
        try:
            content = reduce_text_to(summary, tweet_len - (len(tweet_template) - 4))
        except Exception as e:
            print(e)
            print(f"while processing post: {post.metadata.filename}")
            os.abort()

        tweet = tweet_template.replace("%%%%", content)

        item = {
            "title": post.metadata.title,
            "description": post.description,
            "link": post.metadata.public_url,
            "guid": post.metadata.guid,
            "last_updated": post.metadata.rss_formatted_timestamp,
            "twitter": tweet
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

