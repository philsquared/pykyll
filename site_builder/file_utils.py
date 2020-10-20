import os

def ensure_dirs( dir ):
    if dir and dir != '' and not os.path.exists(dir):
        os.makedirs(dir)

def ensure_parent_dirs( dir ):
    ensure_dirs(os.path.dirname(dir))
