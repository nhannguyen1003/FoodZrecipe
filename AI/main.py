from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uuid
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.post("/search/image")
async def image_search(image: UploadFile = File(...)):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    ext = os.path.splitext(image.filename)[1]  
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        content = await image.read()
        buffer.write(content)
    
    image_url = f"https://upload.wikimedia.org/wikipedia/commons/a/a3/Eq_it-na_pizza-margherita_sep2005_sml.jpg"
    results = [
        {
            "image": image_url,
            "matchPercentage": 85,
            "ingredients": ["Ingredient X", "Ingredient Y", "Ingredient Z", "Ingredient W", "Ingredient V", "Ingredient U", "Ingredient X", "Ingredient Y", "Ingredient Z", "Ingredient W", "Ingredient V", "Ingredient U", "Ingredient X", "Ingredient Y", "Ingredient Z", "Ingredient W", "Ingredient V", "Ingredient U", "Ingredient X", "Ingredient Y"]
        },
        {
            "image": image_url,
            "matchPercentage": 85,
            "ingredients": ["Ingredient X", "Ingredient Y", "Ingredient Z", "Ingredient W", "Ingredient V", "Ingredient U", "Ingredient X", "Ingredient Y", "Ingredient Z", "Ingredient W", "Ingredient V", "Ingredient U", "Ingredient X", "Ingredient Y", "Ingredient Z", "Ingredient W", "Ingredient V", "Ingredient U", "Ingredient X", "Ingredient Y"]
        }
    ]
    return {"results": results}

@app.get("/search")
async def text_search(q: str):
    results = [
        {
            "image": "https://via.placeholder.com/500x400",
            "matchPercentage": 80,
            "ingredients": ["Ingredient A", "Ingredient B"],
        }
    ]
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
