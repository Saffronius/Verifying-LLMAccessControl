#!/bin/bash
# Launch script for Quacky Pipeline Demo

echo "🚀 Launching Quacky Pipeline Demo..."
echo ""

# Check dependencies
echo "Checking dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check ABC solver
if ! command -v abc &> /dev/null; then
    echo "⚠️  Warning: ABC solver not found in PATH"
    echo "   Some features may not work properly"
    echo "   Install ABC and add to PATH for full functionality"
fi

# Check quacky
QUACKY_PATH="/home/ash/Desktop/VerifyingLLMGeneratedPolicies/CPCA/quacky/src/quacky.py"
if [ ! -f "$QUACKY_PATH" ]; then
    echo "❌ Quacky not found at: $QUACKY_PATH"
    exit 1
fi

# Check .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "   Please edit .env and add your API keys"
fi

# Install dependencies if needed
echo "Installing Python dependencies..."
pip install -q -r requirements.txt 2>/dev/null

echo ""
echo "✅ Setup complete!"
echo ""
echo "Starting Streamlit app..."
echo "--------------------------------"
echo "Access the app at: http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo "--------------------------------"
echo ""

# Launch Streamlit
streamlit run app.py