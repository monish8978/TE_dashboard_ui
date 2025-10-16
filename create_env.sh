#!/bin/bash
# ==========================================================
# 🚀 TE Dashboard Auto Setup Script (CentOS / AlmaLinux)
# ==========================================================
set -euo pipefail

# -----------------------------
# Configuration Variables
# -----------------------------
APP_DIR="/Czentrix/apps/TE_dashboard_ui"
VENV_DIR="$APP_DIR/venv"
PYTHON_PATH="/usr/bin/python3"
STREAMLIT_DIR="$APP_DIR/.streamlit"
CONFIG_FILE="$STREAMLIT_DIR/config.toml"
LOG_DIR="/var/log/czentrix/TE_dashboard"
SERVICE_NAME="TE-dash"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
HEALTH_CHECK_FILE="$APP_DIR/service_check.py"
CRON_JOB="*/2 * * * * ${VENV_DIR}/bin/python ${HEALTH_CHECK_FILE}"
LOG_FILE="/var/log/czentrix/te_dashboard_setup.log"
SETTINGS_FILE="$APP_DIR/settings.py"

# -----------------------------
# Logging Setup
# -----------------------------
mkdir -p "$(dirname "$LOG_FILE")"
exec > >(tee -a "$LOG_FILE") 2>&1

# -----------------------------
# Step 0: Detect Package Manager & Install System Dependencies
# -----------------------------
if command -v dnf >/dev/null 2>&1; then
    PKG_MANAGER="dnf"
elif command -v yum >/dev/null 2>&1; then
    PKG_MANAGER="yum"
else
    echo "❌ No supported package manager found (dnf/yum)."
    exit 1
fi

echo "📦 Installing system packages via $PKG_MANAGER..."
sudo $PKG_MANAGER install -y python3 python3-virtualenv gcc >/dev/null
echo "✅ System packages installed."

# -----------------------------
# Step 1: Detect Server IP and Update settings.py
# -----------------------------
# Detect server IP automatically
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="127.0.0.1"
fi
echo "🌐 Using server IP: $SERVER_IP"

# Update settings.py dynamically
cat <<EOF > "$SETTINGS_FILE"
# ==========================================================
# 🌐 Server and API Configuration
# ==========================================================
# This section defines all server URLs and API endpoints that the
# dashboard will communicate with for fetching data, logging in, etc.
# Keeping these values centralized allows easy updates if the server
# or network configuration changes.

# Base IP or domain of the main application server.
# Used as the root URL for login and primary server requests.
ip = "http://$SERVER_IP"

# API endpoint for fetching general or overall dashboard data.
# Typically used to display aggregated metrics and performance stats.
api_end_url = "http://$SERVER_IP:5000/get-data"

# API endpoint for fetching comparative data.
# Used when comparing metrics between two time periods, campaigns, or agents.
cmp_api_end_url = "http://$SERVER_IP:5000/get-data-cmp"

# API endpoint for retrieving agent-specific data.
# Includes information like call counts, performance, and activity.
agent_api_end_url = "http://$SERVER_IP:5000/get-data-agent"

# API endpoint for fetching available campaign names.
# The response populates dropdown lists or filter menus for campaign selection.
camp_api_url = "http://$SERVER_IP/apps/czAppHandler.php"

# Login URL for the TE dashboard or related web interface.
# Constructed dynamically by appending the base IP to the root path.
login_url = ip + "/"

# ==========================================================
# 📁 Log File Paths
# ==========================================================
# This section defines file paths used for application logging.
# Logs are essential for monitoring system behavior and debugging issues.

# Main log file for the dashboard application.
# Stores key events, information logs, and error traces.
main_log_path = "/var/log/czentrix/TE_dashboard/main.log"

# Log file specifically for monitoring UI service health.
# Used by background checks to ensure the dashboard frontend is responsive.
log_path_check_service_ui = "/var/log/czentrix/TE_dashboard/service_check_ui.log"

# ==========================================================
# 📂 Directory Paths for Data and Filters
# ==========================================================
# Defines directory paths for filters and CSV data used in reports.

# Directory to store filter configuration files.
# These are used to apply user-selected filters in dashboard reports.
filter_path = "/var/log/czentrix/TE_dashboard/filter/"

# Directory for saving historical data in CSV format.
# Used for generating downloadable reports and trend analysis.
download_csv_row_data = "/var/log/czentrix/TE_dashboard/download_csv_row_data/hitorical_data/"

# (Optional) Directory for saving live (real-time) CSV data.
# Uncomment and configure if live download functionality is needed.
# download_csv_live_current_row_data = "/var/log/czentrix/TE_dashboard/download_csv_row_data/live_data/"

# Company logo URL displayed on the dashboard UI.
# Ensures consistent branding across all interfaces.
logo_url = "https://www.c-zentrix.com/images/C-Zentrix-logo-white.png"

# ==========================================================
# 📊 Dashboard Settings
# ==========================================================
# Configurations related to UI presentation, available dashboards,
# and dashboard behavior.

# List of available dashboards for users to switch between.
# Each dashboard represents a separate data visualization view.
dashboard_names_list = ["Telephony Dashboard", "Campaign Details Dashboard"]

# Name of the dashboard service.
# Helps identify the service in logs or monitoring systems.
SERVICE_NAME = "TE-dash"

# Dashboard auto-refresh time interval (in milliseconds).
# Determines how frequently the dashboard refreshes data automatically.
# 50,000 ms = 50 seconds
dashboard_reload_time = 50000

EOF
echo "✅ settings.py updated with server IP"

# -----------------------------
# Step 2: Navigate to project directory
# -----------------------------
cd "$APP_DIR" || { echo "❌ Application directory $APP_DIR not found"; exit 1; }
echo "📂 Working directory: $(pwd)"

# -----------------------------
# Step 3: Virtual Environment
# -----------------------------
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR" || virtualenv "$VENV_DIR" -p "$PYTHON_PATH"
    echo "✅ Virtual environment created."
else
    echo "🔄 Virtual environment exists. Reusing."
fi
source "$VENV_DIR/bin/activate"
pip install --upgrade pip >/dev/null
echo "✅ Pip upgraded."

# -----------------------------
# Step 4: Python Dependencies
# -----------------------------
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt >/dev/null
    echo "✅ Dependencies installed."
else
    echo "⚠️  requirements.txt not found. Skipping."
fi

# -----------------------------
# Step 5: Streamlit Configuration
# -----------------------------
mkdir -p "$STREAMLIT_DIR" "$LOG_DIR"
cat > "$CONFIG_FILE" <<EOL
[theme]
base="light"
textColor="#0a0a0a"

[server]
port = 8511
EOL
echo "✅ Streamlit config created at $CONFIG_FILE"

# -----------------------------
# Step 6: Systemd Service
# -----------------------------
echo "🧠 Configuring systemd service $SERVICE_NAME..."
if [ -f "$SERVICE_FILE" ]; then
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        sudo systemctl restart "$SERVICE_NAME"
        echo "🔄 Service restarted."
    else
        sudo systemctl start "$SERVICE_NAME"
        echo "🟡 Service started."
    fi
else
    sudo tee "$SERVICE_FILE" >/dev/null <<EOL
[Unit]
Description=Telephony Dashboard Service
After=network.target

[Service]
WorkingDirectory=$APP_DIR
ExecStart=$VENV_DIR/bin/uvicorn app:app --host 0.0.0.0 --port 8511 --workers 4
Restart=always
RestartSec=5
Environment="PATH=$VENV_DIR/bin:$PATH"

[Install]
WantedBy=multi-user.target
EOL
    sudo chmod 644 "$SERVICE_FILE"
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    sudo systemctl restart "$SERVICE_NAME"
    echo "✅ Service created and started."
fi

# -----------------------------
# Step 7: Cron Job for Health Check
# -----------------------------
if crontab -l 2>/dev/null | grep -Fq "$CRON_JOB"; then
    echo "🕒 Cron job exists."
else
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added."
fi

# -----------------------------
# Setup Completed
# -----------------------------
echo "=========================================================="
echo "🎉 TE Dashboard setup completed!"
echo "Service      : $SERVICE_NAME"
echo "Port         : 8511"
echo "Log Directory: $LOG_DIR"
echo "Cron Job     : Every 2 minutes"
echo "Setup Log    : $LOG_FILE"
echo "=========================================================="
