# pykyll
A static site generator, with similarities to Jekyll, in Python.

This is currently intended to be used by including this repo as a submodule - but there's no reason that other methdos shouldn't work.

Sites are generated from templates, posts (blog posts or articles), and (fixed) content.

### Templating

Templates use a simple templating language with the following features:

All directives are enclosed in double braces (`{{ ... }}`).

`{{$<name>}}`
expands the value of the variable named by `<name>`

`{{#include <name>#}}`
includes the file `<name>.template.html` in the `_templates` folder. Works like a C pre-processor #include.

```
{{%for <local name> in <list name>:
	<pattern to repeat>
%}}```
Loops over the `<list name>` variable (which must be a list/ array) and binds each element to the `<local name>`, which can be expanded in the inner block.

If the elements being iterated in a `for` expression are tuples you can bind multiple variables as a comma separated list.