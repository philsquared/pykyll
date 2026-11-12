import os

from pykyll.contentengine import ContentEngine
from pykyll.templater import Templater


def test_templates_needn_t_be_under_working_directory(tmp_path, monkeypatch):
    templates = tmp_path / "templates"
    (templates / "sub").mkdir(parents=True)
    (templates / "base.html").write_text("<b>{% block content %}{% endblock %}</b>")
    (templates / "sub" / "page.html").write_text("{% extends '../base.html' %}{% block content %}{{ text }}{% endblock %}")

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    assert Templater.render_from_template(str(templates), "sub/page.html", text="hi") == "<b>hi</b>"


def test_instance_root_is_resolved_when_created(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert ContentEngine().instance_root == os.path.realpath(tmp_path)
    assert ContentEngine(sources_root="site").instance_root == os.path.realpath(tmp_path / "site")
    assert ContentEngine(instance_root="/somewhere").instance_root == "/somewhere"
