import os
from dataclasses import dataclass


@dataclass
class ContentEngine:
    sources_root: str = "."
    static_source_subdir: str = "_static"
    content_source_subdir: str = "_content"
    templates_source_subdir: str = "_templates"
    posts_source_subdir: str = "_posts"
    fonts_source_subdir: str = "_fonts"

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

    def content_path(self, filename: str) -> str:
        return os.path.join(self.content_source_path, filename)