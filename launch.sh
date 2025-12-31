#!/bin/bash
# Launcher script for Streamlit dashboards

# Add Python bin to PATH
export PATH="$HOME/Library/Python/3.9/bin:$PATH"

# Stop any existing streamlit
EXISTING=$(lsof -ti:8501)
if [ ! -z "$EXISTING" ]; then
    echo "Stopping existing Streamlit process..."
    kill $EXISTING 2>/dev/null
    sleep 1
fi

# Menu
echo "================================"
echo "Pairing Dashboard Launcher"
echo "================================"
echo ""
echo "Select dashboard to launch:"
echo ""
echo "1) Unified Dashboard (Pairing Explorer + QA Workbench) ⭐ RECOMMENDED"
echo "2) Main Dashboard (dashboard_with_maps.py)"
echo "3) QA Workbench (qa_workbench.py)"
echo "4) QA Annotations (qa_annotations.py)"
echo "5) Exit"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo "Launching Unified Dashboard..."
        python3 -m streamlit run unified_dashboard.py
        ;;
    2)
        echo "Launching Main Dashboard..."
        python3 -m streamlit run dashboard_with_maps.py
        ;;
    3)
        echo "Launching QA Workbench..."
        python3 -m streamlit run qa_workbench.py
        ;;
    4)
        echo "Launching QA Annotations..."
        python3 -m streamlit run qa_annotations.py
        ;;
    5)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
