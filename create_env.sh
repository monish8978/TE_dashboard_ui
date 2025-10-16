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
ip = "http://$SERVER_IP"
api_end_url = "http://$SERVER_IP:5000/get-data"
cmp_api_end_url = "http://$SERVER_IP:5000/get-data-cmp"
agent_api_end_url = "http://$SERVER_IP:5000/get-data-agent"
camp_api_url = "http://$SERVER_IP/apps/czAppHandler.php"
login_url = ip + "/"

# ==========================================================
# 📁 Log File Paths
# ==========================================================
main_log_path = "/var/log/czentrix/TE_dashboard/main.log"
log_path_check_service_ui = "/var/log/czentrix/TE_dashboard/service_check_ui.log"

# ==========================================================
# 📂 Directory Paths for Data and Filters
# ==========================================================
filter_path = "/var/log/czentrix/TE_dashboard/filter/"
download_csv_row_data = "/var/log/czentrix/TE_dashboard/download_csv_row_data/hitorical_data/"
# download_csv_live_current_row_data = "/var/log/czentrix/TE_dashboard/download_csv_row_data/live_data/"

logo_url = "https://www.c-zentrix.com/images/C-Zentrix-logo-white.png"

# ==========================================================
# 📊 Dashboard Settings
# ==========================================================
dashboard_names_list = ["Telephony Dashboard", "Campaign Details Dashboard"]
SERVICE_NAME = "TE-dash"
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
