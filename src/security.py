"""
PictoMusic Security Module
Input validation, rate limiting, CSP headers, and sanitization.
"""

import re
import time
import socket
import logging
from pathlib import Path
from urllib.parse import urlparse

from config import (
    MAX_UPLOAD_SIZE_BYTES,
    MAX_UPLOAD_SIZE_MB,
    MAX_URL_LENGTH,
    ALLOWED_URL_SCHEMES,
    ALLOWED_IMAGE_EXTENSIONS,
    _BLOCKED_IP_PREFIXES,
    _IMAGE_MAGIC_BYTES,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    MAX_IMAGE_PIXELS,
)

try:
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
except ImportError:
    Image = None


def escape_html(text: str) -> str:
    """Escape HTML special characters to prevent injection."""
    if not isinstance(text, str):
        return str(text)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def validate_image_url(url: str) -> str:
    """Validate an image URL for safety. Raises ValueError on failure."""
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string.")

    url = url.strip()

    if len(url) > MAX_URL_LENGTH:
        raise ValueError(f"URL exceeds maximum length of {MAX_URL_LENGTH} characters.")

    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_URL_SCHEMES:
        raise ValueError(
            f"URL scheme '{parsed.scheme}' is not allowed. "
            f"Use one of: {', '.join(ALLOWED_URL_SCHEMES)}"
        )

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must contain a valid hostname.")

    try:
        ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        raise ValueError(f"Could not resolve hostname: {hostname}")

    for prefix in _BLOCKED_IP_PREFIXES:
        if ip.startswith(prefix):
            raise ValueError("Access to internal/private network addresses is not allowed.")

    return url


def validate_uploaded_file(file_obj) -> None:
    """Validate an uploaded file (Streamlit UploadedFile). Raises ValueError on failure."""
    if file_obj is None:
        raise ValueError("No file provided.")

    file_obj.seek(0, 2)
    size = file_obj.tell()
    file_obj.seek(0)

    if size > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError(
            f"File size ({size / (1024*1024):.1f} MB) exceeds the "
            f"maximum of {MAX_UPLOAD_SIZE_MB} MB."
        )

    if size == 0:
        raise ValueError("Uploaded file is empty.")

    name = getattr(file_obj, "name", "")
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(
            f"File extension '{ext}' is not allowed. "
            f"Use one of: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )

    header = file_obj.read(12)
    file_obj.seek(0)

    valid = any(header.startswith(magic) for magic in _IMAGE_MAGIC_BYTES)
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        valid = True

    if not valid:
        raise ValueError(
            "File does not appear to be a valid image. "
            "The file header does not match any supported image format."
        )


def validate_image_content(image_bytes: bytes) -> bool:
    """Actually decode image bytes with PIL to catch malformed/bomb images.
    Returns True if valid, raises ValueError otherwise.
    """
    if Image is None:
        return True  # Skip validation if PIL not available

    import io
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        return True
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError(
            "Image is too large (potential decompression bomb). "
            f"Max allowed: {MAX_IMAGE_PIXELS:,} pixels."
        )
    except Exception as e:
        raise ValueError(f"Image could not be decoded: {e}")


def sanitize_filename(name: str) -> str:
    """Strip path traversal characters and enforce safe naming."""
    name = Path(name).name
    name = re.sub(r'[^\w\-.]', '_', name)
    if not name or name.startswith('.'):
        name = "upload" + name
    return name[:255]


class RateLimiter:
    """Session-based rate limiter using Streamlit session state."""

    def __init__(
        self,
        max_requests: int = RATE_LIMIT_MAX_REQUESTS,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._key = "_rate_limiter_timestamps"

    def _get_timestamps(self) -> list:
        import streamlit as st
        if self._key not in st.session_state:
            st.session_state[self._key] = []
        return st.session_state[self._key]

    def check(self) -> bool:
        """Returns True if request is allowed, False if rate limited."""
        import streamlit as st
        now = time.time()
        timestamps = self._get_timestamps()
        cutoff = now - self.window_seconds
        timestamps = [t for t in timestamps if t > cutoff]
        st.session_state[self._key] = timestamps

        if len(timestamps) >= self.max_requests:
            return False

        timestamps.append(now)
        st.session_state[self._key] = timestamps
        return True

    def seconds_until_available(self) -> float:
        """How many seconds until the next request slot opens."""
        now = time.time()
        timestamps = self._get_timestamps()
        cutoff = now - self.window_seconds
        timestamps = [t for t in timestamps if t > cutoff]
        if len(timestamps) < self.max_requests:
            return 0.0
        oldest = min(timestamps)
        return max(0.0, oldest + self.window_seconds - now)


def inject_csp_headers() -> None:
    """Inject Content-Security-Policy via meta tag."""
    import streamlit as st
    csp = (
        "default-src 'self'; "
        "img-src 'self' https://*.scdn.co https://* data:; "
        "media-src 'self' https://p.scdn.co https://*.scdn.co; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "connect-src 'self' https://*; "
        "frame-ancestors 'self' https://huggingface.co https://*.hf.space;"
    )
    st.markdown(
        f'<meta http-equiv="Content-Security-Policy" content="{csp}">',
        unsafe_allow_html=True,
    )
