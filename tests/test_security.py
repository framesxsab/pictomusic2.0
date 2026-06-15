"""Tests for security module."""

import io
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from security import Image, escape_html, sanitize_filename, validate_image_url, validate_uploaded_file


VALID_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00"
    b"\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82"
)


class TestEscapeHtml:
    def test_escapes_angle_brackets(self):
        assert escape_html("<script>alert('xss')</script>") == (
            "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        )

    def test_escapes_ampersand(self):
        assert escape_html("A & B") == "A &amp; B"

    def test_escapes_quotes(self):
        assert escape_html('"hello"') == "&quot;hello&quot;"

    def test_handles_non_string(self):
        assert escape_html(123) == "123"

    def test_handles_empty_string(self):
        assert escape_html("") == ""


class TestSanitizeFilename:
    def test_removes_path_traversal(self):
        result = sanitize_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_safe_filename_unchanged(self):
        result = sanitize_filename("photo.jpg")
        assert result == "photo.jpg"

    def test_special_chars_replaced(self):
        result = sanitize_filename("my file (1).jpg")
        assert " " not in result
        assert "(" not in result

    def test_empty_filename(self):
        result = sanitize_filename("")
        assert len(result) > 0

    def test_dotfile_gets_prefix(self):
        result = sanitize_filename(".hidden")
        assert not result.startswith(".")

    def test_truncates_long_names(self):
        result = sanitize_filename("a" * 300 + ".jpg")
        assert len(result) <= 255


class TestValidateImageUrl:
    @patch("security.socket.gethostbyname", return_value="93.184.216.34")
    def test_valid_https_url(self, mock_dns):
        result = validate_image_url("https://example.com/image.jpg")
        assert result == "https://example.com/image.jpg"

    def test_empty_url(self):
        with pytest.raises(ValueError, match="non-empty string"):
            validate_image_url("")

    def test_url_too_long(self):
        long_url = "https://example.com/" + "a" * 2100
        with pytest.raises(ValueError, match="maximum length"):
            validate_image_url(long_url)

    def test_disallowed_scheme(self):
        with pytest.raises(ValueError, match="scheme"):
            validate_image_url("ftp://example.com/image.jpg")

    @patch("security.socket.gethostbyname", return_value="192.168.1.1")
    def test_private_ip_blocked(self, mock_dns):
        with pytest.raises(ValueError, match="internal/private"):
            validate_image_url("https://internal.example.com/image.jpg")

    @patch("security.socket.gethostbyname", return_value="127.0.0.1")
    def test_localhost_blocked(self, mock_dns):
        with pytest.raises(ValueError, match="internal/private"):
            validate_image_url("https://localhost/image.jpg")

    @patch("security.socket.gethostbyname", return_value="10.0.0.1")
    def test_class_a_private_blocked(self, mock_dns):
        with pytest.raises(ValueError, match="internal/private"):
            validate_image_url("https://private.local/image.jpg")


class TestValidateUploadedFile:
    def test_none_file(self):
        with pytest.raises(ValueError, match="No file"):
            validate_uploaded_file(None)

    def test_empty_file(self):
        file = io.BytesIO(b"")
        file.name = "empty.jpg"
        with pytest.raises(ValueError, match="empty"):
            validate_uploaded_file(file)

    def test_wrong_extension(self):
        file = io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 100)
        file.name = "document.pdf"
        with pytest.raises(ValueError, match="extension"):
            validate_uploaded_file(file)

    def test_wrong_magic_bytes(self):
        file = io.BytesIO(b"%PDF-1.4" + b"\x00" * 100)
        file.name = "fake.jpg"
        with pytest.raises(ValueError, match="valid image"):
            validate_uploaded_file(file)

    def test_fake_jpeg_header_is_rejected_by_decode_validation(self):
        if Image is None:
            pytest.skip("Pillow is not installed in this Python environment")
        file = io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 100)
        file.name = "photo.jpg"
        with pytest.raises(ValueError, match="decoded"):
            validate_uploaded_file(file)

    def test_valid_png(self):
        file = io.BytesIO(VALID_PNG_BYTES)
        file.name = "photo.png"
        validate_uploaded_file(file)  # Should not raise
        assert file.tell() == 0

    def test_file_too_large(self):
        # Create a mock file that reports size > 10MB
        file = MagicMock()
        file.name = "big.jpg"
        file.tell.return_value = 11 * 1024 * 1024  # 11 MB
        file.read.return_value = b"\xff\xd8\xff" + b"\x00" * 100
        with pytest.raises(ValueError, match="exceeds"):
            validate_uploaded_file(file)
