#!/usr/bin/env python3

import os
import subprocess
import shutil
import zipfile
import requests
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

# Change to the script directory
os.chdir(SCRIPT_DIR)

# Download the dataset
zip_path = SCRIPT_DIR / "food-ingredients-and-recipe-dataset-with-images.zip"
url = "https://www.kaggle.com/api/v1/datasets/download/pes12017000148/food-ingredients-and-recipe-dataset-with-images"

print(f"Downloading dataset from {url}...")
response = requests.get(url, stream=True)
with open(zip_path, 'wb') as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)

# Remove archive directory if it exists
archive_dir = SCRIPT_DIR / "db"
if archive_dir.exists():
    print(f"Removing existing archive directory: {archive_dir}")
    shutil.rmtree(archive_dir)

# Extract the zip file
print(f"Extracting {zip_path} to {archive_dir}")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(archive_dir)

# Remove the zip file
print("Cleaning up...")
os.remove(zip_path)

print("Done!") 

# rename file 
# Rename the CSV file
original_csv = archive_dir / "Food Ingredients and Recipe Dataset with Image Name Mapping.csv"
new_csv = archive_dir / "raw_recipes.csv"

if original_csv.exists():
    print(f"Renaming {original_csv.name} to {new_csv.name}")
    shutil.move(original_csv, new_csv)
else:
    print(f"Warning: Could not find {original_csv.name}")


