"""PictoMusic Global CSS."""

from config import GOOGLE_FONTS_URL


def get_global_css() -> str:
    return """
<style>
@import url('__GOOGLE_FONTS_URL__');

:root {
    --primary: #f4b642;
    --primary-dim: rgba(244, 182, 66, 0.14);
    --accent-warm: #f4b642;
    --accent-green: #54d39b;
    --accent-rose: #ee6f8f;
    --accent-blue: #6db7ff;
    --bg-dark: #0a0f0d;
    --bg-card: rgba(255, 249, 235, 0.045);
    --panel-soft: rgba(244, 182, 66, 0.055);
    --border-glow: rgba(244, 182, 66, 0.18);
    --surface-top: rgba(255, 249, 235, 0.072);
    --surface-mid: rgba(255, 249, 235, 0.032);
    --surface-low: rgba(7, 12, 10, 0.78);
    --surface-border: rgba(255, 249, 235, 0.14);
    --text-primary: #fff9eb;
    --text-secondary: #c5bdab;
    --text-muted: #aaa08c;
    --glass-bg: linear-gradient(180deg, var(--surface-top) 0%, var(--surface-mid) 44%, var(--surface-low) 100%);
    --glass-border: var(--surface-border);
}

html, body, [data-testid="stAppViewContainer"], .stApp,
[data-testid="stHeader"], [data-testid="stToolbar"] {
    background:
        linear-gradient(180deg, rgba(244, 182, 66, 0.16) 0%, rgba(244, 182, 66, 0.055) 11rem, rgba(10, 15, 13, 0) 29rem),
        linear-gradient(115deg, rgba(84, 211, 155, 0.07) 0%, rgba(84, 211, 155, 0.025) 24%, transparent 44%),
        linear-gradient(245deg, rgba(238, 111, 143, 0.055) 0%, rgba(238, 111, 143, 0.02) 26%, transparent 46%),
        var(--bg-dark) !important;
    color: var(--text-primary) !important;
    font-family: 'Anek Devanagari', sans-serif !important;
}

html {
    overflow-y: scroll;
    scrollbar-gutter: stable;
}

body, [data-testid="stAppViewContainer"], .stApp {
    scrollbar-gutter: stable;
}

#MainMenu, header[data-testid="stHeader"], footer,
[data-testid="stToolbar"], .stDeployButton {
    display: none !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #121613 0%, #0b0f0e 100%) !important;
    border-right: 1px solid var(--border-glow) !important;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown span,
section[data-testid="stSidebar"] .stMarkdown li {
    color: var(--text-secondary) !important;
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] small {
    color: var(--text-secondary) !important;
}

section[data-testid="stSidebar"] .stRadio label {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
}

section[data-testid="stSidebar"] .stRadio label:hover {
    color: var(--text-primary) !important;
}

.brand-mark {
    width: 42px;
    height: 42px;
    background: linear-gradient(135deg, rgba(244, 182, 66, 0.95), rgba(238, 111, 143, 0.85));
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 12px 30px rgba(244, 182, 66, 0.22);
    font-size: 1.3rem;
}

/* Glassmorphism cards */
.glass-card {
    background: var(--glass-bg);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--glass-border);
    border-radius: 0.75rem;
    padding: 2rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
}

.glass-card:hover {
    border-color: var(--border-glow);
    box-shadow: 0 18px 50px rgba(0, 0, 0, 0.22);
}

/* Hero title */
.hero-title {
    font-size: clamp(2.5rem, 6vw, 4.5rem);
    font-family: 'Fraunces', serif;
    font-weight: 800;
    letter-spacing: 0;
    line-height: 1.02;
    background: linear-gradient(135deg, #fff6dc 0%, #f4b642 48%, #54d39b 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin: 0;
    padding: 0.5rem 0;
}

.hero-subtitle {
    text-align: center;
    color: var(--text-secondary);
    font-size: 1.15rem;
    font-weight: 500;
    margin-top: 0.5rem;
    letter-spacing: 0.01em;
}

.version-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 1rem;
    background: var(--primary-dim);
    border: 1px solid var(--border-glow);
    border-radius: 9999px;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--accent-warm);
    margin: 0 auto;
}

.version-badge::before {
    content: '';
    width: 6px;
    height: 6px;
    background: var(--accent-green);
    border-radius: 50%;
    animation: pulse-dot 2s infinite;
}

@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.8); }
}

/* Song card */
.song-card {
    background:
        linear-gradient(180deg, rgba(255, 249, 235, 0.058) 0%, rgba(255, 249, 235, 0.028) 48%, rgba(7, 12, 10, 0.76) 100%),
        linear-gradient(90deg, rgba(244, 182, 66, 0.034), rgba(84, 211, 155, 0.026) 42%, rgba(238, 111, 143, 0.022));
    backdrop-filter: blur(12px);
    border: 1px solid var(--surface-border);
    border-radius: 0.75rem;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
    position: relative;
    overflow: hidden;
    display: flex;
    gap: 1.25rem;
    align-items: center;
    box-shadow:
        inset 0 1px 0 rgba(255, 249, 235, 0.07),
        0 18px 44px rgba(0, 0, 0, 0.18);
}

.song-art-container {
    flex-shrink: 0;
    width: 90px;
    height: 90px;
    border-radius: 0.5rem;
    overflow: hidden;
    border: 1px solid var(--glass-border);
    background: rgba(255, 255, 255, 0.05);
    display: flex;
    align-items: center;
    justify-content: center;
}

.song-art {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.song-card:hover .song-art {
    transform: none;
}

.song-art-placeholder {
    font-size: 2rem;
    color: var(--text-muted);
}

.song-details {
    flex: 1;
    min-width: 0;
}

.song-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 1.25rem;
    right: 1.25rem;
    height: 2px;
    background: linear-gradient(90deg, rgba(244, 182, 66, 0.78), rgba(84, 211, 155, 0.5), rgba(238, 111, 143, 0.38));
    border-radius: 9999px;
    opacity: 0.54;
    transition: opacity 0.3s ease;
}

.song-card:hover {
    border-color: rgba(255, 249, 235, 0.2);
    box-shadow:
        inset 0 1px 0 rgba(255, 249, 235, 0.1),
        0 18px 48px rgba(0, 0, 0, 0.28);
}

.song-card:hover::before {
    opacity: 1;
}

.song-rank {
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--accent-warm);
    margin-bottom: 0.25rem;
}

.song-name {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    letter-spacing: 0;
}

.song-artist {
    font-size: 0.85rem;
    color: var(--text-secondary);
    font-weight: 500;
    margin-top: 0.15rem;
}

.song-meta {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.35rem;
    flex-wrap: wrap;
}

.song-tag {
    display: inline-flex;
    padding: 0.15rem 0.5rem;
    background: rgba(255, 249, 235, 0.055);
    border: 1px solid rgba(255, 249, 235, 0.12);
    border-radius: 9999px;
    font-size: 0.6rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* Match score bar */
.score-container {
    margin-top: 0.75rem;
}

.score-label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.35rem;
}

.score-text {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--text-muted);
}

.score-value {
    font-size: 0.78rem;
    font-weight: 800;
    color: var(--accent-warm);
}

.match-reasons {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin: 0.25rem 0 0.45rem;
}

.match-reason {
    display: inline-flex;
    align-items: center;
    border: 1px solid rgba(84, 211, 155, 0.18);
    background: rgba(84, 211, 155, 0.07);
    border-radius: 9999px;
    padding: 0.12rem 0.46rem;
    font-size: 0.68rem;
    color: var(--text-secondary);
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.score-bar-bg {
    width: 100%;
    height: 6px;
    background: rgba(255, 249, 235, 0.09);
    border-radius: 9999px;
    overflow: hidden;
}

.score-bar-fill {
    height: 100%;
    border-radius: 9999px;
    background: linear-gradient(90deg, var(--accent-green), var(--accent-warm), var(--accent-rose));
    box-shadow: 0 0 12px rgba(244, 182, 66, 0.35);
    transition: none;
}

/* Section headers */
.section-header {
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: 0;
    margin-bottom: 0.25rem;
}

.section-accent {
    color: var(--accent-warm);
}

/* Upload area */
.intake-shell {
    background:
        linear-gradient(180deg, rgba(255, 249, 235, 0.062), rgba(255, 249, 235, 0.026)),
        linear-gradient(90deg, rgba(84, 211, 155, 0.045), rgba(244, 182, 66, 0.045));
    border: 1px solid var(--surface-border);
    border-radius: 0.75rem;
    padding: 1rem 1.1rem;
    margin-bottom: 0.85rem;
    box-shadow: inset 0 1px 0 rgba(255, 249, 235, 0.08);
}

.intake-eyebrow,
.retrieval-summary-label,
.analysis-stage-label,
.image-ready-kicker {
    font-size: 0.62rem;
    font-weight: 850;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--accent-warm);
}

.intake-title {
    color: var(--text-primary);
    font-size: 1.15rem;
    font-weight: 850;
    margin-top: 0.18rem;
}

.intake-hint {
    color: var(--text-secondary);
    font-size: 0.86rem;
    line-height: 1.45;
    margin-top: 0.25rem;
}

[data-testid="stFileUploader"],
[data-testid="stFileUploader"] > *,
[data-testid="stFileUploader"] > div,
[data-testid="stFileUploader"] section,
[data-testid="stFileUploader"] section > *,
[data-testid="stFileUploader"] section > div,
[data-testid="stFileUploader"] section > div > div {
    background: transparent !important;
    background-color: transparent !important;
    color: var(--text-secondary) !important;
    border-color: transparent !important;
    border: none !important;
}

[data-testid="stFileUploadDropzone"],
[data-testid="stFileUploadDropzone"] > * {
    background: var(--bg-card) !important;
    background-color: var(--bg-card) !important;
    color: var(--text-secondary) !important;
    border-color: var(--border-glow) !important;
}

[data-testid="stFileUploader"] {
    border-radius: 0.75rem !important;
    overflow: hidden !important;
}

[data-testid="stFileUploadDropzone"] {
    border: 2px dashed var(--border-glow) !important;
    border-radius: 0.75rem !important;
    transition: all 0.3s ease !important;
    background:
        linear-gradient(135deg, rgba(244, 182, 66, 0.08), rgba(84, 211, 155, 0.045)) !important;
    background-color: rgba(244, 182, 66, 0.05) !important;
    padding: 2.5rem 1.5rem !important;
}

[data-testid="stFileUploadDropzone"]:hover {
    border-color: var(--primary) !important;
    box-shadow: 0 0 24px rgba(244, 182, 66, 0.16) !important;
    background-color: rgba(244, 182, 66, 0.08) !important;
}

[data-testid="stFileUploadDropzone"] > div:first-child > div:first-child > span {
    font-size: 0 !important;
}

[data-testid="stFileUploadDropzone"] > div:first-child > div:first-child > span::after {
    content: 'Drop an image or browse' !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: var(--text-secondary) !important;
    letter-spacing: 0.01em !important;
}

[data-testid="stFileUploadDropzone"] > div:first-child > div:first-child > small {
    font-size: 0 !important;
}

[data-testid="stFileUploadDropzone"] > div:first-child > div:first-child > small::after {
    content: 'JPG, PNG, WEBP - Max 10 MB' !important;
    font-size: 0.7rem !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
}

[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploadDropzone"] span,
[data-testid="stFileUploadDropzone"] small,
[data-testid="stFileUploadDropzone"] p,
[data-testid="stFileUploadDropzone"] div {
    color: var(--text-secondary) !important;
}

[data-testid="stFileUploadDropzone"] button,
[data-testid="stFileUploader"] button[kind="secondary"],
[data-testid="stBaseButton-secondary"] {
    background: var(--primary-dim) !important;
    background-color: var(--primary-dim) !important;
    color: var(--primary) !important;
    border: 1px solid var(--border-glow) !important;
    border-radius: 0.75rem !important;
    font-weight: 600 !important;
}

[data-testid="stBaseButton-secondary"]:hover {
    background-color: rgba(244, 182, 66, 0.18) !important;
    border-color: var(--primary) !important;
}

.image-ready-panel,
.retrieval-summary,
.analysis-stage,
.empty-guidance {
    background:
        linear-gradient(180deg, rgba(255, 249, 235, 0.06), rgba(255, 249, 235, 0.026)),
        rgba(8, 12, 10, 0.72);
    border: 1px solid var(--surface-border);
    border-radius: 0.75rem;
    padding: 1rem;
    margin-top: 0.85rem;
    box-shadow:
        inset 0 1px 0 rgba(255, 249, 235, 0.08),
        0 14px 34px rgba(0, 0, 0, 0.16);
}

.image-ready-panel {
    position: relative;
    overflow: hidden;
}

.image-ready-panel::before {
    content: '';
    position: absolute;
    inset: 0 auto 0 0;
    width: 3px;
    background: linear-gradient(180deg, var(--accent-green), var(--accent-warm));
}

.image-ready-title,
.retrieval-summary-title,
.empty-guidance-title {
    color: var(--text-primary);
    font-weight: 800;
    font-size: 1rem;
    margin-top: 0.15rem;
}

.image-ready-meta,
.retrieval-summary-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-top: 0.7rem;
}

.image-ready-meta span,
.summary-chip {
    display: inline-flex;
    align-items: center;
    border: 1px solid rgba(255, 249, 235, 0.12);
    background: rgba(255, 249, 235, 0.055);
    color: var(--text-secondary);
    border-radius: 9999px;
    padding: 0.26rem 0.62rem;
    font-size: 0.68rem;
    font-weight: 700;
}

.ready-hint {
    color: var(--text-muted);
    font-size: 0.8rem;
    text-align: center;
    margin-top: -0.15rem;
}

.analysis-stage {
    margin-bottom: 0.9rem;
    position: relative;
    overflow: hidden;
}

.analysis-stage::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent, rgba(244, 182, 66, 0.045), transparent);
    transform: translateX(-100%);
    animation: loader-sweep 2.4s ease-in-out infinite;
}

.analysis-loader {
    position: relative;
    display: flex;
    align-items: center;
    gap: 0.8rem;
    z-index: 1;
}

.analysis-disc {
    width: 46px;
    height: 46px;
    border-radius: 50%;
    border: 1px solid rgba(255, 249, 235, 0.16);
    background:
        radial-gradient(circle at center, #0a0f0d 0 14%, rgba(244, 182, 66, 0.9) 15% 18%, transparent 19%),
        conic-gradient(from 0deg, rgba(244, 182, 66, 0.95), rgba(84, 211, 155, 0.8), rgba(238, 111, 143, 0.7), rgba(244, 182, 66, 0.95));
    box-shadow: 0 0 24px rgba(244, 182, 66, 0.18);
    animation: loader-spin 1.8s linear infinite;
    flex: 0 0 auto;
}

.analysis-disc span {
    display: none;
}

.analysis-bars {
    display: flex;
    align-items: end;
    gap: 0.22rem;
    height: 34px;
}

.analysis-bars span {
    width: 5px;
    min-height: 8px;
    border-radius: 9999px;
    background: linear-gradient(180deg, var(--accent-green), var(--accent-warm));
    animation: loader-bar 1s ease-in-out infinite;
    opacity: 0.86;
}

.analysis-bars span:nth-child(2) { animation-delay: 0.12s; }
.analysis-bars span:nth-child(3) { animation-delay: 0.24s; }
.analysis-bars span:nth-child(4) { animation-delay: 0.36s; }
.analysis-bars span:nth-child(5) { animation-delay: 0.48s; }

.analysis-stage-copy {
    position: relative;
    z-index: 1;
    margin-top: 0.75rem;
}

.analysis-stage-detail {
    color: var(--text-secondary);
    font-size: 0.88rem;
    line-height: 1.45;
    margin-top: 0.25rem;
}

.analysis-stage-track {
    position: relative;
    z-index: 1;
    height: 7px;
    width: 100%;
    border-radius: 9999px;
    overflow: hidden;
    background: rgba(255, 249, 235, 0.08);
    margin-top: 0.85rem;
}

.analysis-stage-fill {
    height: 100%;
    border-radius: 9999px;
    background: linear-gradient(90deg, var(--accent-green), var(--accent-warm), var(--accent-rose));
    box-shadow: 0 0 18px rgba(244, 182, 66, 0.28);
    transition: width 0.5s ease;
}

@keyframes loader-spin {
    to { transform: rotate(360deg); }
}

@keyframes loader-bar {
    0%, 100% { height: 9px; }
    50% { height: 32px; }
}

@keyframes loader-sweep {
    0% { transform: translateX(-100%); }
    45%, 100% { transform: translateX(100%); }
}

.empty-guidance {
    border-color: rgba(238, 111, 143, 0.32);
}

.empty-guidance ul {
    margin: 0.65rem 0 0;
    padding-left: 1.1rem;
    color: var(--text-secondary);
}

.empty-guidance li {
    margin: 0.18rem 0;
}

/* Text input */
.stTextInput input {
    background: var(--bg-card) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 0.5rem !important;
    color: var(--text-primary) !important;
    font-family: 'Anek Devanagari', sans-serif !important;
    transition: all 0.3s ease !important;
}

.stTextInput input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(244, 182, 66, 0.16) !important;
}

.stTextInput label {
    color: var(--text-secondary) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #f4b642, #d05f73) !important;
    color: #160f0a !important;
    border: none !important;
    border-radius: 0.5rem !important;
    font-family: 'Anek Devanagari', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.75rem 2rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 12px 30px rgba(244, 182, 66, 0.24) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 18px 42px rgba(244, 182, 66, 0.32) !important;
}

.stButton > button:active {
    transform: translateY(0) scale(0.98) !important;
}

/* Radio buttons */
.stRadio > div {
    background: transparent !important;
    gap: 0.35rem !important;
}

.stRadio > label {
    display: none !important;
}

.stRadio [role="radiogroup"] {
    gap: 0.35rem !important;
}

.stRadio [role="radiogroup"] label {
    background: rgba(255, 249, 235, 0.045) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 0.5rem !important;
    padding: 0.6rem 1rem !important;
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    cursor: pointer !important;
    transition: all 0.25s ease !important;
    margin: 0 !important;
}

.stRadio [role="radiogroup"] label:hover {
    background: rgba(244, 182, 66, 0.1) !important;
    border-color: var(--border-glow) !important;
    color: var(--text-primary) !important;
}

.stRadio [role="radiogroup"] label[data-checked="true"],
.stRadio [role="radiogroup"] label:has(input:checked) {
    background: var(--primary-dim) !important;
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    box-shadow: 0 0 12px rgba(244, 182, 66, 0.16) !important;
}

.stRadio [role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] [data-testid="stTickBarMin"],
section[data-testid="stSidebar"] [data-testid="stTickBarMax"] {
    color: var(--text-secondary) !important;
    opacity: 1 !important;
}

section[data-testid="stSidebar"] [data-testid="stThumbValue"] {
    color: var(--accent-warm) !important;
}

/* Spinner */
.stSpinner > div {
    border-top-color: var(--primary) !important;
}

/* Image display */
[data-testid="stImage"] {
    border-radius: 0.75rem;
    overflow: hidden;
    border: 1px solid var(--glass-border);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

/* Audio player */
[data-testid="stAudio"],
.element-container:has(audio) {
    min-height: 48px;
    margin-bottom: 0.75rem;
}

audio {
    width: 100%;
    height: 40px;
    border-radius: 0.5rem;
    filter: hue-rotate(240deg) saturate(1.5);
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-track {
    background: var(--bg-dark);
}
::-webkit-scrollbar-thumb {
    background: var(--primary);
    border-radius: 9999px;
}
::-webkit-scrollbar-thumb:hover {
    background: var(--accent-green);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    gap: 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 0.75rem !important;
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 1.25rem !important;
}

.stTabs [aria-selected="true"] {
    background: var(--primary-dim) !important;
    border-color: var(--border-glow) !important;
    color: var(--primary) !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    background: var(--primary) !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 0.75rem !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

hr {
    border-color: var(--glass-border) !important;
}

/* Stats row */
.stat-card {
    background:
        linear-gradient(180deg, rgba(255, 249, 235, 0.06) 0%, rgba(255, 249, 235, 0.03) 46%, rgba(8, 12, 10, 0.78) 100%),
        linear-gradient(90deg, rgba(244, 182, 66, 0.024), rgba(84, 211, 155, 0.02), rgba(238, 111, 143, 0.018));
    backdrop-filter: blur(12px);
    border: 1px solid var(--surface-border);
    border-radius: 0.75rem;
    padding: 1.25rem 1.5rem;
    text-align: left;
    position: relative;
    overflow: hidden;
    box-shadow:
        inset 0 1px 0 rgba(255, 249, 235, 0.07),
        0 16px 36px rgba(0, 0, 0, 0.16);
}

.stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 1rem;
    right: 1rem;
    height: 2px;
    background: linear-gradient(90deg, var(--stat-accent, var(--primary)), rgba(255, 249, 235, 0.1));
    border-radius: 9999px;
    opacity: 0.82;
}

.stat-label {
    font-size: 0.6rem;
    font-weight: 800;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.35rem;
}

.stat-value {
    display: inline-flex;
    align-items: baseline;
    gap: 0.35rem;
    flex-wrap: wrap;
    font-size: 1.75rem;
    font-weight: 900;
    color: var(--text-primary);
}

.stat-unit {
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--primary);
}

/* Preview unavailable */
.no-preview {
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--glass-border);
    border-radius: 9999px;
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 500;
    flex-wrap: wrap;
}

.no-preview a {
    text-decoration: none;
    font-weight: 600;
    transition: opacity 0.2s;
}

.no-preview a:hover {
    opacity: 0.8;
}

/* Hero glow */
.hero-glow {
    position: relative;
}

.hero-glow::before {
    content: '';
    position: absolute;
    top: -100px;
    left: 50%;
    transform: translateX(-50%);
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(244, 182, 66, 0.12) 0%, transparent 70%);
    pointer-events: none;
    z-index: -1;
}

/* Mobile optimizations */
@media (max-width: 768px) {
    .glass-card, .song-card, .stat-card {
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        box-shadow: none !important;
    }
    .hero-glow::before {
        display: none !important;
    }
    .score-bar-fill {
        box-shadow: none !important;
    }
    audio {
        filter: none !important;
    }
    .image-ready-meta,
    .retrieval-summary-chips {
        gap: 0.35rem;
    }
    .image-ready-meta span,
    .summary-chip {
        font-size: 0.64rem;
    }
    .intake-shell,
    .image-ready-panel,
    .retrieval-summary,
    .analysis-stage,
    .empty-guidance {
        padding: 0.85rem;
    }
}

@media (prefers-reduced-motion: reduce) {
    .analysis-stage::before,
    .analysis-disc,
    .analysis-bars span,
    .score-bar-fill,
    .version-badge::before {
        animation: none !important;
    }
}
</style>
""".replace("__GOOGLE_FONTS_URL__", GOOGLE_FONTS_URL)
