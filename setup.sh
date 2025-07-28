#!/bin/bash

# Change to the project directory (assuming script is in project root)
cd "$(dirname "$0")" || exit 1

# Create the virtual environment in the project
python3 -m venv coffee_analysis_env

# Activate the virtual environment
source coffee_analysis_env/bin/activate

# Install from requirements
pip install -r requirements.txt

echo "Setup complete! Virtual environment is activated."
echo "To activate it again later, run: source coffee_analysis_env/bin/activate"