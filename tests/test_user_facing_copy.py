"""Checks for misleading hardcoded user-facing workflow copy."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

USER_FACING_FILES = [
    PROJECT_ROOT / "src" / "app.py",
    PROJECT_ROOT / "src" / "config.py",
    PROJECT_ROOT / "src" / "ui" / "components.py",
    PROJECT_ROOT / "src" / "ui" / "results.py",
    PROJECT_ROOT / "src" / "ui" / "sidebar.py",
]

INTERACTIVE_UI_FILES = [
    PROJECT_ROOT / "src" / "app.py",
    PROJECT_ROOT / "src" / "ui" / "components.py",
    PROJECT_ROOT / "src" / "ui" / "results.py",
    PROJECT_ROOT / "src" / "ui" / "sidebar.py",
]


def test_user_facing_copy_does_not_claim_neural_only_workflow():
    banned_phrases = [
        "Neural Recommendations",
        "Neural Match",
        "Neural engine",
    ]

    for path in USER_FACING_FILES:
        text = path.read_text(encoding="utf-8")
        for phrase in banned_phrases:
            assert phrase not in text, f"{phrase!r} found in {path}"


def test_streamlit_app_does_not_inject_ignored_csp_meta_tag():
    text = (PROJECT_ROOT / "src" / "app.py").read_text(encoding="utf-8")

    assert "inject_csp_headers" not in text


def test_user_facing_copy_stays_india_first():
    banned_phrases = [
        "Global Retrieval",
        "World Retrieval",
        "global moods",
        "Global charts",
    ]

    for path in USER_FACING_FILES:
        text = path.read_text(encoding="utf-8")
        for phrase in banned_phrases:
            assert phrase not in text, f"{phrase!r} found in {path}"


def test_user_facing_copy_has_no_mojibake_markers():
    mojibake_markers = ["ð", "â", "Ã", "�"]

    for path in USER_FACING_FILES:
        text = path.read_text(encoding="utf-8")
        for marker in mojibake_markers:
            assert marker not in text, f"mojibake marker {marker!r} found in {path}"


def test_user_facing_copy_does_not_show_fake_image_url_placeholder():
    for path in USER_FACING_FILES:
        text = path.read_text(encoding="utf-8")
        assert "example.com/image" not in text, f"fake image URL placeholder found in {path}"


def test_interactive_ui_does_not_expose_stack_in_loader_copy():
    banned_phrases = [
        "Loading CLIP",
        "FAISS index",
        "91K-song catalog",
        "Initializing CLIP",
    ]

    for path in INTERACTIVE_UI_FILES:
        text = path.read_text(encoding="utf-8")
        for phrase in banned_phrases:
            assert phrase not in text, f"{phrase!r} found in {path}"


def test_failure_guidance_does_not_expose_internal_runtime_details():
    app_text = (PROJECT_ROOT / "src" / "app.py").read_text(encoding="utf-8")

    assert 'f"Missing components:' not in app_text
    assert '"suggestions": [\n                        "Please try again or use a different image.",\n                        str(exc),' not in app_text


def test_hugging_face_deployment_enforces_embedding_manifest_validation():
    docker_text = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")
    verifier_text = (PROJECT_ROOT / "scripts" / "verify_hf_deployment.py").read_text(encoding="utf-8")

    assert "PICTOMUSIC_STRICT_EMBEDDING_MANIFEST=1" in docker_text
    assert "Dockerfile must enforce strict embedding manifest validation" in verifier_text


def test_results_page_does_not_render_catalog_summary():
    text = (PROJECT_ROOT / "src" / "ui" / "results.py").read_text(encoding="utf-8")

    assert "render_catalog_health" not in text
    assert '"Catalog"' not in text


def test_results_styles_reserve_stable_layout_space():
    text = (PROJECT_ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")

    assert "scrollbar-gutter: stable" in text
    assert '[data-testid="stAudio"]' in text
    assert ".element-container:has(audio)" in text
    assert ".song-player-container" in text
    assert "min-height: 32px;" in text


def test_desktop_content_canvas_is_centered_without_changing_mobile_width():
    style_text = (PROJECT_ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")

    assert ".block-container" in style_text
    assert "max-width: 1280px !important;" in style_text
    assert "margin-left: auto !important;" in style_text
    assert "margin-right: auto !important;" in style_text


def test_styles_do_not_reference_removed_accent_tokens():
    style_text = (PROJECT_ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")
    results_text = (PROJECT_ROOT / "src" / "ui" / "results.py").read_text(encoding="utf-8")

    assert "accent-warm" not in style_text
    assert "accent-warm" not in results_text


def test_app_uses_bitcount_single_as_only_declared_font_family():
    config_text = (PROJECT_ROOT / "src" / "config.py").read_text(encoding="utf-8")
    style_text = (PROJECT_ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")

    assert "Bitcount+Single" in config_text
    assert "--font-ui: 'Bitcount Single', 'Courier New', monospace;" in style_text
    assert "*::before" in style_text
    assert "*::after" in style_text
    for removed_font in ["Plus Jakarta", "Outfit", "JetBrains"]:
        assert removed_font not in config_text
        assert removed_font not in style_text


def test_instructional_step_ui_is_not_rendered():
    app_text = (PROJECT_ROOT / "src" / "app.py").read_text(encoding="utf-8")
    component_text = (PROJECT_ROOT / "src" / "ui" / "components.py").read_text(encoding="utf-8")
    style_text = (PROJECT_ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")

    for removed_marker in ["render_workflow_ribbon", "workflow-ribbon", "deck-step", "step-num"]:
        assert removed_marker not in app_text
        assert removed_marker not in component_text
        assert removed_marker not in style_text


def test_mobile_upload_has_gallery_type_filter_and_camera_path():
    app_text = (PROJECT_ROOT / "src" / "app.py").read_text(encoding="utf-8")

    assert "st.camera_input" in app_text
    assert '("Gallery", "Camera")' in app_text
    assert 'type=["jpg", "jpeg", "png", "webp", "heic", "heif"]' in app_text
    assert "accept_multiple_files=False" in app_text


def test_sidebar_controls_are_visible_by_default():
    app_text = (PROJECT_ROOT / "src" / "app.py").read_text(encoding="utf-8")
    sidebar_text = (PROJECT_ROOT / "src" / "ui" / "sidebar.py").read_text(encoding="utf-8")

    assert 'initial_sidebar_state="auto"' in app_text
    assert 'initial_sidebar_state="collapsed"' not in app_text
    for control in [
        "Image source",
        "Language",
        "Region",
        "Prioritize newer releases",
        "Only songs with audio previews",
        "Prioritize Indian music",
        "Results",
    ]:
        assert control in sidebar_text


def test_file_upload_dropzone_text_cannot_overlap_button():
    style_text = (PROJECT_ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")

    assert '[data-testid="stFileUploadDropzone"]' in style_text
    assert '[data-testid="stFileUploaderDropzone"]' in style_text
    assert '[data-testid="stFileUploaderDropzoneInstructions"]' in style_text
    assert "flex-direction: column !important;" in style_text
    assert "align-items: center !important;" in style_text
    assert "min-height: 136px !important;" in style_text
    assert "white-space: normal !important;" in style_text
    assert "overflow-wrap: anywhere !important;" in style_text
    assert "min-height: 2.7rem !important;" in style_text
    assert '[data-testid="stIconMaterial"]' in style_text
    assert 'button span:first-child:not(:last-child)' in style_text
    assert "width: 156px !important;" in style_text
    assert "gap: 0 !important;" in style_text
    assert "white-space: nowrap !important;" in style_text
    assert '[data-testid="stFileUploaderFile"]' in style_text
    assert '[data-testid="stFileUploader"] button[kind="secondary"]' not in style_text
    assert '[data-testid="stBaseButton-secondary"] {' not in style_text
    assert '[data-testid="stBaseButton-secondary"]:hover' not in style_text


def test_selected_gallery_upload_uses_app_preview_and_clear_button():
    app_text = (PROJECT_ROOT / "src" / "app.py").read_text(encoding="utf-8")

    assert "def _hide_native_gallery_uploader" in app_text
    assert "def _reset_upload_widget" in app_text
    assert 'key=f"gallery_upload_{st.session_state[\'gallery_upload_nonce\']}"' in app_text
    assert 'key=f"camera_upload_{st.session_state[\'camera_upload_nonce\']}"' in app_text
    assert 'st.button("Clear image"' in app_text
    assert "_reset_upload_widget(upload_method)" in app_text


def test_streamlit_button_labels_do_not_wrap_mid_word():
    style_text = (PROJECT_ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")

    assert ".stButton > button p" in style_text
    assert "word-break: keep-all !important;" in style_text
    assert "overflow-wrap: normal !important;" in style_text
    assert "font-size: 0.78rem !important;" in style_text


def test_upload_method_selector_is_equal_width_on_mobile():
    style_text = (PROJECT_ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")

    assert '.stRadio [role="radiogroup"]' in style_text
    assert "grid-template-columns: repeat(2, minmax(0, 1fr)) !important;" in style_text
    assert "min-height: 2.75rem !important;" in style_text
    assert "margin-bottom: 0.85rem !important;" in style_text


def test_sidebar_can_render_direct_app_link_for_browser_wrapper_fallback():
    sidebar_text = (PROJECT_ROOT / "src" / "ui" / "sidebar.py").read_text(encoding="utf-8")
    config_text = (PROJECT_ROOT / "src" / "config.py").read_text(encoding="utf-8")
    docker_text = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "PICTOMUSIC_PUBLIC_APP_URL" in config_text
    assert "PUBLIC_APP_URL" in sidebar_text
    assert "Open direct app" in sidebar_text
    assert "rel=\"noopener noreferrer\"" in sidebar_text
    assert 'f"""' not in sidebar_text
    assert "            </div>" not in sidebar_text
    assert "https://fxsab-pictomusicu.hf.space" in docker_text


def test_styles_use_gold_silver_palette_tokens():
    style_text = (PROJECT_ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")

    assert "#cfd6e2" in style_text
    assert "#f1d27a" in style_text
    assert "#b8924f" in style_text
    for removed_token in ["#5f7cff", "#35d8ff", "#c77dff", "#ffd166"]:
        assert removed_token not in style_text


def test_card_surfaces_do_not_render_decorative_stripes():
    style_text = (PROJECT_ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")

    striped_card_selectors = [
        ".image-ready-panel::before",
        ".retrieval-summary::before",
        ".search-context-panel::before",
        ".detected-themes-panel::before",
        ".stat-card::before",
        ".song-card::before",
    ]

    for selector in striped_card_selectors:
        assert selector not in style_text


def test_mobile_styles_keep_subtle_glass_surfaces():
    style_text = (PROJECT_ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")

    assert "--glass-blur: 14px;" in style_text
    assert "backdrop-filter: none" not in style_text
    assert "-webkit-backdrop-filter: none" not in style_text
    assert "backdrop-filter: blur(8px) saturate(1.06) !important;" in style_text
