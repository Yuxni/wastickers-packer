from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from whatsappsticker.grouping import (
    _display_name,
    _split_flat,
    plan_packs,
)
from whatsappsticker.exceptions import InputError

from .conftest import mock_path


DISPLAY_NAME_CASES = [
    ("cute_animals", "Cute Animals"),
    ("funny-memes", "Funny Memes"),
    ("best_of_both-worlds", "Best Of Both Worlds"),
    ("simple", "Simple"),
    ("ALLCAPS", "Allcaps"),
]


@pytest.mark.parametrize("raw,expected", DISPLAY_NAME_CASES)
def test_display_name(raw: str, expected: str) -> None:
    assert _display_name(raw) == expected


def _paths(n: int) -> list:
    return [mock_path(f"img_{i:02d}.png") for i in range(n)]


class TestSplitFlat:
    def test_single_pack_when_under_max(self) -> None:
        images = _paths(4)
        result = _split_flat(images, "My Pack")
        assert result == {"My Pack": images}

    def test_splits_into_multiple_packs_when_over_max(self) -> None:
        images = _paths(35)
        result = _split_flat(images, "Big Pack")
        assert list(result) == ["Big Pack 1", "Big Pack 2"]
        assert len(result["Big Pack 1"]) == 30
        assert len(result["Big Pack 2"]) == 5

    def test_exact_minimum_succeeds(self) -> None:
        assert len(_split_flat(_paths(3), "Exact")["Exact"]) == 3

    def test_pads_two_to_three(self) -> None:
        result = _split_flat(_paths(2), "Small")
        assert len(result["Small"]) == 3
        # third entry is duplicate of first (cycling: 2 % 2 == 0)
        assert result["Small"][2].name == "img_00.png"

    def test_pads_one_to_three(self) -> None:
        result = _split_flat(_paths(1), "Single")
        assert len(result["Single"]) == 3

    def test_empty_returns_empty(self) -> None:
        assert _split_flat([], "Empty") == {}


class TestPlanPacks:
    @patch("whatsappsticker.grouping.scan_subfolders")
    def test_subfolder_mode(self, mock_subfolders) -> None:
        mock_subfolders.return_value = [
            ("animals", [mock_path("cat.png")] * 4),
            ("food", [mock_path("pizza.png")] * 4),
        ]

        packs = plan_packs(MagicMock(spec=Path))

        assert set(packs) == {"Animals", "Food"}
        assert len(packs["Animals"]) == 4

    @patch("whatsappsticker.grouping.scan_subfolders")
    @patch("whatsappsticker.grouping.scan")
    def test_flat_mode_without_name_uses_folder_name(
        self, mock_scan, mock_subfolders
    ) -> None:
        mock_subfolders.return_value = []
        mock_scan.return_value = _paths(4)

        input_dir = MagicMock(spec=Path)
        type(input_dir).name = PropertyMock(return_value="my_folder")

        packs = plan_packs(input_dir)

        assert "My Folder" in packs

    @patch("whatsappsticker.grouping.scan_subfolders")
    @patch("whatsappsticker.grouping.scan")
    def test_flat_mode_with_custom_name(
        self, mock_scan, mock_subfolders
    ) -> None:
        mock_subfolders.return_value = []
        mock_scan.return_value = _paths(4)

        packs = plan_packs(MagicMock(spec=Path), name="Custom Name")

        assert "Custom Name" in packs

    @patch("whatsappsticker.grouping.scan_subfolders")
    @patch("whatsappsticker.grouping.scan")
    def test_raises_on_empty_input(
        self, mock_scan, mock_subfolders
    ) -> None:
        mock_subfolders.return_value = []
        mock_scan.return_value = []

        with pytest.raises(InputError):
            plan_packs(MagicMock(spec=Path))

    @patch("whatsappsticker.grouping.scan_subfolders")
    def test_subfolder_raises_when_over_max(self, mock_subfolders) -> None:
        mock_subfolders.return_value = [
            ("Many", _paths(31)),
        ]

        with pytest.raises(InputError, match="maximum"):
            plan_packs(MagicMock(spec=Path))

    @patch("whatsappsticker.grouping.scan_subfolders")
    def test_subfolder_pads_below_minimum(self, mock_subfolders) -> None:
        mock_subfolders.return_value = [
            ("Tiny", _paths(2)),
        ]

        packs = plan_packs(MagicMock(spec=Path))

        assert "Tiny" in packs
        assert len(packs["Tiny"]) == 3

    @patch("whatsappsticker.grouping.scan_subfolders")
    def test_subfolder_allows_mixed_content(self, mock_subfolders) -> None:
        """Mixed static/animated in a subfolder is now allowed."""
        mock_subfolders.return_value = [
            ("Mixed", [mock_path("a.webp"), mock_path("b.webp"),
                       mock_path("c.png"), mock_path("d.png")]),
        ]

        packs = plan_packs(MagicMock(spec=Path))

        assert "Mixed" in packs
        assert len(packs["Mixed"]) == 4
