"""PictoMusic Sidebar."""

import streamlit as st

from config import APP_TITLE, LANGUAGE_DISPLAY_MAP


REGION_OPTIONS = {
    "Any": "any",
    "Bollywood / Hindi": "bollywood",
    "South Indian": "south_indian",
    "Punjabi": "punjabi",
    "Bengali": "bengali",
    "Marathi": "marathi",
    "Gujarati": "gujarati",
    "Odia": "odia",
    "Northeast Indian": "northeast_indian",
    "Rajasthani": "rajasthani",
    "Bhojpuri": "bhojpuri",
    "Haryanvi": "haryanvi",
}


def _language_options() -> dict[str, str]:
    labels = {"Any": "any"}
    for code, display in LANGUAGE_DISPLAY_MAP.items():
        labels[display] = code
    return labels


def render_sidebar() -> dict:
    """Render the sidebar and return retrieval preferences."""
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
                <div class="brand-mark" aria-hidden="true">PM</div>
                <div class="brand-copy">
                    <div class="brand-title">{APP_TITLE}</div>
                    <div class="brand-subtitle">Music intelligence</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        image_source_option = st.radio(
            "Image source",
            ("Upload Image", "Image URL"),
            label_visibility="visible",
        )

        st.markdown("---")
        st.markdown("**Music Focus**")

        language_labels = _language_options()
        language_label = st.selectbox("Language", list(language_labels.keys()), index=0)
        region_label = st.selectbox("Region", list(REGION_OPTIONS.keys()), index=0)
        prefer_recent = st.toggle("Prioritize newer releases", value=True)
        require_preview = st.toggle("Only songs with audio previews", value=False)
        boost_indian = st.toggle("Prioritize Indian music", value=True)

        top_k = st.slider("Results", min_value=5, max_value=25, value=10, step=5)

        st.markdown("---")

        st.markdown(
            """
            <div class="sidebar-note">
                <div class="sidebar-note-label">Listening profile</div>
                <div class="sidebar-note-copy">
                    Balance language, region, freshness, and playable previews.
                    <br><br>
                    <span>
                        Built for Bollywood, Punjabi, Tamil, Telugu, Bengali, Marathi, Gujarati, Bhojpuri, and more.
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return {
        "image_source_option": image_source_option,
        "preferred_language": language_labels[language_label],
        "language_label": language_label,
        "preferred_region": REGION_OPTIONS[region_label],
        "region_label": region_label,
        "prefer_recent": prefer_recent,
        "require_preview": require_preview,
        "boost_indian": boost_indian,
        "top_k": top_k,
    }
