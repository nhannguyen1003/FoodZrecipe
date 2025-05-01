#!/bin/bash

# Set the script to exit immediately if any command fails
set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "=== Initializing Recipe Data ==="

# Step 1: Download raw data from Kaggle
echo "Downloading raw data from Kaggle..."
python3 "$SCRIPT_DIR/get_data_from_kaggle.py"

# Step 2: Transform the raw data
echo "Transforming raw data..."
python3 "$SCRIPT_DIR/get_transformed_data.py"

echo "=== Data initialization complete! ==="
