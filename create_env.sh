#!/bin/bash

# Navigate to the specified directory
cd /Czentrix/apps/TE_dashboard_ui/

# Store the current directory's virtual environment binary path in a variable
cdir="$(pwd)/venv/bin/"

# Print the virtual environment directory for debugging purposes
echo "Virtual environment directory: $cdir"

# Create a virtual environment named 'venv' using Python 3
echo "Creating virtual environment..."
python3 -m venv venv
# Alternatively, create the virtual environment using a specific Python interpreter
virtualenv venv -p /opt/python3.6.7/bin/python3
echo "Virtual environment created."

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip to the latest version
pip install --upgrade pip

# Install the required packages listed in requirements.txt
echo "Installing requirements..."
pip install -r requirements.txt
echo "Requirements installed."

# Define the directory path and file name for the Streamlit configuration
directory="/Czentrix/apps/TE_dashboard_ui/.streamlit"
filename="config.toml"

# Create the directory if it doesn't exist
mkdir -p "$directory"

# Define the path for the main data directory
main_data_path_dit='/var/log/czentrix/TE_dashboard/'

# Create the main data directory if it doesn't exist
mkdir -p "$main_data_path_dit"

# Define the content of the config.toml file
config_content="[theme]
base=\"light\"
textColor=\"#0a0a0a\"

[server]
port = 8511
"

# Write the content to the config.toml file
echo "$config_content" > "$directory/$filename"

# Confirm that the config.toml file has been created successfully
echo "Config.toml file has been created successfully."


