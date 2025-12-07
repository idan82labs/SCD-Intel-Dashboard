#!/bin/bash
# SCD Intel Dashboard - Setup Script

set -e

echo "Setting up SCD Intel Dashboard..."

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo ""
    echo "ERROR: backend/.env not found!"
    echo ""
    echo "Create backend/.env with your API keys:"
    echo "  ANTHROPIC_API_KEY=your-key"
    echo "  EXA_API_KEY=your-key"
    echo "  SAM_GOV_API_KEY=your-key"
    echo "  SEC_EDGAR_CONTACT_EMAIL=your-email@example.com"
    echo ""
    exit 1
fi

# Create frontend .env.local
cat > frontend/.env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
echo "Created frontend/.env.local"

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "Setup complete!"
echo ""
echo "To run the app, open two terminal windows:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd $(pwd)/backend && python -m app.main"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd $(pwd)/frontend && npm run dev"
echo ""
echo "Then open http://localhost:3000"
