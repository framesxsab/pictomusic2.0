"""PictoMusic - AI Music Discovery main Streamlit entrypoint."""

import io
import logging

import streamlit as st

from log_config import setup_logging

setup_logging()

from config import (
    ALLOWED_IMAGE_EXTENSIONS,
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
    validate_image_content,
    validate_image_url,
    validate_uploaded_file,
)
from ui.components import render_hero_section
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

image_source = None
col_pad_l, col_main, col_pad_r = st.columns([1, 3, 1])

with col_main:
    # Reset cache when switching upload method
    if st.session_state.get("last_image_source_option") != image_source_option:
        st.session_state["last_image_source_option"] = image_source_option
        st.session_state.pop("cached_file_key", None)
        st.session_state.pop("cached_image_bytes", None)
        st.session_state.pop("cached_file_error", None)

    if image_source_option == "Upload Image":
        uploaded_file = st.file_uploader(
            "Drop your image here",
            type=[ext.lstrip(".") for ext in ALLOWED_IMAGE_EXTENSIONS],
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            cache_key = f"{uploaded_file.name}_{uploaded_file.size}"
            if st.session_state.get("cached_file_key") != cache_key:
                try:
                    validate_uploaded_file(uploaded_file)
                    st.session_state["cached_file_key"] = cache_key
                    st.session_state["cached_image_bytes"] = uploaded_file.getvalue()
                    st.session_state["cached_file_error"] = None
                except ValueError as exc:
                    st.session_state["cached_file_key"] = cache_key
                    st.session_state["cached_image_bytes"] = None
                    st.session_state["cached_file_error"] = str(exc)

            if st.session_state.get("cached_file_error"):
                st.error(f"Image validation failed: {st.session_state['cached_file_error']}")
            elif st.session_state.get("cached_image_bytes"):
                st.image(st.session_state["cached_image_bytes"], use_container_width=True)
                image_source = io.BytesIO(st.session_state["cached_image_bytes"])
                image_source.name = uploaded_file.name
        else:
            # Clear cache when file is removed
            st.session_state.pop("cached_file_key", None)
            st.session_state.pop("cached_image_bytes", None)
            st.session_state.pop("cached_file_error", None)

    elif image_source_option == "Image URL":
        if st.button("Use sample image", use_container_width=True):
            st.session_state["image_url_input"] = DEMO_IMAGE_URL

        image_url = st.text_input(
            "Enter Image URL",
            placeholder=DEMO_IMAGE_URL,
            key="image_url_input",
            label_visibility="collapsed",
        )
        if image_url:
            cache_key = f"url_{image_url}"
            if st.session_state.get("cached_file_key") != cache_key:
                try:
                    validated_url = validate_image_url(image_url)
                    import requests
                    response = requests.get(
                        validated_url, stream=True, timeout=REQUEST_TIMEOUT
                    )
                    response.raise_for_status()

                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > MAX_UPLOAD_SIZE_BYTES:
                        raise ValueError(
                            f"Remote image too large ({int(content_length)} bytes)"
                        )

                    downloaded = []
                    downloaded_size = 0
                    for chunk in response.iter_content(chunk_size=HTTP_CHUNK_SIZE):
                        downloaded_size += len(chunk)
                        if downloaded_size > MAX_UPLOAD_SIZE_BYTES:
                            raise ValueError(
                                "Remote image exceeds size limit during download"
                            )
                        downloaded.append(chunk)

                    image_bytes = b"".join(downloaded)
                    validate_image_content(image_bytes)

                    st.session_state["cached_file_key"] = cache_key
                    st.session_state["cached_image_bytes"] = image_bytes
                    st.session_state["cached_file_error"] = None
                except ValueError as exc:
                    st.session_state["cached_file_key"] = cache_key
                    st.session_state["cached_image_bytes"] = None
                    st.session_state["cached_file_error"] = str(exc)
                except Exception as exc:
                    logging.warning("Image URL error: %s", exc)
                    st.session_state["cached_file_key"] = cache_key
                    st.session_state["cached_image_bytes"] = None
                    st.session_state["cached_file_error"] = (
                        "Could not load image from this URL. Please check the link and try again."
                    )

            if st.session_state.get("cached_file_error"):
                st.error(f"URL validation failed: {st.session_state['cached_file_error']}")
            elif st.session_state.get("cached_image_bytes"):
                st.image(st.session_state["cached_image_bytes"], use_container_width=True)
                image_source = io.BytesIO(st.session_state["cached_image_bytes"])
                image_source.name = "url_image.jpg"
        else:
            # Clear cache when URL is empty
            st.session_state.pop("cached_file_key", None)
            st.session_state.pop("cached_image_bytes", None)
            st.session_state.pop("cached_file_error", None)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Analyze image", use_container_width=True):
        if image_source is None:
            st.warning("Please provide an image first.")
        elif not rate_limiter.check():
            wait_time = rate_limiter.seconds_until_available()
            st.warning(
                f"Rate limit reached. Please wait {wait_time:.0f} seconds before trying again."
            )
        else:
            try:
                @st.cache_resource(show_spinner=False)
                def get_recommender():
                    status_placeholder = st.empty()
                    progress_placeholder = st.empty()

                    def progress_cb(current, total):
                        pct = int((current / total) * 100)
                        status_placeholder.text(f"Regenerating CLIP embeddings for {total:,} songs... ({pct}%)")
                        progress_placeholder.progress(current / total)

                    status_placeholder.text("Initializing CLIP model and loading 91K song catalog...")
                    recommender = ImageMusicRecommender(progress_callback=progress_cb)

                    status_placeholder.empty()
                    progress_placeholder.empty()

                    if not recommender.is_ready:
                        st.cache_resource.clear()
                    return recommender

                with st.spinner("Loading recommendation engine and FAISS index..."):
                    recommender = get_recommender()

                if recommender.is_ready:
                    spinner_msg = (
                        "Reading the image and ranking Indian music matches..."
                        if retrieval_options["boost_indian"]
                        else "Reading the image and ranking music matches..."
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
                        st.session_state["recommendations"] = recommendations
                        st.session_state["show_results"] = True
                        st.session_state["catalog_stats"] = recommender.catalog_stats()
                        st.session_state["detected_themes"] = getattr(recommender, "last_detected_themes", [])
                        st.session_state["search_context"] = {
                            "query": getattr(recommender, "last_query_text", ""),
                            "candidate_count": getattr(recommender, "last_candidate_count", 0),
                            "mood_confidence": getattr(recommender, "last_mood_confidence", 0.0),
                        }
                    else:
                        st.info(
                            "No matching tracks found with these filters. "
                            "Try Any language/region or disable preview-only mode."
                        )
                else:
                    st.error(
                        "Recommendation engine offline. Missing: "
                        + ", ".join(recommender.missing_components())
                    )
            except Exception as exc:
                logging.error("Recommender error: %s", exc, exc_info=True)
                st.error(
                    "An error occurred while processing your request. "
                    "Please try again or use a different image."
                )


if st.session_state.get("show_results") and "recommendations" in st.session_state:
    render_results(
        st.session_state["recommendations"],
        st.session_state.get("catalog_stats"),
        st.session_state.get("search_context"),
    )
