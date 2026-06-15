"""Checks for misleading hardcoded user-facing workflow copy."""

from pathlib import Path


USER_FACING_FILES = [
    Path("src/app.py"),
    Path("src/ui/components.py"),
    Path("src/ui/results.py"),
    Path("src/ui/sidebar.py"),
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
    text = Path("src/app.py").read_text(encoding="utf-8")

    assert "inject_csp_headers" not in text
