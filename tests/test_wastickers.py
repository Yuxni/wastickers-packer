import zipfile
from io import BytesIO
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from PIL import Image

from wastickers_packer.wastickers import (
    ProcessedPack,
    create_pack,
    pack_to_wastickers,
    _sticker_to_webp,
    _image_to_png,
    _image_to_bytes,
)
from wastickers_packer.exceptions import ImageConversionError

from .conftest import mock_path

# Capture the real Image.open once at module load, before any @patch runs.
_real_image_open = Image.open


def _smart_img_open(sample_image: Image.Image):
    """Side-effect for Image.open mock: file paths return stub, BytesIO delegates."""
    def side_effect(fp, *args, **kwargs):
        if isinstance(fp, BytesIO):
            return _real_image_open(fp, *args, **kwargs)
        return sample_image
    return side_effect

class TestImageConversion:
    def test_sticker_to_webp_returns_512x512_webp_bytes(self, sample_image) -> None:
        result = _sticker_to_webp(sample_image)
        img = Image.open(BytesIO(result))
        assert img.mode == "RGBA"
        assert img.size == (512, 512)

    def test_sticker_to_webp_under_100kb(self, sample_image) -> None:
        result = _sticker_to_webp(sample_image)
        assert len(result) / 1024 <= 100

    def test_tray_to_png_returns_96x96_png_bytes(self, sample_image) -> None:
        result = _image_to_png(sample_image)
        img = Image.open(BytesIO(result))
        assert img.mode == "RGBA"
        assert img.size == (96, 96)

    def test_image_to_bytes_returns_non_empty(self, sample_image) -> None:
        data = _image_to_bytes(sample_image, "PNG")
        assert isinstance(data, bytes)
        assert len(data) > 0

class TestCreatePack:
    @patch("PIL.Image.open")
    def test_metadata(self, mock_img_open, sample_image) -> None:
        mock_img_open.side_effect = _smart_img_open(sample_image)
        pack = create_pack("Test Pack", [mock_path("a.png")], publisher="TestPub")

        assert pack.id == "test_pack"
        assert pack.name == "Test Pack"
        assert pack.publisher == "TestPub"

    @patch("PIL.Image.open")
    def test_stickers_are_512x512_rgba(self, mock_img_open, sample_image) -> None:
        mock_img_open.side_effect = _smart_img_open(sample_image)
        pack = create_pack("Test", [mock_path(f"img_{i}.png") for i in range(3)], "Pub")

        for sticker_bytes in pack.stickers:
            img = Image.open(BytesIO(sticker_bytes))
            assert img.mode == "RGBA"
            assert img.size == (512, 512)

    def test_raises_on_empty_images(self) -> None:
        with pytest.raises(ImageConversionError, match="No valid stickers"):
            create_pack("Empty", [], "Pub")

    @patch("PIL.Image.open")
    def test_sanitizes_pack_id(self, mock_img_open, sample_image) -> None:
        mock_img_open.side_effect = _smart_img_open(sample_image)
        pack = create_pack("My Cool Pack!!!", [mock_path("a.png")], "Pub")

        assert pack.id == "my_cool_pack"

    @patch("PIL.Image.open")
    def test_tray_is_present(self, mock_img_open, sample_image) -> None:
        mock_img_open.side_effect = _smart_img_open(sample_image)
        pack = create_pack("Test", [mock_path("a.png"), mock_path("b.png")], "Pub")

        assert isinstance(pack.tray, bytes)
        img = Image.open(BytesIO(pack.tray))
        assert img.size == (96, 96)

    @patch("PIL.Image.open")
    @patch("wastickers_packer.wastickers._animated_to_webp")
    def test_animated_path_uses_animated_to_webp(
        self, mock_anim, mock_img_open, sample_image
    ) -> None:
        mock_img = MagicMock(spec=Image.Image)
        type(mock_img).is_animated = PropertyMock(return_value=True)
        type(mock_img).n_frames = PropertyMock(return_value=3)
        mock_img.copy.return_value = sample_image
        mock_img.convert.return_value = sample_image
        mock_img.seek.return_value = None
        mock_img.info = {"duration": 50}

        mock_img_open.return_value = mock_img
        mock_anim.return_value = b"animated webp bytes"

        pack = create_pack("Animated", [mock_path("anim.webp")], "Pub")

        assert pack.stickers[0] == b"animated webp bytes"
        mock_anim.assert_called_once_with(mock_img)



def _png_bytes(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _webp_bytes(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, "WEBP")
    return buf.getvalue()


class TestPackToWastickers:
    def test_returns_non_empty_bytes(self, sample_image) -> None:
        data = pack_to_wastickers(
            ProcessedPack("test", "Test", "Pub", [_webp_bytes(sample_image)],
                          _png_bytes(sample_image))
        )
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_zip_structure(self, sample_image) -> None:
        data = pack_to_wastickers(
            ProcessedPack("test", "Test", "Pub", [_webp_bytes(sample_image)],
                          _png_bytes(sample_image))
        )
        with zipfile.ZipFile(BytesIO(data)) as zf:
            assert set(zf.namelist()) == {
                "author.txt", "title.txt", "tray.png", "sticker_01.webp",
            }

    def test_zip_metadata(self, sample_image) -> None:
        data = pack_to_wastickers(
            ProcessedPack("test", "MyPack", "MyPublisher",
                          [_webp_bytes(sample_image)], _png_bytes(sample_image))
        )
        with zipfile.ZipFile(BytesIO(data)) as zf:
            assert zf.read("author.txt").decode() == "MyPublisher"
            assert zf.read("title.txt").decode() == "MyPack"

    def test_round_trip_images_are_512x512_webp(self, sample_image) -> None:
        sticker_bytes = _sticker_to_webp(sample_image)
        data = pack_to_wastickers(
            ProcessedPack("test", "Test", "Pub",
                          [sticker_bytes, sticker_bytes],
                          _png_bytes(sample_image))
        )
        with zipfile.ZipFile(BytesIO(data)) as zf:
            for i in (1, 2):
                img = Image.open(BytesIO(zf.read(f"sticker_{i:02d}.webp")))
                assert img.size == (512, 512)
