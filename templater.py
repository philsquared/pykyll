import os

from bleach import linkify
from jinja2 import FileSystemLoader, Environment

from .markdown import render_markdown, clean_for_attribute, clean_for_block
from .site import Site
from .fileutils import ensure_parent_dirs


def markdown_filter(markdown: str) -> str:
    return render_markdown(markdown, linkify=True, clean=True, strip_outer_p_tag=True)


def add_filters(env: Environment):
    env.filters["markdown"] = markdown_filter
    env.filters["clean_for_attribute"] = clean_for_attribute
    env.filters["clean_for_block"] = clean_for_block


class RelEnvironment(Environment):
    """Override join_path() to enable relative template paths, collapsing .. dirs."""
    def join_path(self, template, parent):
        return os.path.normpath(os.path.join(os.path.dirname(parent), template))


def get_string_based_environment() -> Environment:
    env = Environment(trim_blocks=True,
                      lstrip_blocks=True)
    add_filters(env)
    return env


def get_file_based_environment() -> Environment:
    loader = FileSystemLoader(".")
    env = RelEnvironment(loader=loader,
                         trim_blocks=True,
                         lstrip_blocks=True)
    add_filters(env)
    return env


class Templater:
    def __init__(
            self, site: Site,
            templates_root: str,
            email_templates_root: str | None = None):
        self.site = site
        self.templates_root = templates_root
        self.email_templates_root = email_templates_root

    @staticmethod
    def render_from_template(
            directory: str,
            template_name: str,
            **kwargs):
        """
        Renders the named template and returns the rendered string
        """
        env = get_file_based_environment()
        template_path = os.path.normpath(os.path.join(directory, template_name))
        wd = os.getcwd()
        if template_path.startswith(wd):
            template_path = template_path[len(wd)+1:]
        template = env.get_template(template_path)
        return template.render(**kwargs)

    @staticmethod
    def render_from_string_raw(template_as_string: str, **kwargs) -> str:
        """
        Renders a template provided as a string and returns the rendered string
        """
        template = get_string_based_environment().from_string(template_as_string)
        return template.render(**kwargs)

    def render_from_string(self, template_as_string: str, levels: int = 0, rootdir=None, **kwargs) -> str:
        """
        Renders a template provided as a string and returns the rendered string.
        Also passed in to the template are rootdir, static_root (off rootdir), canonical_url and site, as well as
        any additional kwargs, passed.
        """
        if rootdir is None:
            rootdir = "../" * levels
        static_root = os.path.join(rootdir, self.site.static_target_subdir)
        template = get_string_based_environment().from_string(template_as_string)
        return template.render(
            rootdir=rootdir,
            static_root=static_root,
            site=self.site,
            **kwargs)

    def render_to_string(
            self,
            template_name: str,
            levels: int = 0,
            canonical_url: str | None = None,
            page_summary: str | None = None,
            rootdir=None,
            **kwargs) -> str:
        """
        Renders the named template to a string, enriching with additional args.
        The page_summary is used as the description of the page for unfurling links. If missing it uses the default
        for the site.
        Also passed in to the template are rootdir, static_root (off rootdir), canonical_url and site, as well as
        any additional kwargs, passed.
        """
        if rootdir is None:
            rootdir = "../" * levels
        static_root = os.path.join(rootdir, self.site.static_target_subdir)
        if canonical_url and canonical_url.endswith("/index.html"):
            canonical_url = canonical_url[:-11]
        if page_summary is None:
            page_summary = self.site.default_page_summary

        if "menu" not in kwargs:
            kwargs["menu"] = self.site.menu

        return Templater.render_from_template(
            self.templates_root,
            template_name,
            rootdir=rootdir,
            static_root=static_root,
            canonical_url=canonical_url,
            site=self.site,
            page_summary=page_summary,
            **kwargs)

    def render_to_file(
            self,
            template_name: str,
            filename: str,
            page_summary: str | None = None,
            **kwargs):
        """
        Renders the named template to the named file, enriching with additional args
        The page_summary is used as the description of the page for unfurling links. If missing it uses the default
        for the site.
        Also passed in to the template are rootdir, static_root (off rootdir), canonical_url and site, as well as
        any additional kwargs, passed.
        """
        dirname = os.path.dirname(filename)
        if dirname == "":
            levels = 0
        else:
            levels = len(dirname.split("/"))
        canonical_url = os.path.join(self.site.public_url, filename)
        rendered = self.render_to_string(template_name, levels, canonical_url, page_summary, **kwargs)
        path = os.path.join(self.site.output_dir, filename)
        ensure_parent_dirs(path)
        with open(path, 'w') as out_file:
            out_file.write(rendered)

    def render_email(self, template_name, **kwargs):
        if not self.email_templates_root:
            raise Exception("Templater renderer not configured for email")
        return Templater.render_from_template(
            self.email_templates_root,
            template_name,
            site=self.site,
            **kwargs)
