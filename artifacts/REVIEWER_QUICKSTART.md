# Reviewer Quick Start Guide

## What's Included

This artifacts folder is a **self-contained demo** of the Quacky Pipeline for policy verification. Everything you need is included:

- ✅ **Modified Quacky** (37MB) - Includes all necessary customizations
- ✅ **Docker configuration** - Builds ABC from source, uses bundled Quacky
- ✅ **Streamlit web interface** - User-friendly UI for all features
- ✅ **Example policies** - Sample AWS IAM policies for testing

## Prerequisites

1. **Docker** and **Docker Compose** installed
2. At least one **API key** (Anthropic, OpenAI, Google, etc.)
3. **4GB RAM** available
4. **Port 8501** free

## 3-Step Setup

```bash
# Step 1: Configure API keys
cp .env.example .env
nano .env  # Add at least one API key

# Step 2: Build and run
docker-compose up -d

# Step 3: Open browser
# Navigate to http://localhost:8501
```

## First Run Notes

- **Build time**: ~5-10 minutes (ABC compilation)
- **Subsequent runs**: Instant (uses cached image)
- **Logs**: `docker-compose logs -f`
- **Stop**: `docker-compose down`

## What Happens During Build

1. **ABC Solver**: Pulled from GitHub and compiled
2. **Quacky**: Uses the bundled `quacky/` directory (with modifications)
3. **Dependencies**: All Python packages installed
4. **Environment**: Configured for Docker deployment

## Testing the Demo

Once running, try these features:

1. **Policy Generation**: Convert "Allow EC2 in us-west-2" to IAM policy
2. **Policy Comparison**: Compare two policies quantitatively
3. **String Generation**: Get example requests that distinguish policies
4. **Regex Synthesis**: Generate patterns from example strings

## Troubleshooting

If you encounter issues:

```bash
# Check your setup
./test-docker-setup.sh

# View container logs
docker-compose logs

# Restart fresh
docker-compose down
docker-compose up --build
```

## Files Overview

- `docker-compose.yml` - Orchestration configuration
- `Dockerfile` - Container build instructions
- `quacky/` - Modified Quacky tool (bundled)
- `app.py` - Main Streamlit application
- `backend/` - Core logic and wrappers
- `.env.example` - Template for API keys

## Support

For Docker-specific issues, see [DOCKER_README.md](DOCKER_README.md)
For application details, see [README.md](README.md)

---
**Note**: This is a research demonstration. The bundled Quacky includes modifications necessary for the demo to function correctly.