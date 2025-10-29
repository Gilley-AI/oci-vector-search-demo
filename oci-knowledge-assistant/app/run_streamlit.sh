#!/bin/bash
# Run Streamlit and show the public Cloud Shell URL

APP_FILE="streamlit_app.py"
PORT=8502

# Start Streamlit in the background
echo "🚀 Starting Streamlit on port $PORT ..."
streamlit run "$APP_FILE" --server.port $PORT --server.address 0.0.0.0 --server.headless true &

# Wait a few seconds for Streamlit to boot
sleep 6

# Try to detect hostname
HOST=$(hostname || echo "cloudshell")

# Print likely URLs
echo
echo "🌐 Try opening one of these in your browser:"
echo "   https://${HOST}-${PORT}.oraclecloudapps.com/"
echo "   http://${HOST}.oraclevcn.com:${PORT}/"
echo
echo "If neither loads, check for a Web Preview button in Cloud Shell, or try another port (e.g., 8502)."
echo
wait
