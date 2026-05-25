#!/bin/bash

echo "Starting TE Dashboard setup..."

# =====================================================
# Go to project directory
# =====================================================
cd /Czentrix/apps/TE_dashboard_ui/ || exit

# Store virtual environment path
cdir="$(pwd)/venv/bin/"
echo "Virtual environment directory: $cdir"

# =====================================================
# Create virtual environment
# =====================================================
echo "Creating virtual environment..."

python3 -m venv venv

# If specific python needed
virtualenv venv -p /opt/python3.6.7/bin/python3

echo "Virtual environment created."

# =====================================================
# Activate virtual environment
# =====================================================
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt
echo "Requirements installed."

# =====================================================
# Create Streamlit config
# =====================================================
directory="/Czentrix/apps/TE_dashboard_ui/.streamlit"
filename="config.toml"

mkdir -p "$directory"

config_content="[theme]
base=\"light\"
textColor=\"#0a0a0a\"

[server]
port = 8511
"

echo "$config_content" > "$directory/$filename"

echo "config.toml created successfully."

# =====================================================
# Create main log/data directory
# =====================================================
main_data_path_dit='/var/log/czentrix/TE_dashboard/'
mkdir -p "$main_data_path_dit"

echo "Log directory created."

# =====================================================
# Add CRON job automatically
# =====================================================

echo "Adding cron job..."

cron_job="*/5 * * * * /Czentrix/apps/TE_dashboard_ui/venv/bin/python /Czentrix/apps/TE_dashboard_ui/service_check.py"

# Check if cron already exists
crontab -l 2>/dev/null | grep -F "$cron_job" > /dev/null

if [ $? -eq 0 ]; then
    echo "Cron job already exists. Skipping..."
else
    (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
    echo "Cron job added successfully."
fi

echo "Setup completed successfully."