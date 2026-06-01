from io import BytesIO
from unittest.mock import MagicMock, call

from PIL import Image

from whatsappsticker.report import write_index
from whatsappsticker.wastickers import ProcessedPack


def _tray_bytes() -> bytes:
    buf = BytesIO()
    Image.new("RGBA", (96, 96), (0, 255, 0, 255)).save(buf, "PNG")
    return buf.getvalue()


class TestWriteIndex:
    def test_writes_html_with_pack_info(self) -> None:
        output_dir = MagicMock()
        tray = _tray_bytes()

        write_index(output_dir, [
            ProcessedPack("p1", "Pack One", "Pub",
                          [Image.new("RGBA", (512, 512), (255, 0, 0, 255))],
                          tray),
        ])

        assert call("index.html") in output_dir.__truediv__.call_args_list
        html = output_dir.__truediv__.return_value.write_text.call_args[0][0]
        assert "<!DOCTYPE html>" in html
        assert "Pack One" in html
        assert "Pub" in html
        assert "1 stickers" in html

    def test_writes_html_with_multiple_packs(self) -> None:
        output_dir = MagicMock()
        tray_a = _tray_bytes()
        tray_b = _tray_bytes()

        write_index(output_dir, [
            ProcessedPack("a", "Pack A", "Pub",
                          [Image.new("RGBA", (512, 512), (255, 0, 0, 255))],
                          tray_a),
            ProcessedPack("b", "Pack B", "Pub",
                          [Image.new("RGBA", (512, 512), (0, 0, 255, 255))],
                          tray_b),
        ])

        assert call("a") in output_dir.__truediv__.call_args_list
        assert call("b") in output_dir.__truediv__.call_args_list
        html = output_dir.__truediv__.return_value.write_text.call_args[0][0]
        assert "Pack A" in html
        assert "Pack B" in html

    def test_creates_pack_subdirectories(self) -> None:
        output_dir = MagicMock()

        write_index(output_dir, [
            ProcessedPack("test_pack", "Test", "Pub",
                          [Image.new("RGBA", (512, 512), (255, 0, 0, 255))],
                          _tray_bytes()),
        ])

        assert call("test_pack") in output_dir.__truediv__.call_args_list
        assert call("index.html") in output_dir.__truediv__.call_args_list
