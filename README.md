# Pykyll
A static site generator, with similarities to Jekyll, written in Python. Pronounced like "Pickle".

This is currently intended to be used by including this repo as a submodule - but there's no reason that other methods shouldn't work.

Dependencies are managed with [uv](https://docs.astral.sh/uv/) - see `pyproject.toml`. To run the unit tests:

```sh
uv run pytest
```

Sites are generated from templates, posts (blog posts or articles), and (fixed) content.

### Templating

Jinga2 is used for templating.
