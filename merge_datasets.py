"""
Merge all Indian song datasets into the existing Music.csv
Output: Single unified Music.csv with all songs
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np
import os
import glob

print("=" * 60)
print("PICTOMUSIC 2.0 - Pan-Indian Dataset Merge")
print("=" * 60)

# ── 1. Load existing Music.csv ──────────────────────────────
print("\n[1/6] Loading existing Music.csv...")
existing = pd.read_csv('Music.csv')
print(f"  Existing songs: {len(existing):,}")
print(f"  Columns: {list(existing.columns)}")

# Target schema (from existing Music.csv)
TARGET_COLS = [
    'name', 'artist', 'spotify_id', 'preview', 'img',
    'danceability', 'energy', 'loudness', 'speechiness',
    'acousticness', 'instrumentalness', 'liveness', 'valence',
    'acousticness_artist', 'danceability_artist', 'energy_artist',
    'instrumentalness_artist', 'liveness_artist', 'speechiness_artist',
    'valence_artist'
]

AUDIO_FEATURES = [
    'danceability', 'energy', 'loudness', 'speechiness',
    'acousticness', 'instrumentalness', 'liveness', 'valence'
]

ARTIST_AGG_FEATURES = [
    'acousticness', 'danceability', 'energy',
    'instrumentalness', 'liveness', 'speechiness', 'valence'
]


# ── 2. Process spotify_tracks.csv (60K multi-language) ──────
print("\n[2/6] Processing spotify_tracks.csv (multi-language)...")
df_tracks = pd.read_csv('datasets/spotify_tracks.csv')
print(f"  Total tracks: {len(df_tracks):,}")

# Filter to Indian languages only
indian_langs = ['Hindi', 'Tamil', 'Telugu', 'Malayalam']
df_tracks_indian = df_tracks[df_tracks['language'].isin(indian_langs)].copy()
print(f"  Indian tracks: {len(df_tracks_indian):,}")

# Map columns
df_tracks_indian = df_tracks_indian.rename(columns={
    'track_name': 'name',
    'artist_name': 'artist',
    'track_id': 'spotify_id',
    'artwork_url': 'img',
})
df_tracks_indian['preview'] = ''  # Will need Spotify API to fill
df_tracks_indian['source'] = 'spotify_tracks'


# ── 3. Process regional language CSVs (37K across 16 langs) ─
print("\n[3/6] Processing regional language CSVs...")
regional_files = sorted(glob.glob('datasets/*_songs.csv'))
regional_dfs = []

for fpath in regional_files:
    lang = os.path.basename(fpath).replace('_songs.csv', '')
    df_lang = pd.read_csv(fpath)
    
    # Rename columns to match target schema
    df_lang = df_lang.rename(columns={
        'song_name': 'name',
        'singer': 'artist',
        'singer_id': 'spotify_id',
        'Valence': 'valence',
    })
    df_lang['img'] = ''        # Regional CSVs don't have artwork
    df_lang['preview'] = ''    # No preview URLs
    df_lang['source'] = f'regional_{lang}'
    
    regional_dfs.append(df_lang)
    print(f"  {lang}: {len(df_lang):,} songs")

df_regional = pd.concat(regional_dfs, ignore_index=True)
print(f"  Total regional: {len(df_regional):,}")


# ── 4. Process Bollywood 2024 (1.4K curated tracks) ─────────
print("\n[4/6] Processing Bollywood 2024 dataset...")
df_bollywood = pd.read_csv('datasets/data.csv')
print(f"  Bollywood tracks: {len(df_bollywood):,}")

df_bollywood = df_bollywood.rename(columns={
    'song_name': 'name',
    'artist_name': 'artist',
    'track_spotify_id': 'spotify_id',
    'thumbnail_link': 'img',
})
df_bollywood['preview'] = ''
df_bollywood['source'] = 'bollywood_2024'


# ── 5. Merge everything ────────────────────────────────────
print("\n[5/6] Merging all datasets...")

# Standardize each dataset to have the required audio feature columns
def standardize(df, name):
    """Ensure all required audio feature columns exist."""
    for col in AUDIO_FEATURES:
        if col not in df.columns:
            df[col] = np.nan
    
    # Keep only relevant columns + source
    keep_cols = ['name', 'artist', 'spotify_id', 'preview', 'img'] + AUDIO_FEATURES + ['source']
    available = [c for c in keep_cols if c in df.columns]
    missing = [c for c in keep_cols if c not in df.columns]
    if missing:
        for c in missing:
            df[c] = '' if c in ['name', 'artist', 'spotify_id', 'preview', 'img', 'source'] else np.nan
    
    result = df[keep_cols].copy()
    print(f"  {name}: {len(result):,} rows, {result['spotify_id'].notna().sum():,} with spotify_id")
    return result

existing['source'] = 'original'
df_exist = standardize(existing, 'Original Music.csv')
df_st = standardize(df_tracks_indian, 'Spotify Tracks (Indian)')
df_rg = standardize(df_regional, 'Regional Languages')
df_bw = standardize(df_bollywood, 'Bollywood 2024')

# Combine all
combined = pd.concat([df_exist, df_st, df_rg, df_bw], ignore_index=True)
print(f"\n  Combined (before dedup): {len(combined):,}")

# Clean up
combined['name'] = combined['name'].astype(str).str.strip()
combined['artist'] = combined['artist'].astype(str).str.strip()
combined['spotify_id'] = combined['spotify_id'].astype(str).str.strip()

# Remove rows with no name or artist
combined = combined[
    (combined['name'] != '') & 
    (combined['name'] != 'nan') & 
    (combined['artist'] != '') & 
    (combined['artist'] != 'nan')
]
print(f"  After cleaning empty rows: {len(combined):,}")

# Deduplicate on spotify_id (prefer entries with more data)
# Sort so that entries with preview/img come first
combined['has_preview'] = combined['preview'].astype(str).str.startswith('http').astype(int)
combined['has_img'] = combined['img'].astype(str).str.startswith('http').astype(int)
combined['richness'] = combined['has_preview'] + combined['has_img']
combined = combined.sort_values('richness', ascending=False)

# Deduplicate — keep richest entry per spotify_id
valid_ids = combined['spotify_id'].notna() & (combined['spotify_id'] != '') & (combined['spotify_id'] != 'nan')
df_with_id = combined[valid_ids].drop_duplicates(subset=['spotify_id'], keep='first')
df_no_id = combined[~valid_ids]
# For songs without spotify_id, deduplicate on name+artist
df_no_id = df_no_id.drop_duplicates(subset=['name', 'artist'], keep='first')

combined = pd.concat([df_with_id, df_no_id], ignore_index=True)
combined = combined.drop(columns=['has_preview', 'has_img', 'richness'])
print(f"  After deduplication: {len(combined):,}")


# ── 6. Compute artist aggregates ────────────────────────────
print("\n[6/6] Computing artist-level aggregate features...")

artist_agg = combined.groupby('artist')[ARTIST_AGG_FEATURES].mean()
artist_agg.columns = [f'{col}_artist' for col in ARTIST_AGG_FEATURES]
artist_agg = artist_agg.reset_index()

# Drop existing artist columns if any
for col in [f'{c}_artist' for c in ARTIST_AGG_FEATURES]:
    if col in combined.columns:
        combined = combined.drop(columns=[col])

combined = combined.merge(artist_agg, on='artist', how='left')

# Reorder columns to match original schema + source column
final_cols = TARGET_COLS + ['source']
for col in final_cols:
    if col not in combined.columns:
        combined[col] = '' if col in ['name', 'artist', 'spotify_id', 'preview', 'img', 'source'] else np.nan

combined = combined[final_cols]

# ── Save ────────────────────────────────────────────────────
# Backup original
if os.path.exists('Music_original_backup.csv'):
    print("\n  Backup already exists, skipping...")
else:
    os.rename('Music.csv', 'Music_original_backup.csv')
    print("\n  Backed up original as Music_original_backup.csv")

combined.to_csv('Music.csv', index=False)
print(f"\n  SAVED: Music.csv ({len(combined):,} songs)")

# Summary stats
print("\n" + "=" * 60)
print("MERGE COMPLETE - Summary")
print("=" * 60)
source_counts = combined['source'].value_counts()
for source, count in source_counts.items():
    print(f"  {source}: {count:,} songs")
print(f"\n  TOTAL: {len(combined):,} songs")

# Preview/img coverage
has_preview = combined['preview'].astype(str).str.startswith('http').sum()
has_img = combined['img'].astype(str).str.startswith('http').sum()
print(f"\n  Songs with preview URL: {has_preview:,} ({100*has_preview/len(combined):.1f}%)")
print(f"  Songs with album art: {has_img:,} ({100*has_img/len(combined):.1f}%)")

print("\n[IMPORTANT] You must now delete song_embeddings_fp16.npy")
print("  and restart the app to regenerate embeddings for all songs.")
print("  This will take 30-60 min on CPU.")
