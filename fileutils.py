import os
import pathlib
import datetime
import shutil


def ensure_dirs(dir_name: str):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def ensure_parent_dirs(dir_name: str):
    ensure_dirs(os.path.dirname(dir_name))


def get_file_modified_time(filename: str):
    path = pathlib.Path(filename)
    if path.exists():
        return datetime.datetime.fromtimestamp(path.stat().st_mtime)


def sync_file(source: str, target: str, always_copy=False) -> bool:
    if not always_copy and os.path.exists(target):
        source_mod_time = os.path.getmtime(source)
        target_mod_time = os.path.getmtime(target)
        if source_mod_time == target_mod_time:
            return False

    ensure_parent_dirs(target)
    shutil.copy2(source, target)
    return True


def sync_files(source: str, target: str, always_copy=False, processor=None) -> int:
    synced = 0
    for file in os.listdir(source):
        source_path = os.path.join(source, file)
        if os.path.isdir(source_path):
            synced = synced + sync_files(os.path.join(source, file),
                                         os.path.join(target, file),
                                         always_copy)
        else:
            target_path = os.path.join(target, file)
            if processor and processor(source_path, target_path):
                synced = synced + 1
            elif sync_file(source_path, target_path, always_copy):
                synced = synced + 1
    return synced


def resolve_relative_path(relative_path: str) -> str:
    return os.path.normpath(os.path.join(os.getcwd(), relative_path))


def print_link(relative_path: str):
    print(f"\nfile://{resolve_relative_path(relative_path)}/index.html")
