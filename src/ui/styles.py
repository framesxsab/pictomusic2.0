"""
PictoMusic Global CSS
Glassmorphic dark theme with violet/neon gradients.
"""


def get_global_css() -> str:
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root {
    --primary: #4f06f9;
    --primary-dim: rgba(79, 6, 249, 0.15);
    --accent-pink: #d400ff;
    --accent-blue: #00d4ff;
    --bg-dark: #0a0516;
    --bg-card: rgba(79, 6, 249, 0.06);
    --border-glow: rgba(79, 6, 249, 0.25);
    --text-primary: #f0eef5;
    --text-secondary: #8a85a0;
    --text-muted: #5a5670;
    --glass-bg: rgba(255, 255, 255, 0.03);
    --glass-border: rgba(255, 255, 255, 0.08);
}

html, body, [data-testid="stAppViewContainer"], .stApp,
[data-testid="stHeader"], [data-testid="stToolbar"] {
    background-color: var(--bg-dark) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

#MainMenu, header[data-testid="stHeader"], footer,
[data-testid="stToolbar"], .stDeployButton {
    display: none !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0820 0%, #0a0516 100%) !important;
    border-right: 1px solid var(--border-glow) !important;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown span,
section[data-testid="stSidebar"] .stMarkdown li {
    color: var(--text-secondary) !important;
}

section[data-testid="stSidebar"] .stRadio label {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
}

section[data-testid="stSidebar"] .stRadio label:hover {
    color: var(--text-primary) !important;
}

/* Glassmorphism cards */
.glass-card {
    background: var(--glass-bg);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--glass-border);
    border-radius: 1.5rem;
    padding: 2rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
}

.glass-card:hover {
    border-color: var(--border-glow);
    box-shadow: 0 0 30px rgba(79, 6, 249, 0.08);
}

/* Hero title */
.hero-title {
    font-size: clamp(2.5rem, 6vw, 4.5rem);
    font-weight: 900;
    letter-spacing: -0.03em;
    line-height: 1.1;
    background: linear-gradient(135deg, #4f06f9 0%, #d400ff 50%, #00d4ff 100%);
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
    font-weight: 300;
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
    color: var(--primary);
    margin: 0 auto;
}

.version-badge::before {
    content: '';
    width: 6px;
    height: 6px;
    background: var(--primary);
    border-radius: 50%;
    animation: pulse-dot 2s infinite;
}

@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.8); }
}

/* Song card */
.song-card {
    background: var(--bg-card);
    backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: 1.25rem;
    padding: 1.5rem;
    margin-bottom: 0.75rem;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.song-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: linear-gradient(180deg, var(--primary), var(--accent-pink));
    border-radius: 4px 0 0 4px;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.song-card:hover {
    border-color: var(--border-glow);
    transform: translateX(4px);
    box-shadow: 0 8px 32px rgba(79, 6, 249, 0.12);
}

.song-card:hover::before {
    opacity: 1;
}

.song-rank {
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--primary);
    margin-bottom: 0.25rem;
}

.song-name {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    letter-spacing: -0.01em;
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
    background: rgba(79, 6, 249, 0.08);
    border: 1px solid rgba(79, 6, 249, 0.15);
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
    font-size: 0.75rem;
    font-weight: 800;
    color: var(--primary);
}

.score-bar-bg {
    width: 100%;
    height: 6px;
    background: rgba(79, 6, 249, 0.1);
    border-radius: 9999px;
    overflow: hidden;
}

.score-bar-fill {
    height: 100%;
    border-radius: 9999px;
    background: linear-gradient(90deg, var(--primary), var(--accent-pink));
    box-shadow: 0 0 12px rgba(79, 6, 249, 0.5);
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Section headers */
.section-header {
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    margin-bottom: 0.25rem;
}

.section-accent {
    color: var(--primary);
}

/* Upload area */
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
    border-radius: 1.25rem !important;
    overflow: hidden !important;
}

[data-testid="stFileUploadDropzone"] {
    border: 2px dashed var(--border-glow) !important;
    border-radius: 1.25rem !important;
    transition: all 0.3s ease !important;
    background-color: rgba(79, 6, 249, 0.04) !important;
    padding: 2.5rem 1.5rem !important;
}

[data-testid="stFileUploadDropzone"]:hover {
    border-color: var(--primary) !important;
    box-shadow: 0 0 24px rgba(79, 6, 249, 0.15) !important;
    background-color: rgba(79, 6, 249, 0.08) !important;
}

[data-testid="stFileUploadDropzone"] > div:first-child > div:first-child > span {
    font-size: 0 !important;
}

[data-testid="stFileUploadDropzone"] > div:first-child > div:first-child > span::after {
    content: '🖼️  Drop your image here or browse' !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: var(--text-secondary) !important;
    letter-spacing: 0.01em !important;
}

[data-testid="stFileUploadDropzone"] > div:first-child > div:first-child > small {
    font-size: 0 !important;
}

[data-testid="stFileUploadDropzone"] > div:first-child > div:first-child > small::after {
    content: 'JPG, PNG, WEBP — Max 10 MB' !important;
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
    background-color: rgba(79, 6, 249, 0.25) !important;
    border-color: var(--primary) !important;
}

/* Text input */
.stTextInput input {
    background: var(--bg-card) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 0.75rem !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.3s ease !important;
}

.stTextInput input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(79, 6, 249, 0.2) !important;
}

.stTextInput label {
    color: var(--text-secondary) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--primary), #6d28d9) !important;
    color: white !important;
    border: none !important;
    border-radius: 0.75rem !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.75rem 2rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 20px rgba(79, 6, 249, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 8px 40px rgba(79, 6, 249, 0.5) !important;
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
    background: rgba(79, 6, 249, 0.06) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 0.75rem !important;
    padding: 0.6rem 1rem !important;
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    cursor: pointer !important;
    transition: all 0.25s ease !important;
    margin: 0 !important;
}

.stRadio [role="radiogroup"] label:hover {
    background: rgba(79, 6, 249, 0.12) !important;
    border-color: var(--border-glow) !important;
    color: var(--text-primary) !important;
}

.stRadio [role="radiogroup"] label[data-checked="true"],
.stRadio [role="radiogroup"] label:has(input:checked) {
    background: var(--primary-dim) !important;
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    box-shadow: 0 0 12px rgba(79, 6, 249, 0.2) !important;
}

.stRadio [role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
}

/* Spinner */
.stSpinner > div {
    border-top-color: var(--primary) !important;
}

/* Image display */
[data-testid="stImage"] {
    border-radius: 1.25rem;
    overflow: hidden;
    border: 1px solid var(--glass-border);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

/* Audio player */
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
    background: var(--accent-pink);
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
    background: var(--glass-bg);
    backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-left: 4px solid var(--primary);
    border-radius: 1rem;
    padding: 1.25rem 1.5rem;
    text-align: left;
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
    font-size: 1.75rem;
    font-weight: 900;
    color: var(--text-primary);
}

.stat-unit {
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--primary);
    margin-left: 0.35rem;
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
    background: radial-gradient(circle, rgba(79, 6, 249, 0.12) 0%, transparent 70%);
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
}
</style>
"""
