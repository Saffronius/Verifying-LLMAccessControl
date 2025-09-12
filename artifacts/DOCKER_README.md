# Docker Deployment Guide for Quacky Pipeline Demo

This guide provides instructions for running the Quacky Pipeline Demo using Docker, making it easy for reviewers to test the application without complex setup.

## Prerequisites

- Docker Engine 20.10+ installed
- Docker Compose 2.0+ (optional, for docker-compose deployment)
- At least 4GB of available RAM
- API keys for LLM services (at least one of: Anthropic, OpenAI, Google, Grok, or DeepSeek)

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Clone the repository** and navigate to the artifacts directory:
```bash
git clone <repository-url>
cd VerifyingLLMGeneratedPolicies/Prev-Experiments/Verifying-LLMAccessControl/artifacts
```

2. **Set up your API keys**:
```bash
cp .env.example .env
# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

3. **Start the application**:
```bash
docker-compose up -d
```

4. **Access the application**:
Open your browser and navigate to http://localhost:8501

5. **View logs** (optional):
```bash
docker-compose logs -f
```

6. **Stop the application**:
```bash
docker-compose down
```

### Option 2: Using Docker Scripts

1. **Make scripts executable**:
```bash
chmod +x docker-build.sh docker-run.sh
```

2. **Build the Docker image**:
```bash
./docker-build.sh
```

3. **Run the container**:
```bash
./docker-run.sh
```

4. **Access the application**:
Open your browser and navigate to http://localhost:8501

### Option 3: Manual Docker Commands

1. **Build the image** (from the repository root):
```bash
cd /path/to/VerifyingLLMGeneratedPolicies
docker build -f Prev-Experiments/Verifying-LLMAccessControl/artifacts/Dockerfile -t quacky-pipeline-demo:latest .
```

2. **Run the container**:
```bash
docker run -d \
  --name quacky-pipeline-demo \
  -p 8501:8501 \
  --env-file artifacts/.env \
  -v $(pwd)/artifacts/results:/app/results \
  -v $(pwd)/artifacts/temp:/app/temp \
  quacky-pipeline-demo:latest
```

## Environment Variables

The application requires API keys to function. Create a `.env` file with the following structure:

```env
# At least one of these is required
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here
GROK_API_KEY=your_grok_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
```

## Container Details

### Exposed Ports
- `8501`: Streamlit web interface

### Volumes
- `/app/results`: Stores analysis results (mounted to `./results`)
- `/app/temp`: Temporary files for processing (mounted to `./temp`)
- `/app/.env`: Environment configuration (mounted read-only)

### Included Components
- Python 3.10 runtime
- Streamlit web framework
- ABC solver (built from source from GitHub)
- Quacky verification tool (includes local modifications)
- All required Python dependencies

### Important Note on Quacky
The Docker image includes a **modified version of Quacky** with necessary customizations already applied. This modified version is bundled in the `quacky/` directory within the artifacts folder. The Docker build uses this local version rather than pulling from GitHub to ensure all customizations are preserved.

## Features Available in Docker

All features of the Quacky Pipeline Demo are available:

1. **Policy Generation** - Convert natural language to AWS IAM policies
2. **Policy Comparison** - Quantitative analysis using SMT solving
3. **String Generation** - Generate distinguishing example requests
4. **Regex Synthesis** - Create patterns from example strings

## Troubleshooting

### Container won't start
- Check if port 8501 is already in use: `lsof -i :8501`
- Verify .env file exists and contains valid API keys
- Check Docker logs: `docker logs quacky-pipeline-demo`

### Build fails
- Ensure you have sufficient disk space (>2GB)
- Check internet connection (needs to download dependencies)
- Verify Docker daemon is running: `docker info`

### Application errors
- Ensure at least one API key is configured in .env
- Check container logs for specific error messages
- Verify ABC solver built correctly during image creation

### Performance issues
- Allocate more memory to Docker (Settings → Resources)
- Ensure at least 4GB RAM is available
- Close other resource-intensive applications

## Advanced Configuration

### Custom Model Preferences
The application supports different model configurations:
- **best**: Claude Opus 4.1 / GPT-5 (most capable)
- **reasoning**: Claude Sonnet 4 / O3-Pro (deep reasoning)
- **fast**: Claude 3.7 / GPT-5-mini (quick responses)
- **legacy**: Previous generation models

Configure via the sidebar in the web interface.

### Rebuilding the Image
To rebuild with latest changes:
```bash
docker-compose build --no-cache
# or
./docker-build.sh
```

### Running in Development Mode
For development with live code reloading:
```bash
docker run -it --rm \
  -p 8501:8501 \
  -v $(pwd):/app/VerifyingLLMGeneratedPolicies/Prev-Experiments/Verifying-LLMAccessControl/artifacts \
  --env-file .env \
  quacky-pipeline-demo:latest
```

## Security Considerations

- API keys are stored in `.env` and should never be committed to version control
- The container runs with minimal privileges
- Network access is limited to the Streamlit port (8501)
- Volumes are mounted read-only where possible

## Support

For issues specific to Docker deployment:
1. Check the troubleshooting section above
2. Review container logs: `docker logs quacky-pipeline-demo`
3. Ensure all prerequisites are met
4. Verify API keys are correctly configured

For application-specific issues, refer to the main README.md.

## Cleanup

To completely remove the Docker setup:
```bash
# Stop and remove container
docker-compose down
# or
docker stop quacky-pipeline-demo
docker rm quacky-pipeline-demo

# Remove image
docker rmi quacky-pipeline-demo:latest

# Remove volumes (optional - this deletes results)
rm -rf ./results ./temp
```

## Notes for Reviewers

- The Docker image includes all necessary components (ABC solver, Quacky, dependencies)
- No local installation of ABC or Quacky is required
- Results persist in the `./results` directory between container restarts
- The application is fully functional within the container environment
- Build time is approximately 5-10 minutes due to ABC compilation