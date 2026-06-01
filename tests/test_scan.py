from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from whatsappsticker.scan import is_animated, sanitize, scan, scan_subfolders

from .conftest import mock_path


# ---------------------------------------------------------------------------
# is_animated()
# ---------------------------------------------------------------------------

class TestIsAnimated:
    @patch("whatsappsticker.scan.Image.open")
    def test_true_when_is_animated_set(self, mock_open) -> None:
        mock_img = MagicMock()
        mock_img.__enter__.return_value = mock_img
        type(mock_img).is_animated = PropertyMock(return_value=True)
        mock_open.return_value = mock_img

        assert is_animated(mock_path("anim.webp"))

    @patch("whatsappsticker.scan.Image.open")
    def test_false_when_not_animated(self, mock_open) -> None:
        mock_img = MagicMock()
        mock_img.__enter__.return_value = mock_img
        type(mock_img).is_animated = PropertyMock(return_value=False)
        mock_open.return_value = mock_img

        assert not is_animated(mock_path("static.png"))

    @patch("whatsappsticker.scan.Image.open")
    def test_false_when_attr_missing(self, mock_open) -> None:
        mock_img = MagicMock(spec=["__enter__", "__exit__"])
        mock_img.__enter__.return_value = mock_img
        mock_img.__exit__.return_value = False
        mock_open.return_value = mock_img

        assert not is_animated(mock_path("static.png"))


# ---------------------------------------------------------------------------
# sanitize() — pure string logic, no I/O needed
# ---------------------------------------------------------------------------

SANITIZE_CASES = [
    ("HelloWorld", "helloworld"),
    ("foo bar baz!", "foo_bar_baz"),
    ("foo___bar", "foo_bar"),
    ("__hello__", "hello"),
    ("", "pack"),
    ("!!!", "pack"),
    ("my-pack", "my-pack"),
    ("pack123", "pack123"),
]


@pytest.mark.parametrize("raw,expected", SANITIZE_CASES)
def test_sanitize(raw: str, expected: str) -> None:
    assert sanitize(raw) == expected


# ---------------------------------------------------------------------------
# scan()
# ---------------------------------------------------------------------------


class TestScan:
    def test_returns_sorted_image_files(self) -> None:
        folder = MagicMock(spec=Path)
        a = mock_path("a.png", suffix=".png")
        b = mock_path("b.png", suffix=".png")
        folder.iterdir.return_value = [b, a]

        result = scan(folder)

        assert result == [a, b]

    def test_ignores_dotfiles(self) -> None:
        folder = MagicMock(spec=Path)
        folder.iterdir.return_value = [
            mock_path(".hidden.png"),
            mock_path("img.png"),
        ]

        result = scan(folder)

        assert result == [folder.iterdir.return_value[1]]

    def test_ignores_unsupported_extensions(self) -> None:
        folder = MagicMock(spec=Path)
        folder.iterdir.return_value = [
            mock_path("img.png", suffix=".png"),
            mock_path("notes.txt", suffix=".txt"),
        ]

        result = scan(folder)

        assert result == [folder.iterdir.return_value[0]]

    def test_returns_empty_for_no_files(self) -> None:
        folder = MagicMock(spec=Path)
        folder.iterdir.return_value = []

        assert scan(folder) == []

    def test_skips_non_files(self) -> None:
        folder = MagicMock(spec=Path)
        folder.iterdir.return_value = [
            mock_path("subdir", is_file=False, is_dir=True),
            mock_path("img.png"),
        ]

        result = scan(folder)

        assert result == [folder.iterdir.return_value[1]]


# ---------------------------------------------------------------------------
# scan_subfolders()
# ---------------------------------------------------------------------------


class TestScanSubfolders:
    @patch("whatsappsticker.scan.scan")
    def test_returns_sorted_subfolders(self, mock_scan) -> None:
        root = MagicMock(spec=Path)
        root.iterdir.return_value = [
            mock_path("food", is_file=False, is_dir=True),
            mock_path("animals", is_file=False, is_dir=True),
        ]

        mock_scan.side_effect = lambda p: (
            [mock_path("a.png")] if p.name == "animals" else [mock_path("b.png")]
        )

        entries = scan_subfolders(root)

        assert [name for name, _ in entries] == ["animals", "food"]

    @patch("whatsappsticker.scan.scan")
    def test_skips_subfolders_without_images(self, mock_scan) -> None:
        root = MagicMock(spec=Path)
        root.iterdir.return_value = [
            mock_path("animals", is_file=False, is_dir=True),
            mock_path("empty", is_file=False, is_dir=True),
        ]

        mock_scan.side_effect = lambda p: (
            [mock_path("a.png")] if p.name == "animals" else []
        )

        entries = scan_subfolders(root)

        assert len(entries) == 1
        assert entries[0][0] == "animals"

    @patch("whatsappsticker.scan.scan")
    def test_skips_dot_prefixed_subfolders(self, mock_scan) -> None:
        root = MagicMock(spec=Path)
        root.iterdir.return_value = [
            mock_path(".hidden", is_file=False, is_dir=True),
            mock_path("visible", is_file=False, is_dir=True),
        ]
        mock_scan.return_value = [mock_path("a.png")]

        entries = scan_subfolders(root)

        assert len(entries) == 1
        assert entries[0][0] == "visible"

    def test_returns_empty_when_no_subdirs(self) -> None:
        root = MagicMock(spec=Path)
        root.iterdir.return_value = [mock_path("file.txt", is_file=True)]

        entries = scan_subfolders(root)

        assert entries == []
