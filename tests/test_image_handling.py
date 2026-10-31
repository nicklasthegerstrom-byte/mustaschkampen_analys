import io
import pytest
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()


def make_jpeg(size=(200, 200), color=(120, 80, 60)) -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_png(size=(200, 200), color=(100, 150, 200)) -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_rgba_png(size=(200, 200)) -> bytes:
    img = Image.new("RGBA", size, (100, 150, 200, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestImageOpen:
    def test_jpeg_opens_as_rgb(self):
        data = make_jpeg()
        img = Image.open(io.BytesIO(data)).convert("RGB")
        assert img.mode == "RGB"

    def test_png_opens_as_rgb(self):
        data = make_png()
        img = Image.open(io.BytesIO(data)).convert("RGB")
        assert img.mode == "RGB"

    def test_rgba_converts_to_rgb(self):
        data = make_rgba_png()
        img = Image.open(io.BytesIO(data)).convert("RGB")
        assert img.mode == "RGB"

    def test_invalid_data_raises(self):
        with pytest.raises(Exception):
            Image.open(io.BytesIO(b"not an image")).convert("RGB")

    def test_large_image_stays_rgb(self):
        data = make_jpeg(size=(3000, 3000))
        img = Image.open(io.BytesIO(data)).convert("RGB")
        assert img.mode == "RGB"
        assert img.size == (3000, 3000)


class TestConvertRgb:
    """Kontrollerar att .convert('RGB') inte kraschar på olika lägen."""

    def test_l_mode(self):
        img = Image.new("L", (100, 100), 128)
        result = img.convert("RGB")
        assert result.mode == "RGB"

    def test_p_mode(self):
        img = Image.new("P", (100, 100))
        result = img.convert("RGB")
        assert result.mode == "RGB"

    def test_rgba_mode(self):
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        result = img.convert("RGB")
        assert result.mode == "RGB"
