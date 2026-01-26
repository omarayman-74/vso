#!/bin/bash

# Eshtri Aqar Chatbot - Quick Setup Script

echo "=========================================="
echo "Eshtri Aqar Chatbot - Setup"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file with your credentials:"
    echo "   - OPENAI_API_KEY"
    echo "   - DB_USER"
    echo "   - DB_PASSWORD"
    echo "   - DB_HOST"
    echo ""
    echo "The credentials from your notebook are:"
    echo "OPENAI_API_KEY=your_openai_api_key"
    echo "DB_USER=your_db_user"
    echo "DB_PASSWORD=your_db_password"
    echo "DB_HOST=your_db_host"
    echo ""
    read -p "Press Enter after you've updated .env file..."
else
    echo "✅ .env file already exists"
fi

echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To start the application:"
echo "  uvicorn main:app --reload"
echo ""
echo "Then open: http://localhost:8000"
echo ""
echo "To deploy to Render:"
echo "  1. Push to GitHub"
echo "  2. Connect repo in Render dashboard"
echo "  3. Add environment variables"
echo "  4. Deploy!"
echo ""
echo "See README.md for detailed instructions."
echo ""
