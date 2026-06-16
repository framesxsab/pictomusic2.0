"""PictoMusic Sidebar."""

import streamlit as st

from config import APP_ICON, APP_TITLE, LANGUAGE_DISPLAY_MAP


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
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 2rem;">
                <div class="brand-mark">
                    {APP_ICON}
                </div>
                <div>
                    <div style="font-size: 1.2rem; font-weight: 800; color: var(--text-primary); letter-spacing: -0.02em;">
                        {APP_TITLE}
                    </div>
                    <div style="font-size: 0.6rem; font-weight: 700; color: var(--accent-warm);
                                letter-spacing: 0.2em; text-transform: uppercase;">
                        Global Retrieval
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        image_source_option = st.radio(
            "\U0001f5bc\ufe0f Image Source",
            ("Upload Image", "Image URL"),
            label_visibility="visible",
        )

        st.markdown("---")
        st.markdown("**Retrieval Focus**")

        language_labels = _language_options()
        language_label = st.selectbox("Language", list(language_labels.keys()), index=0)
        region_label = st.selectbox("Region", list(REGION_OPTIONS.keys()), index=0)
        prefer_recent = st.toggle("Prioritize newer releases", value=True)
        require_preview = st.toggle("Only songs with audio previews", value=False)
        boost_indian = st.toggle("Prioritize Indian music", value=False)

        top_k = st.slider("Results", min_value=5, max_value=25, value=10, step=5)

        st.markdown("---")

        st.markdown(
            """
            <div style="background: var(--panel-soft); border: 1px solid var(--glass-border);
                        border-radius: 1rem; padding: 1rem; margin-top: 1rem;">
                <div style="font-size: 0.6rem; font-weight: 700; color: var(--text-muted);
                            letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 0.5rem;">
                    Retrieval Stack
                </div>
                <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5;">
                    <span style="color: var(--accent-warm); font-weight: 800;">CLIP</span> visual vectors,
                    <span style="color: var(--accent-green); font-weight: 800;">FAISS</span> candidate search,
                    and hybrid ranking for global language, region, recency, and playable previews.
                    <br><br>
                    <span style="font-size: 0.7rem; color: var(--text-muted);">
                        Global charts, Pop, Rock, Hip-Hop, Bollywood, Punjabi, Tamil, Telugu and more.
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return {
        "image_source_option": image_source_option,
        "preferred_language": language_labels[language_label],
        "preferred_region": REGION_OPTIONS[region_label],
        "prefer_recent": prefer_recent,
        "require_preview": require_preview,
        "boost_indian": boost_indian,
        "top_k": top_k,
    }
