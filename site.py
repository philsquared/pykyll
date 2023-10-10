import os
from dataclasses import dataclass


@dataclass
class Site:
    name: str  # Name of the site
    subtitle: str
    default_page_summary: str  # Default page summary
    public_url: str  # URL the site will be published to on the public internet
    image: str  # Default image associated with each page (can be overridden)
    keywords: str
    author: str
    output_dir = "web"  # Where the site files should be generated to
    static_target_subdir = "static"
    posts_subdir = "posts"  # Sub-directory where blog/ news/ journal posts should be generated to
    favicon_svg: str | None = None
    favicon_png: str | None = None
    is_local_build = os.environ.get("is_local_build") == "1"

    @property
    def static_target_path(self): return os.path.join(self.output_dir, self.static_target_subdir)

    @property
    def posts_target_path(self): return os.path.join(self.output_dir, self.posts_subdir)

    @property
    def posts_base_url(self): return os.path.join(self.public_url, self.posts_subdir)
