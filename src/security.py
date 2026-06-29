"""
PictoMusic Security Module
Input validation, rate limiting, CSP headers, and sanitization.
"""

import hashlib
import io
import re
import time
import socket
import logging
from pathlib import Path
from urllib.parse import urlparse

from config import (
    CSP_FONT_SOURCES,
    CSP_FRAME_ANCESTORS,
    CSP_IMG_SOURCES,
    CSP_MEDIA_SOURCES,
    CSP_STYLE_SOURCES,
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
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
        HEIF_SUPPORT_AVAILABLE = True
    except ImportError:
        HEIF_SUPPORT_AVAILABLE = False
except ImportError:
    Image = None
    HEIF_SUPPORT_AVAILABLE = False

HEIF_IMAGE_EXTENSIONS = {".heic", ".heif"}
HEIF_BRANDS = {
    b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis",
    b"mif1", b"msf1",
}
INFERRED_IMAGE_EXTENSIONS = {
    "jpeg": ".jpg",
    "png": ".png",
    "webp": ".webp",
    "heif": ".heic",
}
JPEG_QUALITY_STEPS = (92, 86, 80, 74, 68, 60)
JPEG_RESIZE_STEPS = (1.0, 0.85, 0.72, 0.60, 0.50, 0.42, 0.35)



def patch_urllib3_dns_pinning() -> None:
    """Patch urllib3 to pin resolved IP addresses and block private IPs.

    This mitigates DNS rebinding / SSRF attacks.
    """
    try:
        import urllib3.util.connection as urllib3_connection

        orig_create_connection = urllib3_connection.create_connection

        def safe_create_connection(address, *args, **kwargs):
            host, port = address
            try:
                infos = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
                if not infos:
                    raise socket.error("DNS resolution returned no addresses.")

                # Check resolved IPs
                for family, socktype, proto, canonname, sockaddr in infos:
                    ip = sockaddr[0]
                    for prefix in _BLOCKED_IP_PREFIXES:
                        if ip.startswith(prefix):
                            raise socket.error(
                                f"Access to private/internal IP address {ip} is blocked."
                            )

                # Enforce direct connection to the resolved IP to prevent DNS rebinding
                resolved_ip = infos[0][4][0]
                return orig_create_connection((resolved_ip, port), *args, **kwargs)
            except Exception as e:
                if isinstance(e, socket.error):
                    raise e
                raise socket.error(f"Connection validation failed: {e}")

        urllib3_connection.create_connection = safe_create_connection
        logging.info("urllib3 DNS pinning patch applied successfully.")
    except Exception as exc:
        logging.warning("Could not apply urllib3 DNS pinning patch: %s", exc)


# Apply patch immediately on module load
patch_urllib3_dns_pinning()


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


def build_uploaded_image_cache_key(filename: str, image_bytes: bytes) -> str:
    """Build a stable cache key that changes when upload content changes."""
    digest = hashlib.sha256(image_bytes).hexdigest()[:16]
    safe_name = sanitize_filename(filename or "upload")
    return f"upload_{safe_name}_{len(image_bytes)}_{digest}"


def read_uploaded_image_bytes(file_obj) -> bytes:
    """Read Streamlit upload bytes across browser/session object variants."""
    if file_obj is None:
        raise ValueError("No file provided.")

    image_bytes = None
    read_error = None
    try:
        getvalue = getattr(file_obj, "getvalue", None)
        if callable(getvalue):
            candidate = getvalue()
            if isinstance(candidate, (bytes, bytearray, memoryview)):
                image_bytes = candidate
    except Exception as exc:
        read_error = exc

    if image_bytes is None:
        try:
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            image_bytes = file_obj.read()
        except Exception as exc:
            read_error = exc

    try:
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
    except Exception:
        pass

    if image_bytes is None and read_error is not None:
        raise ValueError(f"Could not read uploaded file: {read_error}") from read_error

    if isinstance(image_bytes, memoryview):
        image_bytes = image_bytes.tobytes()
    if isinstance(image_bytes, bytearray):
        image_bytes = bytes(image_bytes)
    if not isinstance(image_bytes, bytes):
        raise ValueError("Could not read uploaded file bytes.")
    return image_bytes


def validate_uploaded_image_bytes(filename: str, image_bytes: bytes) -> None:
    """Validate uploaded image bytes. Raises ValueError on failure."""
    if image_bytes is None:
        raise ValueError("No file provided.")

    size = len(image_bytes)

    if size > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError(
            f"File size ({size / (1024*1024):.1f} MB) exceeds the "
            f"maximum of {MAX_UPLOAD_SIZE_MB} MB."
        )

    if size == 0:
        raise ValueError("Uploaded file is empty.")

    ext = Path(filename or "").suffix.lower()
    if not ext:
        ext = infer_image_extension(image_bytes)
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(
            f"File extension '{ext}' is not allowed. "
            f"Use one of: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )

    valid = has_supported_image_header(image_bytes, ext)

    if not valid:
        raise ValueError(
            "File does not appear to be a valid image. "
            "The file header does not match any supported image format."
        )

    if ext in HEIF_IMAGE_EXTENSIONS and not HEIF_SUPPORT_AVAILABLE:
        raise ValueError(
            "HEIC/HEIF mobile photos are supported only when pillow-heif is installed. "
            "Please try JPG, PNG, or WEBP."
        )

    validate_image_content(image_bytes)


def infer_image_extension(image_bytes: bytes) -> str:
    """Infer a safe upload extension from image container bytes."""
    header = image_bytes[:64]
    if header.startswith(b"\xff\xd8\xff"):
        return INFERRED_IMAGE_EXTENSIONS["jpeg"]
    if header.startswith(b"\x89PNG"):
        return INFERRED_IMAGE_EXTENSIONS["png"]
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return INFERRED_IMAGE_EXTENSIONS["webp"]
    if is_heif_container(header):
        return INFERRED_IMAGE_EXTENSIONS["heif"]
    return ""


def has_supported_image_header(image_bytes: bytes, extension: str = "") -> bool:
    """Return True when bytes match a supported upload image container."""
    header = image_bytes[:64]
    ext = str(extension or "").lower()

    if any(header.startswith(magic) for magic in _IMAGE_MAGIC_BYTES):
        if header[:4] == b"RIFF":
            return header[8:12] == b"WEBP"
        return True

    if ext in HEIF_IMAGE_EXTENSIONS:
        return is_heif_container(header)

    return False


def is_heif_container(header: bytes) -> bool:
    """Detect HEIC/HEIF files without accepting arbitrary MP4 containers."""
    if len(header) < 12 or header[4:8] != b"ftyp":
        return False

    major_brand = header[8:12].lower()
    compatible_brands = {
        header[idx: idx + 4].lower()
        for idx in range(16, min(len(header), 64), 4)
        if len(header[idx: idx + 4]) == 4
    }
    return major_brand in HEIF_BRANDS or bool(HEIF_BRANDS & compatible_brands)


def _resize_image(image, scale: float):
    """Return a scaled copy of an image, preserving tiny dimensions."""
    if scale >= 1.0:
        return image

    width, height = image.size
    resized_size = (
        max(1, int(width * scale)),
        max(1, int(height * scale)),
    )
    resampling = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
    return image.resize(resized_size, resample=resampling)


def _encode_jpeg(image, quality: int) -> bytes:
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=quality, optimize=True)
    return output.getvalue()


def encode_jpeg_under_size_limit(image, max_bytes: int = MAX_UPLOAD_SIZE_BYTES) -> bytes:
    """Encode RGB image bytes as JPEG without exceeding the upload limit."""
    last_size = 0
    for scale in JPEG_RESIZE_STEPS:
        candidate = _resize_image(image, scale)
        for quality in JPEG_QUALITY_STEPS:
            encoded = _encode_jpeg(candidate, quality)
            last_size = len(encoded)
            if last_size <= max_bytes:
                return encoded

    limit_text = (
        f"{max_bytes / (1024 * 1024):.1f} MB"
        if max_bytes >= 1024 * 1024
        else f"{max_bytes} bytes"
    )
    raise ValueError(
        "Converted HEIC/HEIF image exceeds the maximum upload size of "
        f"{limit_text} after JPEG conversion "
        f"({last_size} bytes). Please try JPG, PNG, or WEBP."
    )


def prepare_uploaded_image_bytes(filename: str, image_bytes: bytes) -> tuple[str, bytes, bool]:
    """Validate and normalize mobile uploads to browser-safe image bytes.

    HEIC/HEIF is common from phone galleries but is not reliably previewable in
    browsers or downstream image tooling, so it is decoded and re-encoded as JPEG.
    """
    validate_uploaded_image_bytes(filename, image_bytes)

    ext = Path(filename or "").suffix.lower() or infer_image_extension(image_bytes)
    raw_name = filename or f"mobile_upload{ext or '.jpg'}"
    if not Path(raw_name).suffix and ext:
        raw_name = f"{raw_name}{ext}"
    safe_name = sanitize_filename(raw_name)
    if ext not in HEIF_IMAGE_EXTENSIONS:
        return safe_name, image_bytes, False

    if Image is None or not HEIF_SUPPORT_AVAILABLE:
        raise ValueError(
            "This mobile image format requires HEIC/HEIF support on the server. "
            "Please try JPG, PNG, or WEBP."
        )

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
        if image.mode not in {"RGB", "L"}:
            image = image.convert("RGB")
        elif image.mode == "L":
            image = image.convert("RGB")

        converted_bytes = encode_jpeg_under_size_limit(image)
        validate_image_content(converted_bytes)

        stem = Path(safe_name).stem or "mobile_upload"
        return f"{stem}.jpg", converted_bytes, True
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Could not convert mobile HEIC/HEIF image: {exc}") from exc


def validate_uploaded_file(file_obj) -> None:
    """Validate an uploaded file-like object. Raises ValueError on failure."""
    image_bytes = read_uploaded_image_bytes(file_obj)
    validate_uploaded_image_bytes(getattr(file_obj, "name", ""), image_bytes)


def validate_image_content(image_bytes: bytes) -> bool:
    """Actually decode image bytes with PIL to catch malformed/bomb images.
    Returns True if valid, raises ValueError otherwise.
    """
    if Image is None:
        return True  # Skip validation if PIL not available

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
