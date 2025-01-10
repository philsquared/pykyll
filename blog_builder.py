import codecs
import copy
import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property

import dateutil.parser
import typing

from pykyll.html import slugify, make_description, find_image_with_class
from pykyll.markdown import render_markdown
from pykyll.utils import format_datetime_for_blog, format_datetime_for_rss, format_longdate

open_script_parser = re.compile(r'.*?<script.*?>(.*)', re.DOTALL)
close_script_parser = re.compile(r'(.*)</script>.*', re.DOTALL)
html_title_parser = re.compile(r'.*?<h1>(.*?)</h1>.*', re.DOTALL)
md_title_parser = re.compile(r'.*?#(.*)', re.DOTALL)

use_html_extension: bool = True


def set_use_html_extension(use: bool):
    global  use_html_extension
    use_html_extension = use


@dataclass
class PostMetadata:
    filename: str
    title: str
    slug: str
    page_image: str | None
    timestamp: datetime
    guid: str
    hash: str
    tags: str
    hide_title: bool
    version: int
    redirect_url: str  # If page used to be at a different url, what was it
    is_draft: bool
    content_line_no: int  # !What line the content starts from (after the title)
    base_url: str
    is_dirty: bool  # Just created, or updated?

    @property
    def formatted_timestamp(self): return format_datetime_for_blog(self.timestamp)

    @property
    def formatted_date(self): return format_longdate(self.timestamp)

    @property
    def rss_formatted_timestamp(self): return format_datetime_for_rss(self.timestamp)

    @property
    def page_name(self):
        if use_html_extension:
            return f"{self.slug}.html"
        else:
            return self.slug

    @property
    def public_url(self): return f"{self.base_url}/{self.page_name}"

    def to_properties(self):
        properties = {
            "slug": self.slug,
            "guid": self.guid,
            "hash": self.hash,
            "version": self.version
        }
        if self.hide_title:
            properties["hide-title"] = True
        if self.redirect_url:
            if self.redirect_url:
                properties["redirect"] = self.redirect_url
            if self.page_image:
                properties["page-image"] = self.page_image
            if self.tags:
                properties["tags"] = ", ".join(self.tags)

        return properties
def read_metadata_strings(path: str) -> (str, str, int):
    script_text = None
    reading_script = False
    with codecs.open(path, "r", "utf-8") as file:
        for line_no, line in enumerate(file.readlines()):
            if not reading_script:
                m = html_title_parser.match(line)
                if not m:
                    m = md_title_parser.match(line)
                if m:
                    title = m.group(1).strip()
                    return script_text, title, line_no+1
            else:
                m = close_script_parser.match(line)
                if not m:
                    script_text = script_text + line
                else:
                    script_text = script_text + m.group(1)
                    reading_script = False

            if script_text is None:
                m = open_script_parser.match(line)
                if m:
                    script_text = m.group(1)
                    reading_script = True

    raise Exception(f"{path} has no title")


def read_metadata(path: str, base_url: str) -> PostMetadata:
    properties_str, title, content_line_no = read_metadata_strings(path)
    is_dirty = False
    if properties_str:
        properties = json.loads(properties_str)
    else:
        properties = {}

    def try_get_property(name: str, compute_default):
        value = properties.get(name)
        if value is None:
            nonlocal is_dirty
            is_dirty = True
            value = compute_default()
        return value

    slug = try_get_property("slug", lambda: slugify(title))
    guid = try_get_property("guid", lambda: str(uuid.uuid4()))
    hash = try_get_property("hash", lambda: None)
    hide_title = try_get_property("hide-title", lambda: False)
    version = try_get_property("version", lambda: 0)

    page_image = properties.get("page-image")
    redirect_url = properties.get("redirect")
    tags = properties.get("tags")
    if tags:
        tags = [tag.strip() for tag in tags.split(",")]

    basename = os.path.basename(path)
    is_draft = "draft" in basename

    if is_draft:
        timestamp = datetime.now()
    else:
        try:
            timestamp_str = basename[:13] + ":" + basename[14:-3]
            timestamp = dateutil.parser.parse(timestamp_str)
        except:
            timestamp = None

    metadata = PostMetadata(
        filename=path,
        title=title,
        slug=slug,
        page_image=page_image,
        timestamp=timestamp,
        guid=guid,
        hash=hash,
        tags=tags,
        hide_title=hide_title,
        version=version,
        redirect_url=redirect_url,
        is_draft=is_draft,
        content_line_no=content_line_no,
        base_url=base_url,
        is_dirty=is_dirty
    )
    return metadata


class Post:
    def __init__(self, metadata: PostMetadata, md_content: str, summary_length = 500):
        self.md_content = md_content
        self.html_content = render_markdown(md_content)
        self.summary_length = summary_length
        hash = hashlib.sha256(self.html_content.encode()).hexdigest()
        if hash == metadata.hash:
            self.metadata = metadata
        else:
            self.metadata = copy.deepcopy(metadata)
            self.metadata.hash = hash
            self.metadata.is_dirty = True

    @cached_property
    def summary(self):
        return make_description(
            self.html_content,
            attribute_safe=False,
            wrap_in_p_tags=True,
            max_length=self.summary_length)

    @cached_property
    def description(self):
        return make_description(self.html_content, max_length=300)

    @cached_property
    def page_image(self):
        return find_image_with_class(self.html_content, "post-image")

    def write(self, out_file: typing.TextIO):
        out_file.write('<script type="application/json">\n')
        json.dump(self.metadata.to_properties(), out_file, sort_keys=True, indent=4)
        out_file.write("\n</script>\n\n")
        out_file.write(f"# {self.metadata.title}\n\n")
        out_file.write(self.md_content.strip("\n"))


def load_post_from_metadata(metadata: PostMetadata, summary_length=400) -> Post:
    with codecs.open(metadata.filename, "r", "utf-8") as file:
        content = "".join(file.readlines()[metadata.content_line_no:])
    return Post(metadata, content, summary_length)


def load_post_metadata(posts_dir: str, base_url: str) -> [PostMetadata]:
    filenames = [f for f in os.listdir(posts_dir) if os.path.isfile(os.path.join(posts_dir, f)) and f.endswith(".md")]
    filenames.sort(reverse=True)
    paths = [os.path.join(posts_dir, filename) for filename in filenames]
    return [read_metadata(path, base_url) for path in paths]


def load_post(posts_dir: str, base_url: str) -> [Post]:
    metadata = read_metadata(posts_dir, base_url)
    return load_post_from_metadata(metadata)


def save_post(post: Post):
    basename, ext = os.path.splitext(post.metadata.filename)
    temp_filename = f"{basename}.new{ext}"
    with codecs.open(temp_filename, "w", "utf-8") as out_file:
        post.write(out_file)
    os.remove(post.metadata.filename)
    os.rename(temp_filename, post.metadata.filename)
