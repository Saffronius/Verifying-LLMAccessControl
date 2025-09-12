# Multi-stage build for Quacky Pipeline Demo
FROM python:3.10-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    cmake \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Build ABC solver from source
WORKDIR /tmp
RUN git clone https://github.com/vlab-cs-ucsb/ABC.git && \
    cd ABC && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make -j$(nproc) && \
    make install

# Final stage
FROM python:3.10-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    curl \
    git \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy ABC solver from builder
COPY --from=builder /usr/local/bin/abc /usr/local/bin/abc
COPY --from=builder /usr/local/lib/libabc* /usr/local/lib/

# Set working directory for the app
WORKDIR /app

# Copy the modified quacky directory (with your customizations) to the expected location
RUN mkdir -p /opt/VerifyingLLMGeneratedPolicies/CPCA
COPY quacky /opt/VerifyingLLMGeneratedPolicies/CPCA/quacky

# Copy artifacts directory contents
COPY . /app/

# Install Python dependencies for Quacky
RUN pip install --no-cache-dir \
    cel-python \
    selenium \
    sentence-transformers \
    anthropic \
    openai \
    google-generativeai \
    scikit-learn \
    pandas \
    numpy \
    python-dotenv \
    streamlit \
    requests

# Install any additional requirements from requirements.txt if it exists
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Create necessary directories
RUN mkdir -p /app/temp /app/results

# Create a wrapper script to set up environment
RUN echo '#!/bin/bash\n\
# Set up environment for Docker\n\
export QUACKY_PATH="/opt/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/quacky.py"\n\
export QUACKY_DOCKER=1\n\
# Start the application\n\
exec streamlit run app.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true --browser.gatherUsageStats=false' > /app/start.sh && \
    chmod +x /app/start.sh

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV QUACKY_DOCKER=1
ENV QUACKY_PATH=/opt/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/quacky.py

# Run the application
CMD ["/app/start.sh"]