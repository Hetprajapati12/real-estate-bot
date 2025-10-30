#!/bin/bash

# Real Estate RAG Chatbot Setup Script
# This script automates the initial setup process

set -e  # Exit on error

echo "================================================"
echo "Real Estate RAG Chatbot - Setup Script"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${YELLOW}⚠${NC} Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate
echo -e "${GREEN}✓${NC} Virtual environment activated"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓${NC} Dependencies installed"

# Create __init__.py files
echo ""
echo "Creating package structure..."
touch ingestion/__init__.py
touch retrieval/__init__.py
touch lead/__init__.py
touch services/__init__.py
touch utils/__init__.py
touch tests/__init__.py
echo -e "${GREEN}✓${NC} Package structure created"

# Create directories
echo ""
echo "Creating required directories..."
mkdir -p data/WebP
mkdir -p data/chroma_db
mkdir -p logs
echo -e "${GREEN}✓${NC} Directories created"

# Check for .env file
echo ""
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠${NC} .env file not found"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠${NC} Please edit .env and add your OpenAI API key"
    echo "   Run: nano .env"
else
    echo -e "${GREEN}✓${NC} .env file exists"
fi

# Check for data files
echo ""
echo "Checking data files..."
DATA_COMPLETE=true

if [ ! -f "data/ABV Final Floorplans.pdf" ]; then
    echo -e "${YELLOW}⚠${NC} PDF file not found: data/ABV Final Floorplans.pdf"
    DATA_COMPLETE=false
fi

WEBP_COUNT=$(find data/WebP -name "*Rev11*.webp" 2>/dev/null | wc -l)
if [ "$WEBP_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠${NC} No WebP images found in data/WebP/"
    DATA_COMPLETE=false
else
    echo -e "${GREEN}✓${NC} Found $WEBP_COUNT WebP images"
fi

# Final instructions
echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""

if [ "$DATA_COMPLETE" = false ]; then
    echo -e "${YELLOW}⚠ NEXT STEPS:${NC}"
    echo "1. Add your data files:"
    echo "   - Place PDF in: data/ABV Final Floorplans.pdf"
    echo "   - Place images in: data/WebP/"
    echo ""
    echo "2. Edit .env and add your OpenAI API key:"
    echo "   nano .env"
    echo ""
    echo "3. Run data ingestion:"
    echo "   python ingest_data.py --reset"
    echo ""
    echo "4. Start the server:"
    echo "   python app.py"
else
    echo -e "${GREEN}✓${NC} All data files are in place"
    echo ""
    echo -e "${YELLOW}⚠ NEXT STEPS:${NC}"
    echo "1. Make sure your OpenAI API key is set in .env"
    echo ""
    echo "2. Run data ingestion:"
    echo "   python ingest_data.py --reset"
    echo ""
    echo "3. Start the server:"
    echo "   python app.py"
    echo ""
    echo "4. Run tests (optional):"
    echo "   pytest tests/test_chat.py -v"
fi

echo ""
echo "For detailed documentation, see:"
echo "  - README.md (setup and usage)"
echo "  - DESIGN.md (architecture)"
echo "  - PROJECT_STRUCTURE.md (file organization)"
echo ""
echo "================================================"