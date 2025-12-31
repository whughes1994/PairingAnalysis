#!/bin/bash
# Setup script to add Python bin to PATH for current session
# Run with: source setup_path.sh

export PATH="$HOME/Library/Python/3.9/bin:$PATH"

echo "✅ Added Python bin to PATH for this session"
echo "   You can now use 'streamlit' command directly"
echo ""
echo "To make this permanent, add this to your ~/.zshrc:"
echo "   export PATH=\"\$HOME/Library/Python/3.9/bin:\$PATH\""
