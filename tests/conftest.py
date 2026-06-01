from pathlib import Path

import pytest
from PIL import Image


class _MockPath:
    """Minimal Path-like object with controllable properties — no real I/O."""

    def __init__(self, name: str, suffix: str = None, parent: str = "/fake",
                 is_file: bool = True, is_dir: bool = False):
        self.name = name
        self.suffix = suffix if suffix is not None else Path(name).suffix
        self._is_file = is_file
        self._is_dir = is_dir
        self._str = f"{parent}/{name}"

    def is_file(self) -> bool:
        return self._is_file

    def is_dir(self) -> bool:
        return self._is_dir

    def __str__(self) -> str:
        return self._str

    def __fspath__(self) -> str:
        return self._str

    def __lt__(self, other) -> bool:
        return str(self) < str(other)

    def __repr__(self) -> str:
        return f"MockPath({self.name})"


def mock_path(
    name: str,
    suffix: str = None,
    parent: str = "/fake",
    is_file: bool = True,
    is_dir: bool = False,
) -> _MockPath:
    return _MockPath(name, suffix, parent, is_file, is_dir)


@pytest.fixture
def sample_image() -> Image.Image:
    return Image.new("RGBA", (256, 256), (255, 0, 0, 255))
