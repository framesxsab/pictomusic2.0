"""PictoMusic - AI Music Discovery main Streamlit entrypoint."""

import io
import logging

import streamlit as st
from PIL import Image

from log_config import setup_logging

setup_logging()

from config import (
    APP_ICON,
    APP_SUBTITLE,
    APP_TITLE,
    APP_VERSION_TAG,
    DEMO_IMAGE_URL,
    HTTP_CHUNK_SIZE,
    MAX_UPLOAD_SIZE_BYTES,
    REQUEST_TIMEOUT,
)
from recommend import ImageMusicRecommender
from security import (
    RateLimiter,
    build_uploaded_image_cache_key,
    prepare_uploaded_image_bytes,
    read_uploaded_image_bytes,
    validate_image_content,
    validate_image_url,
)
from ui.components import (
    format_file_size,
    render_analysis_stage,
    render_dashboard_welcome,
    render_empty_result_guidance,
    render_hero_section,
    render_image_ready_panel,
    render_intake_panel_header,
    render_retrieval_summary,
    render_workspace_section_header,
)
from ui.results import render_results
from ui.sidebar import render_sidebar
from ui.styles import get_global_css


st.set_page_config(
    page_title=f"{APP_TITLE} - AI Music Discovery",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(get_global_css(), unsafe_allow_html=True)

rate_limiter = RateLimiter()
retrieval_options = render_sidebar()
image_source_option = retrieval_options["image_source_option"]

render_hero_section(APP_VERSION_TAG, APP_SUBTITLE)


def _clear_cached_image() -> None:
    st.session_state.pop("cached_file_key", None)
    st.session_state.pop("cached_image_bytes", None)
    st.session_state.pop("cached_file_error", None)
    st.session_state.pop("cached_image_detail", None)
    st.session_state.pop("cached_image_file_name", None)
    st.session_state.pop("cached_image_source_label", None)


def _clear_results() -> None:
    st.session_state.pop("recommendations", None)
    st.session_state.pop("show_results", None)
    st.session_state.pop("detected_themes", None)
    st.session_state.pop("search_context", None)
    st.session_state.pop("empty_recommendation_error", None)


def _describe_image_bytes(image_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        width, height = image.size
        image_format = str(image.format or "image").upper()
        return f"{image_format} - {width:,} x {height:,} px"
    except Exception:
        return "Validated image"


def _cache_valid_image(
    cache_key: str,
    image_bytes: bytes,
    source_label: str,
    file_name: str,
) -> None:
    if st.session_state.get("cached_file_key") != cache_key:
        _clear_results()
    st.session_state["cached_file_key"] = cache_key
    st.session_state["cached_image_bytes"] = image_bytes
    st.session_state["cached_file_error"] = None
    st.session_state["cached_image_detail"] = _describe_image_bytes(image_bytes)
    st.session_state["cached_image_file_name"] = file_name
    st.session_state["cached_image_source_label"] = source_label


def _cache_invalid_image(cache_key: str, message: str) -> None:
    if st.session_state.get("cached_file_key") != cache_key:
        _clear_results()
    st.session_state["cached_file_key"] = cache_key
    st.session_state["cached_image_bytes"] = None
    st.session_state["cached_file_error"] = message
    st.session_state["cached_image_detail"] = None
    st.session_state["cached_image_file_name"] = None
    st.session_state["cached_image_source_label"] = None


def _accept_uploaded_image(active_file, default_name: str, source_label: str) -> None:
    uploaded_name = getattr(active_file, "name", "") or default_name
    try:
        uploaded_bytes = read_uploaded_image_bytes(active_file)
    except ValueError as exc:
        _cache_invalid_image(f"upload_read_error_{uploaded_name}", str(exc))
        return

    cache_key = build_uploaded_image_cache_key(uploaded_name, uploaded_bytes)
    if st.session_state.get("cached_file_key") == cache_key:
        return

    try:
        prepared_name, prepared_bytes, was_converted = prepare_uploaded_image_bytes(
            uploaded_name,
            uploaded_bytes,
        )
        label = source_label
        if uploaded_name:
            label = f"{source_label}: {uploaded_name}"
        if was_converted:
            label = f"{label} converted to JPEG"
        _cache_valid_image(
            cache_key,
            prepared_bytes,
            label,
            prepared_name,
        )
    except ValueError as exc:
        _cache_invalid_image(cache_key, str(exc))


def _render_cached_upload_preview(fallback_name: str) -> tuple[object, str]:
    if st.session_state.get("cached_file_error"):
        st.error(f"Image validation failed: {st.session_state['cached_file_error']}")
        return None, ""
    if st.session_state.get("cached_image_bytes"):
        st.image(st.session_state["cached_image_bytes"], use_container_width=True)
        image_source = io.BytesIO(st.session_state["cached_image_bytes"])
        image_source.name = st.session_state.get("cached_image_file_name") or fallback_name
        image_detail = st.session_state.get("cached_image_detail", "Validated image")
        render_image_ready_panel(
            st.session_state.get("cached_image_source_label", "Uploaded image"),
            image_detail,
            format_file_size(len(st.session_state["cached_image_bytes"])),
        )
        return image_source, image_detail
    return None, ""


def _hide_native_gallery_uploader() -> None:
    st.markdown(
        """
<style>
[data-testid="stFileUploader"] {
    display: none !important;
}
</style>
""",
        unsafe_allow_html=True,
    )


def _reset_upload_widget(upload_method: str) -> None:
    nonce_key = "camera_upload_nonce" if upload_method == "Camera" else "gallery_upload_nonce"
    st.session_state[nonce_key] = int(st.session_state.get(nonce_key, 0)) + 1
    _clear_cached_image()
    _clear_results()
    st.rerun()


def _download_url_image(image_url: str) -> bytes:
    validated_url = validate_image_url(image_url)
    import requests

    response = requests.get(validated_url, stream=True, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    content_length = response.headers.get("Content-Length")
    if content_length and int(content_length) > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError(f"Remote image too large ({format_file_size(int(content_length))})")

    downloaded = []
    downloaded_size = 0
    for chunk in response.iter_content(chunk_size=HTTP_CHUNK_SIZE):
        downloaded_size += len(chunk)
        if downloaded_size > MAX_UPLOAD_SIZE_BYTES:
            raise ValueError("Remote image exceeds the 10 MB limit during download.")
        downloaded.append(chunk)

    image_bytes = b"".join(downloaded)
    validate_image_content(image_bytes)
    return image_bytes


image_source = None
image_detail = ""
col_left, col_right = st.columns([10, 12], gap="large")

with col_left:
    render_workspace_section_header(
        "Image desk",
        "Choose the visual",
        "Add one clear image, confirm it is ready, then start the match.",
    )

    # Reset cache when switching upload method
    if st.session_state.get("last_image_source_option") != image_source_option:
        st.session_state["last_image_source_option"] = image_source_option
        _clear_cached_image()
        _clear_results()

    if image_source_option == "Upload Image":
        st.session_state.setdefault("gallery_upload_nonce", 0)
        st.session_state.setdefault("camera_upload_nonce", 0)
        render_intake_panel_header(
            "Upload a frame",
            "Use a gallery photo, poster, camera shot, or celebration image. Mobile HEIC photos are accepted and converted before analysis.",
        )
        upload_method = st.radio(
            "Upload method",
            ("Gallery", "Camera"),
            horizontal=True,
            label_visibility="collapsed",
        )
        active_file = None
        if upload_method == "Gallery":
            active_file = st.file_uploader(
                "Choose an image from your phone gallery",
                type=["jpg", "jpeg", "png", "webp", "heic", "heif"],
                accept_multiple_files=False,
                label_visibility="collapsed",
                key=f"gallery_upload_{st.session_state['gallery_upload_nonce']}",
            )
        else:
            active_file = st.camera_input(
                "Take a photo",
                label_visibility="collapsed",
                key=f"camera_upload_{st.session_state['camera_upload_nonce']}",
            )

        if active_file is not None:
            default_name = "camera_capture.jpg" if upload_method == "Camera" else "mobile_upload.jpg"
            _accept_uploaded_image(active_file, default_name, upload_method)
            if upload_method == "Gallery" and not st.session_state.get("cached_file_error"):
                _hide_native_gallery_uploader()
            image_source, image_detail = _render_cached_upload_preview(default_name)
            if st.button("Clear image", use_container_width=True):
                _reset_upload_widget(upload_method)
        else:
            # Clear cache when file is removed
            _clear_cached_image()
            _clear_results()

    elif image_source_option == "Image URL":
        render_intake_panel_header(
            "Analyze from a URL",
            "Paste a public JPG, PNG, or WEBP link. Private, local, and oversized images are blocked before processing.",
        )
        url_actions = st.columns([1, 1])
        with url_actions[0]:
            if st.button("Use sample image", use_container_width=True):
                st.session_state["image_url_input"] = DEMO_IMAGE_URL
                _clear_cached_image()
                _clear_results()
        with url_actions[1]:
            if st.button("Clear image", use_container_width=True):
                st.session_state["image_url_input"] = ""
                _clear_cached_image()
                _clear_results()

        image_url = st.text_input(
            "Enter Image URL",
            placeholder=DEMO_IMAGE_URL,
            key="image_url_input",
            label_visibility="visible",
        )
        image_url = str(image_url or "").strip()
        if image_url:
            cache_key = f"url_{image_url}"
            if st.session_state.get("cached_file_key") != cache_key:
                try:
                    with st.spinner("Checking and previewing the image URL..."):
                        image_bytes = _download_url_image(image_url)
                    _cache_valid_image(cache_key, image_bytes, "Remote image", "url_image.jpg")
                except ValueError as exc:
                    _cache_invalid_image(cache_key, str(exc))
                except Exception as exc:
                    logging.warning("Image URL error: %s", exc)
                    _cache_invalid_image(
                        cache_key,
                        "Could not load image from this URL. Check that it is public and points directly to an image.",
                    )

            if st.session_state.get("cached_file_error"):
                st.error(f"URL validation failed: {st.session_state['cached_file_error']}")
            elif st.session_state.get("cached_image_bytes"):
                st.image(st.session_state["cached_image_bytes"], use_container_width=True)
                image_source = io.BytesIO(st.session_state["cached_image_bytes"])
                image_source.name = "url_image.jpg"
                image_detail = st.session_state.get("cached_image_detail", "Validated image")
                render_image_ready_panel(
                    st.session_state.get("cached_image_source_label", "Remote image"),
                    image_detail,
                    format_file_size(len(st.session_state["cached_image_bytes"])),
                )
        else:
            # Clear cache when URL is empty
            _clear_cached_image()
            _clear_results()

    st.markdown("<br>", unsafe_allow_html=True)
    if image_source is not None:
        render_retrieval_summary(retrieval_options, image_detail or "Validated image")

    analyze_disabled = image_source is None
    if analyze_disabled:
        st.markdown(
            '<p class="ready-hint">Add a valid image to unlock analysis.</p>',
            unsafe_allow_html=True,
        )

    if st.button("Analyze image", use_container_width=True, disabled=analyze_disabled):
        if image_source is None:
            st.warning("Please provide an image first.")
        elif not rate_limiter.check():
            wait_time = rate_limiter.seconds_until_available()
            st.warning(
                f"Rate limit reached. Please wait {wait_time:.0f} seconds before trying again."
            )
        else:
            try:
                stage_placeholder = st.empty()

                @st.cache_resource(show_spinner=False)
                def get_recommender():
                    status_placeholder = st.empty()
                    progress_placeholder = st.empty()

                    def progress_cb(current, total):
                        pct = int((current / total) * 100)
                        status_placeholder.text(f"Refreshing the music map... ({pct}%)")
                        progress_placeholder.progress(current / total)

                    status_placeholder.text("Preparing the music matcher...")
                    recommender = ImageMusicRecommender(progress_callback=progress_cb)

                    status_placeholder.empty()
                    progress_placeholder.empty()

                    if not recommender.is_ready:
                        st.cache_resource.clear()
                    return recommender

                with stage_placeholder.container():
                    render_analysis_stage(
                        "Warming up the matcher",
                        "Getting your music search ready.",
                        0.28,
                    )
                with st.spinner("Getting the music matcher ready..."):
                    recommender = get_recommender()

                if recommender.is_ready:
                    with stage_placeholder.container():
                        render_analysis_stage(
                            "Reading the image",
                            "Catching the color, scene, mood, and energy.",
                            0.58,
                        )
                    spinner_msg = (
                        "Composing your Indian music matches..."
                        if retrieval_options["boost_indian"]
                        else "Composing your music matches..."
                    )
                    with st.spinner(spinner_msg):
                        recommendations = recommender.recommend(
                            image_source,
                            top_k=retrieval_options["top_k"],
                            preferred_language=retrieval_options["preferred_language"],
                            preferred_region=retrieval_options["preferred_region"],
                            prefer_recent=retrieval_options["prefer_recent"],
                            require_preview=retrieval_options["require_preview"],
                            boost_indian=retrieval_options["boost_indian"],
                        )

                    if not recommendations.empty:
                        with stage_placeholder.container():
                            render_analysis_stage(
                                "Arranging the final set",
                                "Balancing fit, freshness, playable previews, and variety.",
                                1.0,
                            )
                        st.session_state["recommendations"] = recommendations
                        st.session_state["show_results"] = True
                        st.session_state["detected_themes"] = getattr(recommender, "last_detected_themes", [])
                        st.session_state["search_context"] = {
                            "query": getattr(recommender, "last_query_text", ""),
                            "candidate_count": getattr(recommender, "last_candidate_count", 0),
                            "mood_confidence": getattr(recommender, "last_mood_confidence", 0.0),
                        }
                        st.session_state["empty_recommendation_error"] = None
                        stage_placeholder.empty()
                    else:
                        stage_placeholder.empty()
                        st.session_state["show_results"] = False
                        st.session_state["empty_recommendation_error"] = {
                            "message": "No tracks survived the current filters.",
                            "suggestions": [
                                "Switch language or region to Any.",
                                "Turn off preview-only mode.",
                                "Try an image with a clearer face, scene, or celebration cue.",
                            ],
                        }
                else:
                    stage_placeholder.empty()
                    logging.error(
                        "Recommendation engine offline. Missing components: %s",
                        ", ".join(recommender.missing_components()),
                    )
                    st.session_state["show_results"] = False
                    st.session_state["empty_recommendation_error"] = {
                        "message": "Recommendation engine offline.",
                        "suggestions": [
                            "A required music search component is missing.",
                            f"Missing components: {', '.join(recommender.missing_components())}",
                        ],
                    }
            except Exception as exc:
                logging.error("Recommender error: %s", exc, exc_info=True)
                st.session_state["show_results"] = False
                st.session_state["empty_recommendation_error"] = {
                    "message": "An error occurred while processing your request.",
                    "suggestions": [
                        "Please try again or use a different image.",
                        str(exc),
                    ],
                }


with col_right:
    render_workspace_section_header(
        "Output desk",
        "Review the set",
        "Matched tracks, context, and previews stay in one focused queue.",
    )

    if st.session_state.get("show_results") and "recommendations" in st.session_state:
        render_results(
            st.session_state["recommendations"],
            st.session_state.get("search_context"),
        )
    elif st.session_state.get("empty_recommendation_error"):
        err = st.session_state["empty_recommendation_error"]
        render_empty_result_guidance(err["message"], err["suggestions"])
    else:
        render_dashboard_welcome()
