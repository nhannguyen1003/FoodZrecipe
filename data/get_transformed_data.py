from transformers import pipeline
import pandas as pd 
import numpy as np 
import os
import pathlib
from tqdm import tqdm
import json 

def get_current_dir():
    """
    Get the directory where the current script is located.
    
    Returns:
        pathlib.Path: Path object representing the directory of the current script
    """
    return pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

def get_data_path():
    current_dir = get_current_dir()
    """
    Get the data directory by going up one level from the current directory
    and then into the archive folder.
    
    Returns:
        pathlib.Path: Path object representing the data directory
    """
    return current_dir / "db" / "raw_recipes.csv"

def get_prompt(title):
    template= """
    Title: {title}
    """
    return template.format(title=title)


def get_raw_data(df):
    df = df.drop('Unnamed: 0', axis=1)
    df['prompt'] = df.apply(lambda row: get_prompt(row['Title']), axis=1)
    return df.to_dict(orient='records')


def get_output_file_path(overwrite= True):
    current_dir = get_current_dir()
    path = current_dir / "db" / "sample_recipes_cleaned.json"
    if overwrite:
        mode = 'w+'
    else:
        mode = 'r'
    with open(path, mode) as f:
        pass 
    return path 

def put_data(row, path):
    with open(path, 'a') as f:
        json.dump(row, f)
        f.write('\n')

if __name__ == "__main__":
    
    df= pd.read_csv(get_data_path())
    data = get_raw_data(df)
    path = get_output_file_path()


    classifier = pipeline("zero-shot-classification",
                      model="facebook/bart-large-mnli")
    threshold = 0.8
    for row in tqdm(data):
        prompt = row['prompt']
        candidate_labels = [
        "Breakfast", "Lunch", "Dinner", "Snack", "Appetizers", "Side Dishes",
        "Pasta", "Salads", "Soups & Stews", "Casseroles", "Sandwiches & Wraps",
        "Tacos & Quesadillas", "Bowls & Grain Meals", "Stir-Fries", "Baked Goods", "Desserts",
        "Chicken", "Beef", "Pork", "Fish & Seafood", "Vegetarian", "Vegan", "Tofu & Plant-Based",
        "Healthy", "Low-Carb", "Keto", "Sugar-Free", "High-Protein", "Gluten-Free",
        "Instant Pot", "Slow Cooker", "Air Fryer", "Grilled", "Baked", "No-Cook",
        "Quick & Easy", "30-Minute Meals", "Meal Prep", "Kid-Friendly", "Crowd-Pleasing"
        ]
        result = classifier(prompt, candidate_labels, multi_label=True)
        labels = [label for i,label in enumerate(result['labels']) if result['scores'][i] > threshold]
        row['labels'] = labels
        row['Ingredients'] = eval(row['Ingredients'])
        row['Cleaned_Ingredients'] = eval(row['Cleaned_Ingredients'])
        put_data(row, path)



