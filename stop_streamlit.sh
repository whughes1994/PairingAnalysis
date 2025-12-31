#!/bin/bash
# Stop any Streamlit process running on port 8501

echo "Checking for Streamlit processes on port 8501..."

PIDS=$(lsof -ti:8501)

if [ -z "$PIDS" ]; then
    echo "✅ No processes found on port 8501"
    exit 0
fi

echo "Found processes: $PIDS"

# Show what's running
echo ""
echo "Process details:"
ps -p $PIDS -o pid,command

echo ""
read -p "Kill these processes? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    kill $PIDS
    sleep 1

    # Check if killed
    REMAINING=$(lsof -ti:8501)

    if [ -z "$REMAINING" ]; then
        echo "✅ Port 8501 is now free"
    else
        echo "⚠️  Some processes still running. Force killing..."
        kill -9 $REMAINING
        echo "✅ Port 8501 is now free (force killed)"
    fi
else
    echo "Cancelled. No processes killed."
fi
