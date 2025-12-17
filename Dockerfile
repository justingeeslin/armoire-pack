# Include Python
FROM python:3.12-slim

# Label your image with metadata
LABEL maintainer="info@blib.la"
LABEL org.opencontainers.image.source https://github.com/blib-la/runpod-worker-helloworld
LABEL org.opencontainers.image.description "Getting started with a serverless endpoint on RunPod by creating a custom worker"

WORKDIR /

# Copy your source code into the image
COPY src/ .

# Make the start script executable
RUN chmod +x start.sh

# Define your working directory
WORKDIR /app

# Copy the requirements into the image
COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ cmake git libcgal-dev libboost-all-dev pkg-config
RUN pip install --no-cache-dir -r requirements.txt gunicorn parameterized shapely svgelements

RUN git clone https://github.com/justingeeslin/Packaide.git
WORKDIR /app/Packaide
RUN mkdir -p build \
 && cmake -S /app/Packaide/ -B build  \
 && cmake --build build -j$(nproc) \
 && cmake --install build
COPY . .

WORKDIR /

# Run the start script
CMD ["/start.sh"]