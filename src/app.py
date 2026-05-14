"""
PictoMusic — AI Music Discovery
Main Streamlit entrypoint.
"""

import logging
import streamlit as st

from config import (
    ALLOWED_IMAGE_EXTENSIONS,
    APP_ICON,
    APP_SUBTITLE,
    APP_TITLE,
    APP_VERSION_TAG,
)
from security import (
    RateLimiter,
    escape_html,
    inject_csp_headers,
    validate_image_url,
    validate_uploaded_file,
)
from recommend import ImageMusicRecommender
from ui.styles import get_global_css
from ui.components import render_hero_section
from ui.sidebar import render_sidebar
from ui.results import render_results

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Page Config ---
st.set_page_config(
    page_title=f"{APP_TITLE} — AI Music Discovery",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS & Security Headers ---
st.markdown(get_global_css(), unsafe_allow_html=True)
inject_csp_headers()

# --- Rate Limiter ---
rate_limiter = RateLimiter()

# --- Sidebar ---
image_source_option = render_sidebar()

# --- Hero Section ---
render_hero_section(APP_VERSION_TAG, APP_SUBTITLE)

# --- Image Input ---
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
            except ValueError as ve:
                st.error(f"Image validation failed: {ve}")

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
            except ValueError as ve:
                st.error(f"URL validation failed: {ve}")
            except Exception as e:
                st.warning(f"Could not load image. Error: {escape_html(str(e))}")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Analyze Button ---
    if st.button("\u26a1  ANALYZE & DISCOVER", use_container_width=True):
        if image_source is not None:
            # Rate limit check
            if not rate_limiter.check():
                wait_time = rate_limiter.seconds_until_available()
                st.warning(
                    f"Rate limit reached. Please wait {wait_time:.0f} seconds before trying again."
                )
            else:
                try:
                    @st.cache_resource(show_spinner=False)
                    def get_recommender():
                        return ImageMusicRecommender()

                    recommender = get_recommender()

                    if recommender.is_ready:
                        with st.spinner("Neural engine analyzing visual frequencies..."):
                            recommendations = recommender.recommend(image_source)

                        if not recommendations.empty:
                            st.session_state["recommendations"] = recommendations
                            st.session_state["show_results"] = True
                        else:
                            st.info("No matching frequencies found. Try a different image.")
                    else:
                        st.error(
                            "Neural engine offline. Missing: "
                            + ", ".join(recommender.missing_components())
                        )
                except Exception as e:
                    logging.error("Recommender error: %s", e)
                    st.error(
                        "An error occurred while processing your request. "
                        "Please try again or use a different image."
                    )
        else:
            st.warning("Please provide an image first.")


# --- Results ---
if st.session_state.get("show_results") and "recommendations" in st.session_state:
    render_results(st.session_state["recommendations"])
