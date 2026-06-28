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


def test_results_page_does_not_render_catalog_summary():
    text = (PROJECT_ROOT / "src" / "ui" / "results.py").read_text(encoding="utf-8")

    assert "render_catalog_health" not in text
    assert '"Catalog"' not in text


def test_results_styles_reserve_stable_layout_space():
    text = (PROJECT_ROOT / "src" / "ui" / "styles.py").read_text(encoding="utf-8")

    assert "scrollbar-gutter: stable" in text
    assert '[data-testid="stAudio"]' in text
    assert ".element-container:has(audio)" in text


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
