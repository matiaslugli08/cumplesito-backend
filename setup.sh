#!/bin/bash

# Wishlist API Backend Setup Script

echo "========================================="
echo "Wishlist API Backend Setup"
echo "========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL is not found in PATH. Make sure it's installed."
else
    echo "✅ PostgreSQL found: $(psql --version)"
fi

echo ""
echo "Step 1: Creating virtual environment..."
python3 -m venv venv

echo "✅ Virtual environment created"
echo ""
echo "Step 2: Activating virtual environment..."
source venv/bin/activate

echo "✅ Virtual environment activated"
echo ""
echo "Step 3: Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Dependencies installed"
echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Create your PostgreSQL database:"
echo "   psql -U postgres"
echo "   CREATE DATABASE wishlist_db;"
echo ""
echo "2. Copy and configure .env file:"
echo "   cp .env.example .env"
echo "   # Edit .env with your database credentials"
echo ""
echo "3. Generate a secure SECRET_KEY:"
echo "   python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
echo "   # Copy this to your .env file"
echo ""
echo "4. Run the server:"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
echo ""
echo "5. Visit the API documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "========================================="
