import os
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ContentEngine:
    sources_root: str = "."
    # Defaults to the absolute path of sources_root (resolved when created, not when this module is imported)
    instance_root: str | None = field(default=None)
    static_source_subdir: str = "_static"
    content_source_subdir: str = "_content"
    templates_source_subdir: str = "_templates"
    email_templates_source_subdir: str = "_email_templates"
    posts_source_subdir: str = "_posts"
    fonts_source_subdir: str = "_fonts"

    def __post_init__(self):
        if self.instance_root is None:
            self.instance_root = os.path.realpath(self.sources_root)

    @property
    def static_source_path(self): return os.path.join(self.sources_root, self.static_source_subdir)

    @property
    def content_source_path(self): return os.path.join(self.sources_root, self.content_source_subdir)

    @property
    def posts_source_path(self): return os.path.join(self.sources_root, self.posts_source_subdir)

    @property
    def fonts_source_path(self): return os.path.join(self.sources_root, self.fonts_source_subdir)

    @property
    def templates_root(self): return os.path.join(self.sources_root, self.templates_source_subdir)

    @property
    def email_templates_root(self): return os.path.join(self.sources_root, self.email_templates_source_subdir)

    def content_path(self, filename: str) -> str:
        return os.path.join(self.content_source_path, filename)


def promote_draft(filename: str, ce: ContentEngine):
    now = datetime.now()
    dated_filename = "{:0>4}-{:0>2}-{:0>2}T{:0>2}-{:0>2}.md".format(now.year, now.month, now.day, now.hour, now.minute)
    src = filename
    dst = os.path.join(ce.posts_source_path, dated_filename)
    print(f"Promoting `{src}` to `{dst}`")

    if not os.path.exists(src):
        raise Exception(f"{src} does not exist")

    os.rename(src, dst)