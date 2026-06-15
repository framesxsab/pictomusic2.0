"""PictoMusic - AI Music Discovery main Streamlit entrypoint."""

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
)
from recommend import ImageMusicRecommender
from security import (
    RateLimiter,
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
    if image_source_option == "Upload Image":
        uploaded_file = st.file_uploader(
            "Drop your image here",
            type=[ext.lstrip(".") for ext in ALLOWED_IMAGE_EXTENSIONS],
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            try:
                validate_uploaded_file(uploaded_file)
                st.image(uploaded_file, use_container_width=True)
                image_source = uploaded_file
            except ValueError as exc:
                st.error(f"Image validation failed: {exc}")

    elif image_source_option == "Image URL":
        image_url = st.text_input(
            "Enter Image URL",
            placeholder="https://example.com/image.jpg",
            label_visibility="collapsed",
        )
        if image_url:
            try:
                validated_url = validate_image_url(image_url)
                st.image(validated_url, use_container_width=True)
                image_source = validated_url
            except ValueError as exc:
                st.error(f"URL validation failed: {exc}")
            except Exception as exc:
                logging.warning("Image URL error: %s", exc)
                st.warning("Could not load image from this URL. Please check the link and try again.")

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
                    recommender = ImageMusicRecommender()
                    if not recommender.is_ready:
                        st.cache_resource.clear()
                    return recommender

                recommender = get_recommender()

                if recommender.is_ready:
                    with st.spinner("Reading the image and ranking Indian music matches..."):
                        recommendations = recommender.recommend(
                            image_source,
                            top_k=retrieval_options["top_k"],
                            preferred_language=retrieval_options["preferred_language"],
                            preferred_region=retrieval_options["preferred_region"],
                            prefer_recent=retrieval_options["prefer_recent"],
                            require_preview=retrieval_options["require_preview"],
                        )

                    if not recommendations.empty:
                        st.session_state["recommendations"] = recommendations
                        st.session_state["show_results"] = True
                        st.session_state["catalog_stats"] = recommender.catalog_stats()
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
    )
