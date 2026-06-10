import sys
from unittest.mock import MagicMock, patch

import pytest

from .conftest import mock_path


class TestCli:
    @patch("pathlib.Path.is_dir", return_value=True)
    @patch("wastickers_packer.cli.plan_packs")
    @patch("wastickers_packer.cli.create_pack")
    @patch("wastickers_packer.cli.pack_to_wastickers")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.write_bytes")
    def test_successful_run(
        self, mock_write, mock_mkdir, mock_p2w, mock_create, mock_plan, mock_is_dir
    ) -> None:
        mock_plan.return_value = {"My Pack": [mock_path("a.png")]}
        mock_create.return_value = MagicMock(id="my_pack", name="My Pack")
        mock_p2w.return_value = b"fake zip content"

        old_argv, sys.argv = sys.argv, ["wastickers-packer", "/fake/input", "-o", "/fake/output"]
        try:
            from wastickers_packer.cli import cli

            cli()
            mock_plan.assert_called_once()
            mock_create.assert_called_once()
            mock_p2w.assert_called_once()
        finally:
            sys.argv = old_argv

    @patch("pathlib.Path.is_dir", return_value=True)
    @patch("wastickers_packer.cli.plan_packs")
    @patch("wastickers_packer.cli.create_pack")
    @patch("wastickers_packer.cli.pack_to_wastickers")
    @patch("wastickers_packer.cli.write_index")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.write_bytes")
    def test_report_flag_generates_html(
        self, mock_write, mock_mkdir, mock_idx, mock_p2w, mock_create, mock_plan, mock_is_dir
    ) -> None:
        mock_plan.return_value = {"Pack": [mock_path("a.png")]}
        mock_create.return_value = MagicMock(id="pack", name="Pack")
        mock_p2w.return_value = b"zip"

        old_argv, sys.argv = (
            sys.argv,
            ["wastickers-packer", "/fake/input", "-o", "/fake/output", "--report"],
        )
        try:
            from wastickers_packer.cli import cli

            cli()
            mock_idx.assert_called_once()
        finally:
            sys.argv = old_argv

    @patch("pathlib.Path.is_dir", return_value=True)
    @patch("wastickers_packer.cli.plan_packs")
    @patch("wastickers_packer.cli.create_pack")
    @patch("wastickers_packer.cli.pack_to_wastickers")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.write_bytes")
    def test_publisher_flag_is_passed_through(
        self, mock_write, mock_mkdir, mock_p2w, mock_create, mock_plan, mock_is_dir
    ) -> None:
        mock_plan.return_value = {"Pack": [mock_path("a.png")]}
        mock_create.return_value = MagicMock(id="pack", name="Pack")
        mock_p2w.return_value = b"zip"

        old_argv, sys.argv = (
            sys.argv,
            [
                "wastickers-packer",
                "/fake/input",
                "-o",
                "/fake/output",
                "--publisher",
                "CustomPub",
            ],
        )
        try:
            from wastickers_packer.cli import cli

            cli()
            _, kwargs = mock_create.call_args
            assert kwargs["publisher"] == "CustomPub"
        finally:
            sys.argv = old_argv

    @patch("pathlib.Path.is_dir", return_value=False)
    def test_exits_when_input_missing(self, mock_is_dir) -> None:
        old_argv, sys.argv = sys.argv, ["wastickers-packer", "/nonexistent/path"]
        try:
            from wastickers_packer.cli import cli

            with pytest.raises(SystemExit) as exc:
                cli()
            assert exc.value.code == 1
        finally:
            sys.argv = old_argv

    @patch("pathlib.Path.is_dir", return_value=False)
    def test_exits_when_input_is_file(self, mock_is_dir) -> None:
        old_argv, sys.argv = sys.argv, ["wastickers-packer", "/fake/file.txt"]
        try:
            from wastickers_packer.cli import cli

            with pytest.raises(SystemExit) as exc:
                cli()
            assert exc.value.code == 1
        finally:
            sys.argv = old_argv
