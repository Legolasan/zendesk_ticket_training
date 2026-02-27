#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Zendesk Ticket Analysis System                      ║"
echo "║         Setup Script                                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "🐍 Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo ""
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your credentials!"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Zendesk and AI API credentials"
echo "2. Run 'python migrate.py' to set up the database"
echo "3. Run 'python app.py' to start the webhook receiver"
echo "4. Run 'python dashboard/app.py' to start the dashboard"
echo ""
