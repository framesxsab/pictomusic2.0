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
