FROM python:3.11-slim

# Install ffmpeg (system dependency for frame extraction)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY . .

# Place run_all.py in the root to satisfy the submission CMD pattern
RUN cp scripts/run_all.py run_all.py

# entrypoint command
CMD ["python", "run_all.py"]

