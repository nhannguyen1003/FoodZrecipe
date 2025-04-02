#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

curl -L -o "$SCRIPT_DIR/food-ingredients-and-recipe-dataset-with-images.zip" \
  https://www.kaggle.com/api/v1/datasets/download/pes12017000148/food-ingredients-and-recipe-dataset-with-images

rm -rf "$SCRIPT_DIR/archive"

unzip "$SCRIPT_DIR/food-ingredients-and-recipe-dataset-with-images.zip" -d "$SCRIPT_DIR/archive"

rm "$SCRIPT_DIR/food-ingredients-and-recipe-dataset-with-images.zip"
