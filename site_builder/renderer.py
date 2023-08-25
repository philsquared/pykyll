import os
from . import file_utils
from jinja2 import FileSystemLoader, Environment

templates_dir = "_templates"

def get_templates_env():
    loader = FileSystemLoader(templates_dir)
    return Environment(loader=loader)

def render_from_template( template_name, **kwargs ):
    template = get_templates_env().get_template(template_name)
    return template.render(**kwargs)


def render_to_file(template_name, filename, rootdir=None, **kwargs ):
    file_utils.ensure_parent_dirs( filename )
    dir = os.path.dirname( filename )
    levels = len(dir.split("/"))
    if not rootdir:
        rootdir = "../" * (levels-1)
    rendered = render_from_template( template_name, rootdir=rootdir, **kwargs)
    with open(filename, 'w') as out_file:
        out_file.write(rendered)

def render_to_string(template_as_string, **kwargs ):
    template = Environment().from_string( template_as_string )
    return template.render( **kwargs)
