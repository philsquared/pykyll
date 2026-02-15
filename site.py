import os
from dataclasses import dataclass, field

@dataclass
class MenuItem:
    title: str
    link: str


class Menu:
    def __init__(self, left: list | None = None, right : list | None = None):
        self.left = []
        self.right = []
        if left:
            for item in left:
                if isinstance(item, MenuItem):
                    self.left.append(item)
                else:
                    self.left.append(MenuItem(item[0], item[1]))
        if right:
            for item in right:
                if isinstance(item, MenuItem):
                    self.right.append(item)
                else:
                    self.right.append(MenuItem(item[0], item[1]))


@dataclass
class Site:
    name: str  # Name of the site
    subtitle: str
    default_page_summary: str  # Default page summary
    public_url: str  # URL the site will be published to on the public internet
    image: str  # Default image associated with each page (can be overridden)
    keywords: str
    author: str
    rootdir: str = ""  #  root directory - will be local qualified dir for debug, or empty for prod
    output_dir: str = "web"  # Where the site files should be generated to
    static_target_subdir: str = "static"
    posts_subdir: str = "posts"  # Sub-directory where blog/ news/ journal posts should be generated to
    favicon_svg: str | None = None
    favicon_png: str | None = None
    is_local_build = os.environ.get("is_local_build") == "1" or os.environ.get("FLASK_ENV") == "development"
    menu: Menu = Menu()

    @property
    def static_target_path(self): return os.path.join(self.output_dir, self.static_target_subdir)

    @property
    def posts_target_path(self): return os.path.join(self.output_dir, self.posts_subdir)

    @property
    def posts_base_url(self): return os.path.join(self.public_url, self.posts_subdir)
