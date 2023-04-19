from pathlib import Path
from typing import Callable, Iterable, TypeVar

FilePath = TypeVar('FilePath', bound=Path)
FolderPath = TypeVar('FolderPath', bound=Path)


def iter_through_files(folder: FilePath,
                       folder_filter: Callable[[FolderPath], bool],
                       file_filter: Callable[[FilePath], bool]) -> Iterable[FilePath]:
    """ Return all files with provided filters """
    for path in folder.iterdir():
        if path.is_dir() and folder_filter(path):
            yield from iter_through_files(path, folder_filter, file_filter)
        elif path.is_file() and file_filter(path):
            yield path
