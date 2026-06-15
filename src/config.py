"""
PictoMusic Configuration Module
Override any setting via environment variables.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = os.getenv("PICTOMUSIC_DATASET_PATH", str(BASE_DIR / "Music.csv"))
EMBEDDINGS_PATH = os.getenv(
    "PICTOMUSIC_EMBEDDINGS_PATH", str(BASE_DIR / "song_embeddings_fp16.npy")
)

CLIP_MODEL_NAME = os.getenv("PICTOMUSIC_CLIP_MODEL", "openai/clip-vit-base-patch32")
EMBEDDING_BATCH_SIZE = int(os.getenv("PICTOMUSIC_BATCH_SIZE", "32"))
MAX_TOKEN_LENGTH = int(os.getenv("PICTOMUSIC_MAX_TOKEN_LEN", "77"))

DEFAULT_TOP_K = int(os.getenv("PICTOMUSIC_TOP_K", "10"))
RETRIEVAL_CANDIDATE_MULTIPLIER = int(
    os.getenv("PICTOMUSIC_RETRIEVAL_CANDIDATE_MULT", "30")
)

ALLOWED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
MAX_UPLOAD_SIZE_MB = int(os.getenv("PICTOMUSIC_MAX_UPLOAD_MB", "10"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
REQUEST_TIMEOUT = int(os.getenv("PICTOMUSIC_REQUEST_TIMEOUT", "10"))
MAX_URL_LENGTH = int(os.getenv("PICTOMUSIC_MAX_URL_LEN", "2048"))
ALLOWED_URL_SCHEMES = ("http", "https")

_BLOCKED_IP_PREFIXES = (
    "127.", "10.", "0.", "192.168.", "172.16.", "172.17.", "172.18.",
    "172.19.", "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
    "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.",
    "172.31.", "169.254.", "::1", "fc00:", "fd00:", "fe80:",
)

_IMAGE_MAGIC_BYTES = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG": "png",
    b"RIFF": "webp",
}

SONG_TEXT_COLUMNS = ["name", "artist"]

AUDIO_FEATURE_COLUMNS = [
    "danceability", "energy", "valence", "acousticness",
    "instrumentalness", "liveness", "speechiness",
]

# New dataset columns
DATASET_EXTRA_COLUMNS = ["language", "genre", "region", "mood_tags"]

# (column, low_threshold, high_threshold, low_label, high_label, weight)
# Weight controls priority in description — higher-weight descriptors appear first
FEATURE_DESCRIPTORS = [
    ("energy",            0.25, 0.65, "calm and mellow",       "energetic and intense",   1.5),
    ("valence",           0.25, 0.65, "melancholic and dark",   "happy and upbeat",        1.5),
    ("danceability",      0.25, 0.65, "slow and steady",        "danceable and groovy",    1.2),
    ("acousticness",      0.25, 0.65, "electronic",             "acoustic and organic",    1.0),
    ("instrumentalness",  0.25, 0.65, "vocal",                  "instrumental",            0.8),
    ("speechiness",       0.3,  0.7,  "",                       "spoken word or rap",      0.7),
    ("liveness",          0.4,  0.8,  "",                       "live concert energy",     0.5),
]

# Image mood categories for zero-shot CLIP classification + re-ranking
IMAGE_MOOD_KEYWORDS = {
    "nature and greenery":    ["peaceful", "acoustic", "calm", "organic"],
    "sunset and golden hour": ["romantic", "melancholic", "warm", "soothing"],
    "party and celebration":  ["energetic", "danceable", "happy", "groovy"],
    "rain and storm":         ["melancholic", "sad", "calm", "dark"],
    "city and urban":         ["urban", "energetic", "modern", "electronic"],
    "ocean and beach":        ["peaceful", "calm", "happy", "soothing"],
    "night and darkness":     ["dark", "melancholic", "electronic", "intense"],
    "festival and lights":    ["energetic", "happy", "danceable", "intense"],
    "mountain and landscape": ["peaceful", "acoustic", "organic", "calm"],
    "portrait and emotion":   ["romantic", "vocal", "soothing", "warm"],
    "temple and spiritual":   ["peaceful", "acoustic", "devotional", "calm"],
    "dance and movement":     ["danceable", "energetic", "groovy", "happy"],
}

# Mood re-ranking boost factor (0.0 = no boost, 0.15 = moderate boost)
MOOD_RERANK_BOOST = float(os.getenv("PICTOMUSIC_MOOD_BOOST", "0.1"))

# Rate limiter defaults
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("PICTOMUSIC_RATE_LIMIT_MAX", "10"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("PICTOMUSIC_RATE_LIMIT_WINDOW", "60"))

# PIL decompression bomb limit (~5000x5000 pixels)
MAX_IMAGE_PIXELS = int(os.getenv("PICTOMUSIC_MAX_IMAGE_PIXELS", "25000000"))

APP_TITLE = "Pictomusic"
APP_ICON = "\U0001f3b5"
APP_SUBTITLE = "Image-to-song discovery tuned for Indian moods, languages, and charts"
APP_VERSION_TAG = "v2026 India Retrieval"
HERO_TITLE = "FIND THE INDIAN SOUND<br>INSIDE YOUR IMAGE"

# --- India-first retrieval ---
INDIAN_LANGUAGE_CODES = {
    "hi", "ta", "te", "pa", "bn", "kn", "ml", "mr", "ur", "sa", "bh", "as",
    "gu", "or",
}
INDIAN_REGIONS = {
    "bollywood", "south_indian", "punjabi", "bengali", "marathi", "gujarati",
    "odia", "northeast_indian", "rajasthani", "bhojpuri", "haryanvi",
    "indie_indian", "classical_indian",
}
INDIAN_GENRES = {
    "bollywood", "hindi", "tamil", "telugu", "punjabi", "bengali", "kannada",
    "malayalam", "marathi", "gujarati", "urdu", "odia", "assamese",
    "rajasthani", "bhojpuri", "haryanvi", "devotional", "classical", "sufi",
    "ghazal", "indie_indian", "filmi",
}
INDIAN_ARTIST_HINTS = {
    "arijit singh", "pritam", "a r rahman", "a.r. rahman", "anirudh",
    "anirudh ravichander", "shreya ghoshal", "neha kakkar", "badshah",
    "diljit dosanjh", "ap dhillon", "shubh", "sidhu moose wala",
    "vishal-shekhar", "amit trivedi", "atif aslam", "jubin nautiyal",
    "shankar-ehsaan-loy", "sachet-parampara", "darshan raval",
    "sonu nigam", "udit narayan", "alka yagnik", "kumar sanu",
    "karan aujla", "guru randhawa", "ammy virk", "jass manak",
    "harrdy sandhu", "amrit maan", "mankirt aulakh", "b praak",
    "pawan singh", "khesari lal yadav", "antra singh priyanka",
    "kalpana", "bharat sharma vyas", "sharda sinha",
}
INDIAN_TITLE_HINTS = {
    "dil", "ishq", "pyaar", "yaar", "sajna", "maahi", "tere", "meri",
    "tum", "tu", "aankh", "zindagi", "jhoome", "nach", "balle", "vaathi",
    "raataan", "kesariya", "naina", "channa", "kalank", "deva",
    "bhojpuri", "garba", "chhath", "holi", "bhangra", "gidda",
}
RECENT_YEAR_THRESHOLD = int(os.getenv("PICTOMUSIC_RECENT_YEAR", "2025"))
INDIA_RELEVANCE_WEIGHT = float(os.getenv("PICTOMUSIC_INDIA_WEIGHT", "0.22"))
LANGUAGE_MATCH_WEIGHT = float(os.getenv("PICTOMUSIC_LANGUAGE_WEIGHT", "0.22"))
REGION_MATCH_WEIGHT = float(os.getenv("PICTOMUSIC_REGION_WEIGHT", "0.14"))
FRESHNESS_WEIGHT = float(os.getenv("PICTOMUSIC_FRESHNESS_WEIGHT", "0.08"))
POPULARITY_WEIGHT = float(os.getenv("PICTOMUSIC_POPULARITY_WEIGHT", "0.06"))
PREVIEW_WEIGHT = float(os.getenv("PICTOMUSIC_PREVIEW_WEIGHT", "0.08"))
ARTWORK_WEIGHT = float(os.getenv("PICTOMUSIC_ARTWORK_WEIGHT", "0.015"))
PREVIEW_TARGET_SHARE = float(os.getenv("PICTOMUSIC_PREVIEW_TARGET_SHARE", "0.6"))
PREVIEW_IMPORTANCE_MARGIN = float(os.getenv("PICTOMUSIC_PREVIEW_IMPORTANCE_MARGIN", "0.12"))

# --- Mood inference thresholds (preprocess.py) ---
MOOD_THRESHOLDS = {
    "energetic_happy_valence": 0.65,
    "energetic_happy_energy": 0.65,
    "sad_valence": 0.3,
    "sad_energy": 0.4,
    "calm_energy": 0.35,
    "calm_acousticness": 0.6,
    "danceable": 0.7,
    "acoustic": 0.7,
    "romantic_valence_low": 0.35,
    "romantic_valence_high": 0.65,
    "romantic_energy_low": 0.35,
    "romantic_energy_high": 0.65,
    "romantic_acousticness": 0.4,
    "instrumental": 0.5,
    "soothing_energy": 0.45,
    "soothing_acousticness": 0.5,
    "soothing_valence": 0.3,
}

# --- Recommender constants ---
MOOD_SIMILARITY_THRESHOLD = float(os.getenv("PICTOMUSIC_MOOD_SIM_THRESHOLD", "0.15"))
MOOD_TOP_N = int(os.getenv("PICTOMUSIC_MOOD_TOP_N", "2"))
MOOD_FETCH_MULTIPLIER = int(os.getenv("PICTOMUSIC_MOOD_FETCH_MULT", "3"))
HTTP_CHUNK_SIZE = 8192

# --- External service URLs ---
YOUTUBE_SEARCH_URL = "https://www.youtube.com/results?search_query="
SPOTIFY_TRACK_URL = "https://open.spotify.com/track/"
SPOTIFY_SEARCH_URL = "https://open.spotify.com/search/"
GOOGLE_FONTS_URL = "https://fonts.googleapis.com/css2?family=Anek+Devanagari:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,700;9..144,800&display=swap"

# --- CSP policy domains ---
CSP_IMG_SOURCES = "https://*.scdn.co https://* data:"
CSP_MEDIA_SOURCES = "https://p.scdn.co https://*.scdn.co"
CSP_STYLE_SOURCES = "'unsafe-inline' https://fonts.googleapis.com"
CSP_FONT_SOURCES = "https://fonts.gstatic.com"
CSP_FRAME_ANCESTORS = "https://huggingface.co https://*.hf.space"

# --- Language display map (ISO code -> display name) ---
LANGUAGE_DISPLAY_MAP = {
    "hi": "Hindi", "ta": "Tamil", "te": "Telugu", "pa": "Punjabi",
    "bn": "Bengali", "kn": "Kannada", "ml": "Malayalam", "mr": "Marathi",
    "ur": "Urdu", "sa": "Sanskrit", "bh": "Bhojpuri", "as": "Assamese",
    "gu": "Gujarati", "or": "Odia",
}

# --- Kaggle dataset identifier ---
KAGGLE_DATASET_ID = "gauthamvijayaraj/spotify-tracks-dataset-updated-every-week"
