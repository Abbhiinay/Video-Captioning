# ─── Stage 1: Build / dependency install ─────────
FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .
COPY api/requirements.txt ./api_requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt -r api_requirements.txt

# ─── Stage 2: Runtime image ───────────────────────    
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

WORKDIR /app

COPY config/           ./config/
COPY description/      ./description/
COPY src/              ./src/
COPY scripts/          ./scripts/
COPY api/              ./api/
COPY requirements.txt  ./requirements.txt
COPY .env*             ./

# Create the run_all.py entrypoint at root
RUN cp scripts/run_all.py run_all.py

RUN mkdir -p /input /output

ENV GEMINI_MODEL=gemini-2.5-flash
ENV FRAME_COUNT=5
ENV ENABLE_SCENE_DETECTION=true
ENV INPUT_TASKS_PATH=/input/tasks.json
ENV OUTPUT_RESULTS_PATH=/output/results.json

RUN useradd -m -u 1000 runner
RUN chown -R runner:runner /app /input /output
USER runner

# Entrypoint
CMD ["python", "run_all.py"]
