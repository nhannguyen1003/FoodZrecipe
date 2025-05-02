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

# Create the archive directory if it doesn't exist
archive_dir = SCRIPT_DIR / "db"
archive_dir.mkdir(parents=True, exist_ok=True)

# Extract the zip file
print(f"Extracting {zip_path} to {archive_dir}")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(archive_dir)

# Remove the zip file
print("Cleaning up downloaded zip file...")
os.remove(zip_path)

print("Extraction completed!")

# Rename the CSV file
original_csv = archive_dir / "Food Ingredients and Recipe Dataset with Image Name Mapping.csv"
new_csv = archive_dir / "raw_recipes.csv"

if original_csv.exists():
    print(f"Renaming {original_csv.name} to {new_csv.name}")
    shutil.move(original_csv, new_csv)
else:
    print(f"Warning: Could not find {original_csv.name}")

# Copy food images to backend static directory
source_images_dir = archive_dir / "Food Images" / "Food Images"
target_images_dir = Path(SCRIPT_DIR).parent / "backend" / "static" / "food-images"

# Create the target directory if it doesn't exist
target_images_dir.mkdir(parents=True, exist_ok=True)

if source_images_dir.exists():
    print(f"Copying food images to {target_images_dir}")
    
    # Count total files for progress reporting
    total_files = sum(1 for _ in source_images_dir.glob('*.*'))
    copied_files = 0
    
    # Copy all image files, overwriting any duplicates
    for image_file in source_images_dir.glob('*.*'):
        if image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            target_path = target_images_dir / image_file.name
            shutil.copy2(image_file, target_path)
            copied_files += 1
            
            # Print progress every 100 files
            if copied_files % 100 == 0 or copied_files == total_files:
                print(f"Copied {copied_files}/{total_files} images")
    
    print(f"Successfully copied {copied_files} images to backend/static/food-images")
    
    # Delete the original Food Images directory after successful copy
    parent_images_dir = archive_dir / "Food Images"
    if parent_images_dir.exists():
        print(f"Deleting original images directory: {parent_images_dir}")
        shutil.rmtree(parent_images_dir)
        print("Original images directory deleted successfully")
else:
    print(f"Warning: Could not find images directory at {source_images_dir}")


