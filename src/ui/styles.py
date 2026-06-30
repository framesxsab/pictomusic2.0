"""PictoMusic Global CSS."""

from config import GOOGLE_FONTS_URL


def get_global_css() -> str:
    return """
<style>
@import url('__GOOGLE_FONTS_URL__');

:root {
    --font-ui: 'Bitcount Single', 'Courier New', monospace;
    --primary: #cfd6e2;
    --primary-dim: rgba(207, 214, 226, 0.16);
    --accent-fuchsia: #f1d27a;
    --accent-cyan: #d9e0ea;
    --accent-amber: #b8924f;
    --accent-green: #8ce6bd;
    --accent-rose: #b98068;
    --bg-dark: #070708;
    --bg-rail: #0d0e11;
    --bg-panel: rgba(18, 19, 23, 0.9);
    --bg-card: rgba(29, 30, 35, 0.8);
    --panel-soft: rgba(207, 214, 226, 0.12);
    --surface-top: rgba(255, 255, 255, 0.12);
    --surface-mid: rgba(241, 210, 122, 0.056);
    --surface-low: rgba(7, 7, 8, 0.9);
    --surface-border: rgba(217, 224, 234, 0.22);
    --glass-border: rgba(241, 210, 122, 0.22);
    --border-glow: rgba(241, 210, 122, 0.32);
    --text-primary: #f7f7f4;
    --text-secondary: #d8dbe0;
    --text-muted: #9ba2ab;
    --shadow-soft: 0 30px 90px rgba(0, 0, 0, 0.46);
    --glass-blur: 14px;
    --glass-shadow-quiet: inset 0 1px 0 rgba(255, 255, 255, 0.11), 0 18px 48px rgba(0, 0, 0, 0.28);
    --glass-bg:
        linear-gradient(180deg, var(--surface-top), var(--surface-mid) 46%, var(--surface-low));
}

html {
    overflow-y: scroll;
    scrollbar-gutter: stable;
}

html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stHeader"], [data-testid="stToolbar"] {
    background:
        linear-gradient(180deg, rgba(217, 224, 234, 0.16) 0, rgba(7, 7, 8, 0.0) 18rem),
        linear-gradient(120deg, rgba(241, 210, 122, 0.14) 0, rgba(241, 210, 122, 0.034) 25%, transparent 47%),
        linear-gradient(248deg, rgba(184, 146, 79, 0.12) 0, rgba(184, 146, 79, 0.028) 28%, transparent 50%),
        linear-gradient(180deg, #101116 0, #070708 42rem) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-ui) !important;
}

body, [data-testid="stAppViewContainer"], .stApp {
    scrollbar-gutter: stable;
}

*,
*::before,
*::after,
button,
input,
textarea,
select,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] * {
    font-family: var(--font-ui) !important;
    font-synthesis: none;
}

#MainMenu, footer, [data-testid="stToolbar"], .stDeployButton, [data-testid="stConnectionStatus"] {
    display: none !important;
}

header[data-testid="stHeader"] {
    background-color: transparent !important;
    background: transparent !important;
    height: 3.75rem !important;
}

.block-container {
    max-width: 1280px !important;
    padding-top: 1.6rem !important;
    padding-bottom: 4rem !important;
}

section[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(22, 23, 28, 0.98), rgba(7, 7, 8, 0.99)),
        linear-gradient(135deg, rgba(241, 210, 122, 0.07), transparent 45%) !important;
    border-right: 1px solid rgba(217, 224, 234, 0.18) !important;
}

section[data-testid="stSidebar"] > div {
    padding-top: 1.35rem !important;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown span,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] small {
    color: var(--text-secondary) !important;
}

.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 0.78rem;
    margin: 0 0 1.2rem;
}

.brand-mark {
    width: 42px;
    height: 42px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    background:
        linear-gradient(135deg, var(--accent-cyan), var(--accent-fuchsia) 58%, var(--accent-amber));
    color: #070708;
    font-family: var(--font-ui);
    font-weight: 700;
    font-size: 0.83rem;
    box-shadow: 0 16px 38px rgba(241, 210, 122, 0.2), 0 0 22px rgba(217, 224, 234, 0.14);
}

.brand-title {
    font-family: var(--font-ui);
    font-size: 1.08rem;
    font-weight: 700;
    color: var(--text-primary);
}

.brand-subtitle,
.sidebar-note-label,
.intake-eyebrow,
.retrieval-summary-label,
.analysis-stage-label,
.image-ready-kicker,
.console-kicker,
.hero-status,
.version-badge,
.stat-label,
.song-rank,
.detected-themes-label {
    font-family: var(--font-ui);
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.brand-subtitle {
    color: var(--accent-cyan);
    margin-top: 0.1rem;
}

.sidebar-note {
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0.035));
    border: 1px solid var(--surface-border);
    border-radius: 8px;
    padding: 1rem;
    margin-top: 1rem;
    box-shadow: var(--glass-shadow-quiet);
    backdrop-filter: blur(10px) saturate(1.08);
    -webkit-backdrop-filter: blur(10px) saturate(1.08);
}

.sidebar-note-label {
    color: var(--accent-amber);
    margin-bottom: 0.5rem;
}

.sidebar-note-copy {
    color: var(--text-secondary);
    font-size: 0.82rem;
    line-height: 1.55;
}

.sidebar-note-copy span {
    color: var(--text-muted) !important;
    font-size: 0.74rem;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(217, 224, 234, 0.14) !important;
}

[data-baseweb="select"] > div {
    background: rgba(255, 255, 255, 0.07) !important;
    border: 1px solid rgba(217, 224, 234, 0.22) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    box-shadow: none !important;
}

[data-baseweb="select"] [role="combobox"],
[data-baseweb="select"] input,
[data-baseweb="select"] div {
    color: var(--text-primary) !important;
    font-family: var(--font-ui) !important;
}

[data-baseweb="select"] svg {
    color: var(--accent-cyan) !important;
    fill: var(--accent-cyan) !important;
}

[data-baseweb="radio"] > div:first-child,
[data-baseweb="checkbox"] > div:first-child {
    border-color: rgba(217, 224, 234, 0.28) !important;
    background: rgba(255, 255, 255, 0.09) !important;
}

[data-baseweb="radio"]:has(input:checked) > div:first-child,
[data-baseweb="checkbox"]:has(input:checked) > div:first-child {
    border-color: var(--accent-cyan) !important;
    background: linear-gradient(135deg, var(--accent-cyan), var(--primary) 48%, var(--accent-fuchsia)) !important;
    box-shadow: 0 0 20px rgba(241, 210, 122, 0.28) !important;
}

[data-baseweb="radio"]:has(input:checked) > div:first-child > div,
[data-baseweb="checkbox"]:has(input:checked) > div:first-child > div {
    background: #f6f7ff !important;
}

[data-testid="stCheckbox"] [data-testid="stWidgetLabel"] p {
    color: var(--text-secondary) !important;
    font-weight: 700 !important;
}

[data-baseweb="slider"] [role="slider"] {
    background: var(--accent-cyan) !important;
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 18px rgba(241, 210, 122, 0.34) !important;
}

[data-baseweb="slider"] div {
    color: var(--text-secondary) !important;
}

[data-baseweb="slider"] > div > div:first-child {
    background-image:
        linear-gradient(
            to right,
            var(--accent-cyan) 0%,
            var(--accent-cyan) 25%,
            rgba(217, 224, 234, 0.2) 25%,
            rgba(217, 224, 234, 0.2) 100%
        ) !important;
}

[data-testid="stCameraInputWebcamComponent"] > div,
[data-testid="stCameraInputWebcamStyledBox"] {
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.09), rgba(255, 255, 255, 0.04)),
        rgba(14, 18, 33, 0.92) !important;
    border: 1px solid rgba(217, 224, 234, 0.2) !important;
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
}

[data-testid="stCameraInput"] svg,
[data-testid="stCameraInput"] path {
    color: var(--text-muted) !important;
    fill: var(--text-muted) !important;
    stroke: var(--text-muted) !important;
}

[data-testid="stCameraInput"] a {
    color: var(--accent-cyan) !important;
}

[data-testid="stCameraInputButton"] {
    background: rgba(207, 214, 226, 0.16) !important;
    border: 1px solid rgba(217, 224, 234, 0.24) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}

.studio-hero {
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(217, 224, 234, 0.18);
    border-radius: 8px;
    padding: 1.15rem 1.2rem 1rem;
    margin: 0 0 1.3rem;
    background:
        linear-gradient(180deg, rgba(30, 36, 64, 0.84), rgba(8, 10, 18, 0.93)),
        linear-gradient(112deg, rgba(241, 210, 122, 0.15), transparent 35%),
        linear-gradient(146deg, rgba(185, 128, 104, 0.1), transparent 52%),
        linear-gradient(252deg, rgba(217, 224, 234, 0.12), transparent 47%);
    box-shadow: var(--shadow-soft), inset 0 1px 0 rgba(255, 255, 255, 0.09);
    backdrop-filter: blur(var(--glass-blur)) saturate(1.12);
    -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(1.12);
}

.studio-hero::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.024) 1px, transparent 1px);
    background-size: 56px 56px;
    mask-image: linear-gradient(180deg, black, transparent 82%);
    pointer-events: none;
}

.hero-topline,
.hero-grid,
.hero-meter {
    position: relative;
    z-index: 1;
}

.hero-topline {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.9rem;
}

.version-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.52rem;
    padding: 0.46rem 0.72rem;
    background: rgba(6, 7, 13, 0.58);
    border: 1px solid rgba(241, 210, 122, 0.3);
    border-radius: 8px;
    color: var(--accent-cyan);
}

.version-badge::before,
.hero-status::before {
    content: '';
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--accent-green);
    box-shadow: 0 0 12px rgba(62, 230, 168, 0.62);
}

.hero-status {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-secondary);
}

.hero-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.08fr) minmax(300px, 0.78fr);
    gap: 1.4rem;
    align-items: center;
}

.hero-title {
    font-family: var(--font-ui);
    font-size: clamp(2.35rem, 4.4vw, 3.85rem);
    line-height: 1;
    font-weight: 700;
    letter-spacing: 0;
    color: var(--text-primary);
    margin: 0;
    max-width: 560px;
}

.hero-title br {
    display: block;
}

.hero-subtitle {
    max-width: 520px;
    color: var(--text-secondary);
    font-size: 0.96rem;
    line-height: 1.55;
    font-weight: 500;
    margin: 0.72rem 0 0;
}

.hero-console {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.8rem;
}

.console-card {
    min-height: 98px;
    border: 1px solid rgba(217, 224, 234, 0.18);
    border-radius: 8px;
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.035)),
        linear-gradient(135deg, rgba(241, 210, 122, 0.07), transparent 52%);
    padding: 0.9rem;
    box-shadow: var(--glass-shadow-quiet);
    backdrop-filter: blur(10px) saturate(1.1);
    -webkit-backdrop-filter: blur(10px) saturate(1.1);
}

.console-card-primary {
    grid-column: span 2;
    min-height: 118px;
}

.console-kicker {
    color: var(--text-muted);
}

.console-title {
    margin-top: 0.36rem;
    color: var(--text-primary);
    font-family: var(--font-ui);
    font-size: 1.02rem;
    font-weight: 700;
}

.console-wave,
.hero-meter {
    display: flex;
    align-items: center;
    gap: 0.32rem;
}

.console-wave {
    height: 34px;
    margin-top: 0.92rem;
}

.console-wave span,
.hero-meter span {
    display: block;
    width: 100%;
    border-radius: 999px;
    background: linear-gradient(180deg, var(--accent-cyan), var(--primary) 55%, var(--accent-fuchsia));
}

.console-wave span {
    max-width: 16px;
    min-width: 7px;
    height: 16px;
    opacity: 0.62;
}

.console-wave span:nth-child(2),
.console-wave span:nth-child(7) { height: 26px; }
.console-wave span:nth-child(3),
.console-wave span:nth-child(9) { height: 11px; }
.console-wave span:nth-child(4),
.console-wave span:nth-child(8) { height: 31px; }
.console-wave span:nth-child(5) { height: 19px; background: linear-gradient(180deg, var(--accent-amber), var(--accent-rose)); }

.hero-meter {
    height: 18px;
    margin-top: 1rem;
}

.hero-meter span {
    flex: 1;
    height: 3px;
    opacity: 0.38;
}

.hero-meter span:nth-child(3n) {
    background: var(--accent-amber);
    opacity: 0.62;
}

.workspace-header {
    border: 1px solid rgba(217, 224, 234, 0.18);
    border-radius: 8px;
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.09), rgba(255, 255, 255, 0.035)),
        linear-gradient(120deg, rgba(241, 210, 122, 0.065), transparent 54%);
    padding: 0.95rem 1rem;
    margin: 0 0 0.82rem;
    box-shadow: var(--glass-shadow-quiet);
    backdrop-filter: blur(10px) saturate(1.1);
    -webkit-backdrop-filter: blur(10px) saturate(1.1);
}

.workspace-eyebrow {
    font-family: var(--font-ui);
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--accent-cyan);
}

.workspace-title {
    margin-top: 0.28rem;
    color: var(--text-primary);
    font-family: var(--font-ui);
    font-size: 1.04rem;
    font-weight: 800;
}

.workspace-detail {
    margin-top: 0.25rem;
    color: var(--text-secondary);
    font-size: 0.82rem;
    line-height: 1.45;
}

.glass-card,
.intake-shell,
.image-ready-panel,
.retrieval-summary,
.analysis-stage,
.empty-guidance,
.search-context-panel,
.detected-themes-panel,
.stat-card,
.song-card {
    background: var(--glass-bg);
    border: 1px solid var(--surface-border);
    border-radius: 8px;
    box-shadow: var(--glass-shadow-quiet);
    backdrop-filter: blur(var(--glass-blur)) saturate(1.1);
    -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(1.1);
}

.glass-card {
    padding: 1.4rem;
    margin-bottom: 1rem;
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
}

.glass-card:hover,
.song-card:hover {
    border-color: rgba(241, 210, 122, 0.42);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12), 0 28px 76px rgba(0, 0, 0, 0.38);
}

.intake-shell {
    padding: 1rem 1.1rem;
    margin-bottom: 0.85rem;
}

.intake-eyebrow,
.retrieval-summary-label,
.analysis-stage-label,
.image-ready-kicker {
    color: var(--accent-cyan);
}

.intake-title,
.image-ready-title,
.retrieval-summary-title,
.empty-guidance-title {
    color: var(--text-primary);
    font-family: var(--font-ui);
    font-size: 1.08rem;
    font-weight: 700;
    margin-top: 0.2rem;
}

.intake-hint,
.analysis-stage-detail,
.search-context-query {
    color: var(--text-secondary);
    font-size: 0.9rem;
    line-height: 1.55;
    margin-top: 0.35rem;
}

[data-testid="stFileUploader"],
[data-testid="stCameraInput"],
[data-testid="stFileUploader"] > *,
[data-testid="stCameraInput"] > *,
[data-testid="stFileUploader"] > div,
[data-testid="stCameraInput"] > div,
[data-testid="stFileUploader"] section,
[data-testid="stFileUploaderDropzone"],
[data-testid="stCameraInput"] section,
[data-testid="stFileUploader"] section > *,
[data-testid="stFileUploaderDropzone"] > *,
[data-testid="stCameraInput"] section > *,
[data-testid="stFileUploader"] section > div,
[data-testid="stFileUploaderDropzone"] > div,
[data-testid="stCameraInput"] section > div,
[data-testid="stFileUploader"] section > div > div {
    background: transparent !important;
    background-color: transparent !important;
    color: var(--text-secondary) !important;
    border-color: transparent !important;
    border: none !important;
}

[data-testid="stFileUploader"] {
    border-radius: 8px !important;
    overflow: hidden !important;
}

[data-testid="stCameraInput"] {
    margin-top: 0.85rem !important;
}

[data-testid="stFileUploadDropzone"],
[data-testid="stFileUploaderDropzone"],
[data-testid="stCameraInput"] [data-testid="stFileUploadDropzone"],
[data-testid="stCameraInput"] [data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploaderDropzone"] > *,
[data-testid="stFileUploadDropzone"] > * {
    background:
        linear-gradient(135deg, rgba(217, 224, 234, 0.18), rgba(241, 210, 122, 0.11) 54%, rgba(185, 128, 104, 0.055)) !important;
    background-color: rgba(14, 18, 33, 0.88) !important;
    color: var(--text-secondary) !important;
    border-color: var(--border-glow) !important;
}

[data-testid="stFileUploadDropzone"],
[data-testid="stFileUploaderDropzone"] {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0.9rem !important;
    border: 1px dashed rgba(241, 210, 122, 0.52) !important;
    border-radius: 8px !important;
    padding: 1.35rem 1.25rem !important;
    min-height: 136px !important;
    box-shadow: var(--glass-shadow-quiet) !important;
    backdrop-filter: blur(10px) saturate(1.08) !important;
    -webkit-backdrop-filter: blur(10px) saturate(1.08) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

[data-testid="stFileUploadDropzone"] > div,
[data-testid="stFileUploadDropzone"] > div > div,
[data-testid="stFileUploaderDropzone"] > span,
[data-testid="stFileUploaderDropzoneInstructions"] {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    gap: 0.42rem !important;
    width: 100% !important;
    min-width: 0 !important;
}

[data-testid="stFileUploadDropzone"]:hover,
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 30px rgba(241, 210, 122, 0.24) !important;
}

[data-testid="stFileUploadDropzone"] > div:first-child > div:first-child > span {
    font-size: 0 !important;
    display: block !important;
    max-width: 100% !important;
    line-height: 1.35 !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}

[data-testid="stFileUploadDropzone"] > div:first-child > div:first-child > span::after {
    content: 'Drop an image or browse' !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
}

[data-testid="stFileUploadDropzone"] > div:first-child > div:first-child > small {
    font-size: 0 !important;
    display: block !important;
    max-width: 100% !important;
    line-height: 1.4 !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}

[data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] div {
    display: block !important;
    max-width: 100% !important;
    line-height: 1.4 !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    text-align: center !important;
}

[data-testid="stFileUploaderDropzone"] [data-testid="stIconMaterial"],
[data-testid="stFileUploadDropzone"] [data-testid="stIconMaterial"],
[data-testid="stFileUploaderDropzone"] button span[aria-hidden="true"],
[data-testid="stFileUploadDropzone"] button span[aria-hidden="true"],
[data-testid="stFileUploaderDropzone"] button span[class*="Icon"],
[data-testid="stFileUploadDropzone"] button span[class*="Icon"],
[data-testid="stFileUploaderDropzone"] button span:first-child:not(:last-child),
[data-testid="stFileUploadDropzone"] button span:first-child:not(:last-child) {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    min-width: 0 !important;
    max-width: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}

[data-testid="stFileUploadDropzone"] > div:first-child > div:first-child > small::after {
    content: 'JPG, PNG, WEBP, HEIC - Max 10 MB' !important;
    font-size: 0.72rem !important;
    color: var(--text-muted) !important;
    font-weight: 600 !important;
}

[data-testid="stFileUploader"] label,
[data-testid="stCameraInput"] label,
[data-testid="stFileUploader"] p,
[data-testid="stCameraInput"] p,
[data-testid="stFileUploader"] span,
[data-testid="stCameraInput"] span,
[data-testid="stFileUploader"] small,
[data-testid="stCameraInput"] small,
[data-testid="stFileUploadDropzone"] span,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploadDropzone"] small,
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploadDropzone"] p,
[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploadDropzone"] div,
[data-testid="stFileUploaderDropzone"] div {
    color: var(--text-secondary) !important;
}

[data-testid="stFileUploadDropzone"] button,
[data-testid="stFileUploaderDropzone"] button {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex: 0 0 auto !important;
    width: 156px !important;
    max-width: 100% !important;
    min-height: 2.7rem !important;
    padding: 0.72rem 1.15rem !important;
    gap: 0 !important;
    white-space: normal !important;
    line-height: 1.15 !important;
    text-align: center !important;
    background: rgba(207, 214, 226, 0.18) !important;
    background-color: rgba(207, 214, 226, 0.18) !important;
    color: var(--text-primary) !important;
    border: 1px solid rgba(217, 224, 234, 0.28) !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
}

[data-testid="stFileUploaderDropzone"] button p,
[data-testid="stFileUploadDropzone"] button p,
[data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"],
[data-testid="stFileUploadDropzone"] button [data-testid="stMarkdownContainer"] {
    margin: 0 !important;
    color: var(--text-primary) !important;
    text-align: center !important;
    white-space: nowrap !important;
}

[data-testid="stFileUploadDropzone"] button:hover,
[data-testid="stFileUploaderDropzone"] button:hover {
    background-color: rgba(241, 210, 122, 0.22) !important;
    border-color: var(--accent-cyan) !important;
}

[data-testid="stFileUploaderFile"] {
    display: none !important;
}

.image-ready-panel,
.retrieval-summary,
.analysis-stage,
.empty-guidance,
.search-context-panel,
.detected-themes-panel {
    padding: 1rem;
    margin-top: 0.85rem;
    position: relative;
    overflow: hidden;
}

.image-ready-meta,
.retrieval-summary-chips,
.song-meta,
.match-reasons,
.detected-theme-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
}

.image-ready-meta,
.retrieval-summary-chips {
    margin-top: 0.72rem;
}

.image-ready-meta span,
.summary-chip,
.song-tag,
.match-reason,
.detected-theme-chip {
    display: inline-flex;
    align-items: center;
    border: 1px solid rgba(217, 224, 234, 0.18);
    background: rgba(255, 255, 255, 0.07);
    color: var(--text-secondary);
    border-radius: 999px;
    padding: 0.27rem 0.62rem;
    font-size: 0.68rem;
    font-weight: 700;
}

.ready-hint {
    color: var(--text-muted);
    font-size: 0.82rem;
    text-align: center;
    margin-top: -0.1rem;
}

.analysis-stage {
    margin-bottom: 0.9rem;
}

.analysis-stage::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent, rgba(217, 224, 234, 0.1), rgba(241, 210, 122, 0.12), transparent);
    transform: translateX(-100%);
    animation: loader-sweep 2.4s ease-in-out infinite;
}

.analysis-loader,
.analysis-stage-copy,
.analysis-stage-track {
    position: relative;
    z-index: 1;
}

.analysis-loader {
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.analysis-disc {
    width: 46px;
    height: 46px;
    border-radius: 50%;
    border: 1px solid rgba(217, 224, 234, 0.26);
    background:
        radial-gradient(circle at center, #06070d 0 14%, rgba(251, 252, 255, 0.96) 15% 17%, transparent 18%),
        conic-gradient(from 0deg, var(--accent-cyan), var(--accent-fuchsia), var(--accent-amber), var(--accent-cyan));
    box-shadow: 0 0 28px rgba(241, 210, 122, 0.28);
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
    border-radius: 999px;
    background: linear-gradient(180deg, var(--accent-cyan), var(--primary), var(--accent-fuchsia));
    animation: loader-bar 1s ease-in-out infinite;
    opacity: 0.88;
}

.analysis-bars span:nth-child(2) { animation-delay: 0.12s; }
.analysis-bars span:nth-child(3) { animation-delay: 0.24s; }
.analysis-bars span:nth-child(4) { animation-delay: 0.36s; }
.analysis-bars span:nth-child(5) { animation-delay: 0.48s; }

.analysis-stage-copy {
    margin-top: 0.75rem;
}

.analysis-stage-track {
    height: 7px;
    width: 100%;
    border-radius: 999px;
    overflow: hidden;
    background: rgba(217, 224, 234, 0.14);
    margin-top: 0.85rem;
}

.analysis-stage-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--accent-cyan), var(--primary), var(--accent-fuchsia), var(--accent-amber));
    box-shadow: 0 0 20px rgba(241, 210, 122, 0.32);
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
    border-color: rgba(255, 111, 159, 0.32);
}

.empty-guidance ul {
    margin: 0.65rem 0 0;
    padding-left: 1.1rem;
    color: var(--text-secondary);
}

.empty-guidance li {
    margin: 0.18rem 0;
}

.stTextInput input {
    background: rgba(6, 7, 13, 0.62) !important;
    border: 1px solid rgba(217, 224, 234, 0.24) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-family: var(--font-ui) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

.stTextInput input:focus {
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 0 3px rgba(241, 210, 122, 0.18) !important;
}

.stTextInput label {
    color: var(--text-secondary) !important;
}

.stButton > button {
    width: 100% !important;
    min-width: 0 !important;
    background: linear-gradient(135deg, var(--accent-cyan), var(--primary) 45%, var(--accent-fuchsia) 78%, var(--accent-amber)) !important;
    color: #05070d !important;
    border: 0 !important;
    border-radius: 8px !important;
    font-family: var(--font-ui) !important;
    font-weight: 800 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.78rem 2rem !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    box-shadow: 0 18px 42px rgba(241, 210, 122, 0.24), 0 0 22px rgba(217, 224, 234, 0.16) !important;
}

.stButton > button p,
.stButton > button [data-testid="stMarkdownContainer"] {
    margin: 0 !important;
    white-space: nowrap !important;
    overflow-wrap: normal !important;
    word-break: keep-all !important;
    text-align: center !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 22px 56px rgba(241, 210, 122, 0.28), 0 0 28px rgba(217, 224, 234, 0.2) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

.stButton > button:disabled {
    background: rgba(217, 224, 234, 0.13) !important;
    color: rgba(251, 252, 255, 0.42) !important;
    box-shadow: none !important;
}

.stRadio > div {
    background: transparent !important;
    gap: 0.35rem !important;
}

.stRadio [data-baseweb="radio"] > div:first-child {
    display: none !important;
}

.stRadio > label {
    display: none !important;
}

.stRadio [role="radiogroup"] {
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    gap: 0.65rem !important;
    width: 100% !important;
    margin-bottom: 0.85rem !important;
}

.stRadio [role="radiogroup"] label {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-width: 0 !important;
    min-height: 2.75rem !important;
    background: rgba(255, 255, 255, 0.055) !important;
    border: 1px solid rgba(217, 224, 234, 0.16) !important;
    border-radius: 8px !important;
    padding: 0.66rem 0.85rem !important;
    color: var(--text-secondary) !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    cursor: pointer !important;
    transition: background 0.2s ease, border-color 0.2s ease !important;
    margin: 0 !important;
}

.stRadio [role="radiogroup"] label:hover {
    background: rgba(241, 210, 122, 0.11) !important;
    border-color: rgba(241, 210, 122, 0.32) !important;
    color: var(--text-primary) !important;
}

.stRadio [role="radiogroup"] label[data-checked="true"],
.stRadio [role="radiogroup"] label:has(input:checked) {
    background: rgba(207, 214, 226, 0.18) !important;
    border-color: var(--accent-cyan) !important;
    color: var(--text-primary) !important;
    box-shadow: 0 0 16px rgba(241, 210, 122, 0.18) !important;
}

.stRadio [role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    white-space: nowrap !important;
}

section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] [data-testid="stTickBarMin"],
section[data-testid="stSidebar"] [data-testid="stTickBarMax"] {
    color: var(--text-secondary) !important;
    opacity: 1 !important;
}

section[data-testid="stSidebar"] [data-testid="stThumbValue"] {
    color: var(--accent-cyan) !important;
}

.stSpinner > div {
    border-top-color: var(--accent-cyan) !important;
}

[data-testid="stImage"] {
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--surface-border);
    box-shadow: var(--shadow-soft);
}

[data-testid="stImage"] img {
    max-height: 430px;
    object-fit: contain;
}

[data-testid="stAudio"],
.element-container:has(audio) {
    min-height: 48px;
    margin-bottom: 0.75rem;
}

audio {
    width: 100%;
    height: 40px;
    border-radius: 8px;
    filter: hue-rotate(232deg) saturate(1.7);
}

.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    gap: 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(255, 255, 255, 0.065) !important;
    border: 1px solid rgba(217, 224, 234, 0.18) !important;
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 1.25rem !important;
}

.stTabs [aria-selected="true"] {
    background: rgba(207, 214, 226, 0.18) !important;
    border-color: var(--accent-cyan) !important;
    color: var(--text-primary) !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    background: var(--accent-cyan) !important;
}

.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.065) !important;
    border: 1px solid var(--surface-border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-weight: 700 !important;
}

hr {
    border-color: rgba(217, 224, 234, 0.16) !important;
}

.stat-card {
    padding: 1.15rem 1.25rem;
    text-align: left;
    position: relative;
    overflow: hidden;
}

.stat-label {
    color: var(--text-muted);
    margin-bottom: 0.4rem;
}

.stat-value {
    display: inline-flex;
    align-items: baseline;
    gap: 0.35rem;
    flex-wrap: wrap;
    font-family: var(--font-ui);
    font-size: 1.55rem;
    line-height: 1.08;
    font-weight: 700;
    color: var(--text-primary);
}

.stat-unit {
    font-size: 0.82rem;
    font-weight: 800;
    color: var(--accent-cyan);
}

.section-header {
    font-family: var(--font-ui);
    font-size: 1.55rem;
    line-height: 1.15;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: 0;
    margin-bottom: 0.3rem;
}

.section-accent {
    color: var(--accent-cyan);
}

.section-subtitle {
    color: var(--text-muted);
    font-size: 0.88rem;
    margin-bottom: 1.4rem;
}

.detected-themes-panel {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    flex-wrap: wrap;
    margin-bottom: 1.4rem;
}

.detected-themes-label {
    color: var(--text-muted);
    flex: 0 0 auto;
}

.song-card {
    padding: 1.05rem;
    margin-bottom: 0.8rem;
    position: relative;
    overflow: hidden;
    display: grid;
    grid-template-columns: 92px minmax(0, 1fr);
    gap: 1.05rem;
    align-items: center;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.song-art-container {
    width: 92px;
    height: 92px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid rgba(217, 224, 234, 0.22);
    background: rgba(255, 255, 255, 0.07);
    display: flex;
    align-items: center;
    justify-content: center;
}

.song-art {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.song-art-placeholder {
    font-size: 2rem;
    color: var(--text-muted);
}

.song-details {
    min-width: 0;
}

.song-rank {
    color: var(--accent-cyan);
    margin-bottom: 0.25rem;
}

.song-name {
    font-family: var(--font-ui);
    font-size: 1.08rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
}

.song-artist {
    font-size: 0.86rem;
    color: var(--text-secondary);
    font-weight: 600;
    margin-top: 0.14rem;
}

.song-meta {
    margin-top: 0.44rem;
}

.song-tag {
    font-size: 0.62rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.score-container {
    margin-top: 0.78rem;
}

.score-label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.36rem;
}

.score-text {
    font-family: var(--font-ui);
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--text-muted);
}

.score-value {
    font-size: 0.8rem;
    font-weight: 800;
    color: var(--accent-amber);
}

.match-reasons {
    margin: 0.22rem 0 0.48rem;
}

.match-reason {
    border-color: rgba(62, 230, 168, 0.24);
    background: rgba(62, 230, 168, 0.095);
    font-size: 0.64rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.score-bar-bg {
    width: 100%;
    height: 6px;
    background: rgba(217, 224, 234, 0.14);
    border-radius: 999px;
    overflow: hidden;
}

.score-bar-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--accent-cyan), var(--primary), var(--accent-fuchsia), var(--accent-amber));
    box-shadow: 0 0 16px rgba(241, 210, 122, 0.3);
    transition: none;
}

.no-preview {
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.5rem 0.85rem;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid var(--surface-border);
    border-radius: 999px;
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 700;
    flex-wrap: wrap;
}

.no-preview a {
    text-decoration: none;
    font-weight: 800;
    transition: opacity 0.2s;
}

.no-preview a:hover {
    opacity: 0.8;
}

::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-dark);
}

::-webkit-scrollbar-thumb {
    background: rgba(241, 210, 122, 0.62);
    border-radius: 999px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--accent-fuchsia);
}

@media (max-width: 900px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    .hero-grid {
        grid-template-columns: 1fr;
    }

    .hero-console {
        grid-template-columns: 1fr;
    }

    .console-card-primary {
        grid-column: span 1;
    }

    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 1.5rem !important;
    }

    [data-testid="column"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 100% !important;
    }
}

@media (max-width: 768px) {
    .studio-hero {
        padding: 1rem;
    }

    .hero-topline {
        align-items: flex-start;
        flex-direction: column;
        margin-bottom: 1rem;
    }

    .hero-title {
        font-size: clamp(2.15rem, 14vw, 3.65rem);
    }

    .hero-subtitle {
        font-size: 0.94rem;
    }

    .studio-hero,
    .console-card,
    .workspace-header,
    .glass-card,
    .intake-shell,
    .image-ready-panel,
    .retrieval-summary,
    .analysis-stage,
    .empty-guidance,
    .search-context-panel,
    .detected-themes-panel,
    .stat-card,
    .song-card,
    .welcome-deck {
        backdrop-filter: blur(8px) saturate(1.06) !important;
        -webkit-backdrop-filter: blur(8px) saturate(1.06) !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 12px 30px rgba(0, 0, 0, 0.22) !important;
    }

    .song-card {
        grid-template-columns: 76px minmax(0, 1fr);
        gap: 0.78rem;
        padding: 0.88rem;
    }

    .song-art-container {
        width: 76px;
        height: 76px;
    }

    .score-label {
        align-items: flex-start;
        flex-direction: column;
        gap: 0.24rem;
    }

    .image-ready-meta,
    .retrieval-summary-chips,
    .detected-theme-list {
        gap: 0.35rem;
    }

    .image-ready-meta span,
    .summary-chip,
    .song-tag,
    .match-reason,
    .detected-theme-chip {
        font-size: 0.62rem;
    }

    .stButton > button {
        font-size: 0.78rem !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
    }

    .intake-shell,
    .image-ready-panel,
    .retrieval-summary,
    .analysis-stage,
    .empty-guidance,
    .search-context-panel,
    .detected-themes-panel {
        padding: 0.85rem;
    }

    audio {
        filter: none !important;
    }
}

@media (prefers-reduced-motion: reduce) {
    .analysis-stage::before,
    .analysis-disc,
    .analysis-bars span,
    .score-bar-fill,
    .version-badge::before,
    .hero-status::before {
        animation: none !important;
    }
}

/* Premium DJ Console Playlist Scrollbar and scroll window */
.soundtrack-scroll-container {
    max-height: min(68vh, 760px);
    overflow-y: auto;
    padding-right: 0.52rem;
    margin-top: 0.8rem;
    scrollbar-gutter: stable;
}

.soundtrack-scroll-container::-webkit-scrollbar {
    width: 6px;
}

.soundtrack-scroll-container::-webkit-scrollbar-track {
    background: rgba(6, 7, 13, 0.38);
    border-radius: 999px;
}

.soundtrack-scroll-container::-webkit-scrollbar-thumb {
    background: rgba(241, 210, 122, 0.34);
    border-radius: 999px;
}

.soundtrack-scroll-container::-webkit-scrollbar-thumb:hover {
    background: var(--accent-fuchsia);
}

/* Ambient Welcome deck layout and rotating record graphic */
.welcome-deck {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2.4rem 1.5rem;
    text-align: center;
    background: var(--glass-bg);
    border: 1px solid var(--surface-border);
    border-radius: 8px;
    box-shadow: var(--glass-shadow-quiet);
    min-height: 440px;
    margin-top: 0.3rem;
    backdrop-filter: blur(var(--glass-blur)) saturate(1.1);
    -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(1.1);
}

.deck-vinyl-wrapper {
    position: relative;
    width: 130px;
    height: 130px;
    margin-bottom: 1.8rem;
}

.deck-vinyl {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    background:
        radial-gradient(circle at center, #06070d 0 16%, #34363b 17% 18%, #06070d 19% 34%, #1d1e22 35% 36%, #06070d 37% 54%, #2c2e34 55% 57%, #06070d 58% 100%),
        conic-gradient(from 0deg, rgba(217, 224, 234, 0.14) 0deg, transparent 82deg, rgba(241, 210, 122, 0.16) 155deg, transparent 236deg, rgba(185, 128, 104, 0.12) 320deg, transparent 360deg);
    box-shadow: 0 18px 48px rgba(0, 0, 0, 0.5), 0 0 26px rgba(241, 210, 122, 0.22);
    animation: vinyl-spin 10s linear infinite;
}

.vinyl-label {
    position: absolute;
    inset: 38%;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent-cyan), var(--primary), var(--accent-fuchsia), var(--accent-amber));
    display: flex;
    align-items: center;
    justify-content: center;
}

.vinyl-label-center {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #06070d;
}

@keyframes vinyl-spin {
    to { transform: rotate(360deg); }
}

.deck-title {
    font-family: var(--font-ui);
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.deck-desc {
    font-size: 0.9rem;
    color: var(--text-secondary);
    max-width: 360px;
    margin: 0 auto;
    line-height: 1.5;
}

/* Custom embedded HTML5 audio control styling */
.song-player-container {
    margin-top: 0.8rem;
    width: 100%;
}

.song-card audio {
    width: 100%;
    height: 32px;
    border-radius: 6px;
    background: #090b14;
    border: 1px solid rgba(217, 224, 234, 0.16);
    outline: none;
}

.song-card audio::-webkit-media-controls-enclosure {
    background-color: #090b14 !important;
}

.song-card audio::-webkit-media-controls-panel {
    background-color: #090b14 !important;
    color: var(--text-primary) !important;
}

/* ── Sidebar: Collapsed & Expanded Controls ──────────────────────
   Streamlit 1.58 caches collapse state in localStorage. To prevent
   the sidebar from being stuck collapsed, we render a highly-visible
   floating glass button in the top-left corner on all viewports
   whenever the sidebar is collapsed.
   ─────────────────────────────────────────────────────────────── */

/* Make the expand button very visible when sidebar is collapsed (all screens) */
div[data-testid="collapsedControl"],
header [data-testid="stSidebarCollapseButton"],
header button[data-testid="stBaseButton-headerNoPadding"] {
    background-color: rgba(18, 19, 23, 0.95) !important;
    border: 1px solid rgba(217, 224, 234, 0.28) !important;
    border-radius: 8px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 12px rgba(241, 210, 122, 0.16) !important;
    z-index: 999999 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 42px !important;
    height: 42px !important;
    position: fixed !important;
    top: 0.85rem !important;
    left: 0.85rem !important;
    cursor: pointer !important;
    transition: border-color 0.2s ease, background-color 0.2s ease !important;
}

div[data-testid="collapsedControl"]:hover,
header [data-testid="stSidebarCollapseButton"]:hover,
header button[data-testid="stBaseButton-headerNoPadding"]:hover {
    border-color: var(--accent-cyan) !important;
    background-color: rgba(255, 255, 255, 0.08) !important;
}

div[data-testid="collapsedControl"] button,
header [data-testid="stSidebarCollapseButton"] button,
header button[data-testid="stBaseButton-headerNoPadding"] button {
    color: var(--text-primary) !important;
    fill: var(--text-primary) !important;
    background-color: transparent !important;
    border: none !important;
}

div[data-testid="collapsedControl"] svg,
header [data-testid="stSidebarCollapseButton"] svg,
header button[data-testid="stBaseButton-headerNoPadding"] svg {
    fill: var(--text-primary) !important;
    color: var(--text-primary) !important;
}

/* Sidebar close/collapse button styling (inside expanded sidebar) */
section[data-testid="stSidebar"] button {
    color: var(--text-primary) !important;
    background-color: rgba(255, 255, 255, 0.065) !important;
    border: 1px solid rgba(217, 224, 234, 0.18) !important;
    border-radius: 8px !important;
    transition: border-color 0.2s ease !important;
}

section[data-testid="stSidebar"] button:hover {
    border-color: var(--accent-cyan) !important;
    background-color: rgba(255, 255, 255, 0.12) !important;
}

</style>
""".replace("__GOOGLE_FONTS_URL__", GOOGLE_FONTS_URL)
