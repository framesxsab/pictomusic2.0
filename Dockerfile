FROM python:3.11-slim
# Build: 2026-06-30 v4 -- pre-cache CLIP model weights

# Create a new user with UID 1000
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_FILE_WATCHER_TYPE=none \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    PICTOMUSIC_STRICT_EMBEDDING_MANIFEST=1 \
    PICTOMUSIC_PUBLIC_APP_URL=https://fxsab-pictomusicu.hf.space

WORKDIR $HOME/app

# Install system dependencies as root
RUN apt-get update && \
    apt-get install -y --no-install-recommends git git-lfs && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file first, setting correct ownership
COPY --chown=user:user requirements.txt .

# Switch to the non-root user
USER user

# Install Python dependencies to the user's local directory
RUN pip install --user --no-cache-dir -r requirements.txt

# Pre-download the CLIP model weights into the HF cache so they are
# baked into the image and available offline at container start.
RUN python -c "\
from transformers import CLIPModel, CLIPProcessor; \
CLIPModel.from_pretrained('openai/clip-vit-base-patch32'); \
CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32'); \
print('CLIP model cached successfully')"

# Copy the rest of the application files with user ownership
COPY --chown=user:user . .

# Expose Streamlit's default port
EXPOSE 7860

# HF Spaces expects port 7860
CMD ["streamlit", "run", "src/app.py", "--server.port=7860", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false", "--server.fileWatcherType=none", "--browser.gatherUsageStats=false"]
