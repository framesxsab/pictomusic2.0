"""Inspect all dataset schemas for merging."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

print('=== spotify_tracks.csv ===')
df = pd.read_csv('datasets/spotify_tracks.csv')
print(f'Shape: {df.shape}')
print(f'Columns: {list(df.columns)}')
if 'language' in df.columns:
    print(f'Languages: {list(df["language"].unique())}')
print()

print('=== Hindi_songs.csv (sample regional) ===')
df2 = pd.read_csv('datasets/Hindi_songs.csv')
print(f'Shape: {df2.shape}')
print(f'Columns: {list(df2.columns)}')
print()

print('=== Tamil_songs.csv (sample regional) ===')
df2b = pd.read_csv('datasets/Tamil_songs.csv')
print(f'Shape: {df2b.shape}')
print(f'Columns: {list(df2b.columns)}')
print()

print('=== data.csv (Bollywood 2024) ===')
df3 = pd.read_csv('datasets/data.csv')
print(f'Shape: {df3.shape}')
print(f'Columns: {list(df3.columns)}')
print()

print('=== Current Music.csv ===')
df4 = pd.read_csv('Music.csv')
print(f'Shape: {df4.shape}')
print(f'Columns: {list(df4.columns)}')
print()

# Count all regional songs
import os, glob
total = 0
for f in sorted(glob.glob('datasets/*_songs.csv')) + glob.glob('datasets/Old_songs.csv'):
    d = pd.read_csv(f)
    lang = os.path.basename(f).replace('_songs.csv', '')
    print(f'{lang}: {len(d)} songs')
    total += len(d)
print(f'\nTotal regional songs: {total}')
