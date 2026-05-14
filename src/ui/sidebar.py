"""
PictoMusic Sidebar
"""

import streamlit as st


def render_sidebar() -> str:
    """Render the sidebar and return the selected image source option."""
    with st.sidebar:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 2rem;">
                <div style="width: 42px; height: 42px; background: linear-gradient(135deg, #4f06f9, #6d28d9);
                            border-radius: 12px; display: flex; align-items: center; justify-content: center;
                            box-shadow: 0 0 20px rgba(79,6,249,0.4); font-size: 1.3rem;">
                    \U0001f3b5
                </div>
                <div>
                    <div style="font-size: 1.2rem; font-weight: 800; color: #f0eef5; letter-spacing: -0.02em;">
                        Pictomusic
                    </div>
                    <div style="font-size: 0.6rem; font-weight: 700; color: #4f06f9;
                                letter-spacing: 0.2em; text-transform: uppercase;">
                        AI Audio
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

        st.markdown(
            """
            <div style="background: rgba(79,6,249,0.08); border: 1px solid rgba(79,6,249,0.2);
                        border-radius: 1rem; padding: 1rem; margin-top: 1rem;">
                <div style="font-size: 0.6rem; font-weight: 700; color: #5a5670;
                            letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 0.5rem;">
                    Neural Engine
                </div>
                <div style="font-size: 0.8rem; color: #8a85a0; line-height: 1.5;">
                    Powered by <span style="color: #4f06f9; font-weight: 700;">CLIP</span> vision-language
                    model + <span style="color: #4f06f9; font-weight: 700;">FAISS</span> similarity search
                    <br><br>
                    <span style="font-size: 0.7rem; color: #5a5670;">
                        \U0001f30f Indian music: Bollywood, Punjabi, Tamil, Telugu, Bengali + more
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return image_source_option
