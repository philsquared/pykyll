import os
import pathlib
import datetime
import shutil

from pykyll.utils import common_prefix


def ensure_dirs(dir_name: str):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def ensure_parent_dirs(dir_name: str):
    ensure_dirs(os.path.dirname(dir_name))


def get_file_modified_time(filename: str):
    path = pathlib.Path(filename)
    if path.exists():
        return datetime.datetime.fromtimestamp(path.stat().st_mtime)


def needs_sync(source_file: str, target_file: str) -> bool:
    """
    Checks if target exists and is not older than source
    - otherwise needs syncing
    """
    return not os.path.exists(target_file) or os.path.getmtime(source_file) > os.path.getmtime(target_file)


def sync_file(source_path: str, target_dir: str, always_copy=False, processor=None, ignore_absence=False) -> bool:
    if ignore_absence and not os.path.exists(source_path):
        return False

    source_file = os.path.basename(source_path)
    target_path = os.path.join(target_dir, source_file)
    if not always_copy and not needs_sync(source_path, target_path):
        return False

    ensure_dirs(target_dir)

    if not processor or not processor(source_path, target_path):
        shutil.copy2(source_path, target_path)
    return True


def sync_files(source_dir: str, target_dir: str, always_copy=False, processor=None) -> int:
    synced = 0
    for file in os.listdir(source_dir):
        source_path = os.path.join(source_dir, file)
        if os.path.isdir(source_path):
            synced = synced + sync_files(os.path.join(source_dir, file),
                                         os.path.join(target_dir, file),
                                         always_copy, processor)
        else:
            if sync_file(source_path, target_dir, always_copy=always_copy, processor=processor):
                synced = synced + 1
    return synced


def resolve_relative_path(relative_path: str) -> str:
    return os.path.normpath(os.path.join(os.getcwd(), relative_path))


def print_relative_file(relative_path: str, filename: str, prefix="\n"):
    print(f"{prefix}file://{resolve_relative_path(relative_path)}/{filename}")


def print_link(relative_path: str):
    print_relative_file(relative_path, "index.html")


def path_diff(source_path: str, target_path: str) -> str:
    """
    Finds the relative path between the supplied paths.
    Paths are normalised first
    """
    source_path = os.path.normpath(source_path)
    target_path = os.path.normpath(target_path)

    prefix = common_prefix(source_path, target_path)
    relative_source = source_path[len(prefix):].strip("/")
    relative_target = target_path[len(prefix):].strip("/")
    if relative_source == "":
        parents = 0
    else:
        parents = relative_source.count("/") + 1

    return ("../" * parents) + relative_target
