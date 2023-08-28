import os
from dataclasses import dataclass


@dataclass
class ContentEngine:
    sources_root = ".."
    static_source_subdir = "_static"
    content_source_subdir = "_content"
    templates_source_subdir = "_templates"
    posts_source_subdir = "_posts"

    @property
    def static_source_path(self): return os.path.join(self.sources_root, self.static_source_subdir)

    @property
    def content_source_path(self): return os.path.join(self.sources_root, self.content_source_subdir)

    @property
    def posts_source_path(self): return os.path.join(self.sources_root, self.posts_source_subdir)

    @property
    def templates_root(self): return os.path.join(self.sources_root, self.templates_source_subdir)
