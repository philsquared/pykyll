# Pykyll
A static site generator, with similarities to Jekyll, written in Python. Pronounced like "Pickle".

This is currently intended to be used by including this repo as a submodule - but there's no reason that other methods shouldn't work.
The repo is also an installable package, so a project using uv can install the submodule as an editable dependency (rather than putting its parent directory on the import path):

```toml
[project]
dependencies = ["pykyll"]

[tool.uv.sources]
pykyll = { path = "pykyll", editable = true }
```

Some features need optional extras: `scss` (compiling `.scss` files) and `fonts` (converting fonts to web fonts), e.g. `dependencies = ["pykyll[scss,fonts]"]`.
To work on pykyll itself with these installed, use `uv sync --all-extras`.

Dependencies are managed with [uv](https://docs.astral.sh/uv/) - see `pyproject.toml`. To run the unit tests:

```sh
uv run pytest
```

Sites are generated from templates, posts (blog posts or articles), and (fixed) content.

### Templating

Jinga2 is used for templating.

### Fonts

`CssProcessor` (used as the processor when syncing static files) adds `@font-face` rules to CSS for any fonts it uses that are in the fonts directory (`_fonts`, by default), and `sync_fonts()` then generates `.woff2` web fonts for them (needs the `fonts` extra).
Pass `woff=True` to also generate `.woff` files (only needed for very old browsers).

Each face of a font (each weight and style) is a subdirectory with one `.otf` or `.ttf` file, an optional `.txt` file (e.g. the licence, which is copied alongside), and an optional `.yml` file:

```yaml
font-family: Nanum Gothic # Defaults to the directory name
font-weight: bold         # Defaults to normal
font-style: normal        # Defaults to normal
font-display: swap        # Defaults to swap
unicode-range: latin      # Optional. Subsets the font to these characters: a CSS unicode-range, latin or latin-ext (or a list of these)
```
