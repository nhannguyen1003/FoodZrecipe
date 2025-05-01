# TODO: Implement recipe-specific repository operations
from typing import List, Optional, Any, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
import numpy as np
import faiss
import json
from backend.models.recipe import Recipe
from backend.schemas.recipe import RecipeCreate, RecipeUpdate
from database.repositories.base_repository import BaseRepository
from config import settings

class RecipeRepository(BaseRepository[Recipe, RecipeCreate, RecipeUpdate]):
    def __init__(self, model):
        super().__init__(model)
        self.text_index = None
        self.image_index = None
        self.recipe_ids = []  # To maintain mapping between FAISS indices and recipe IDs
        self.text_recipe_map = {}
        self.image_recipe_map = {}
        
        # Get LSH parameters from settings
        self.vector_dim = getattr(settings, 'LSH_VECTOR_DIM', 128)
        self.hash_bits = getattr(settings, 'LSH_HASH_BITS', 32)
        
    def get_by_user_id(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[Recipe]:
        return db.query(Recipe).filter(Recipe.user_id == user_id).offset(skip).limit(limit).all()
    
    def get_by_category(self, db: Session, *, category: str, skip: int = 0, limit: int = 100) -> List[Recipe]:
        return db.query(Recipe).filter(Recipe.categories.contains([category])).offset(skip).limit(limit).all()
    
    def search_by_text(self, db: Session, *, query: str, skip: int = 0, limit: int = 100) -> List[Recipe]:
        """
        Implements PostgreSQL full-text search
        """
        search_query = f"%{query}%"
        return db.query(Recipe).filter(
            or_(
                Recipe.title.ilike(search_query),
                Recipe.description.ilike(search_query),
                func.array_to_string(Recipe.ingredients, ' ').ilike(search_query),
                func.array_to_string(Recipe.instructions, ' ').ilike(search_query)
            )
        ).offset(skip).limit(limit).all()
    
    def load_faiss_indices(self, db: Session) -> None:
        """
        Load all recipe vectors into FAISS indices for fast similarity search
        This should be called at application startup or when recipes are updated
        """
        recipes = db.query(Recipe).all()
        
        # Reset recipe ID mapping
        self.recipe_ids = [recipe.id for recipe in recipes]
        
        # Get text feature vectors (filtering out None values)
        text_vectors = []
        text_recipe_ids = []
        for i, recipe in enumerate(recipes):
            if recipe.text_feature_vector:
                text_vectors.append(np.array(recipe.text_feature_vector, dtype=np.float32))
                text_recipe_ids.append(i)
        
        # Get image feature vectors (filtering out None values)
        image_vectors = []
        image_recipe_ids = []
        for i, recipe in enumerate(recipes):
            if recipe.image_feature_vector:
                image_vectors.append(np.array(recipe.image_feature_vector, dtype=np.float32))
                image_recipe_ids.append(i)
        
        # Create and populate text index if we have vectors
        if text_vectors:
            text_vectors = np.array(text_vectors)
            d = text_vectors.shape[1]  # dimensionality of vectors
            
            # Build LSH index for text search using settings parameters
            self.text_index = faiss.IndexLSH(d, self.hash_bits)
            self.text_index.add(text_vectors)
            self.text_recipe_map = {i: self.recipe_ids[rid] for i, rid in enumerate(text_recipe_ids)}
        
        # Create and populate image index if we have vectors
        if image_vectors:
            image_vectors = np.array(image_vectors)
            d = image_vectors.shape[1]  # dimensionality of vectors
            
            # Build LSH index for image search using settings parameters
            self.image_index = faiss.IndexLSH(d, self.hash_bits)
            self.image_index.add(image_vectors)
            self.image_recipe_map = {i: self.recipe_ids[rid] for i, rid in enumerate(image_recipe_ids)}
    
    def generate_feature_vector(self, db: Session, *, recipe_id: int, text_data: str, update_db: bool = True) -> np.ndarray:
        """
        Generate text feature vector for a recipe and optionally update the database
        
        This is a simplified implementation. In a real application, you'd use 
        more sophisticated NLP techniques like sentence embeddings.
        """
        # Import here to avoid circular imports
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        # Get all recipe texts for the vectorizer
        all_recipes = db.query(Recipe).all()
        all_texts = [
            f"{r.title} {r.description or ''} {' '.join(r.ingredients)} {' '.join(r.instructions)}"
            for r in all_recipes
        ]
        
        # Create and fit the vectorizer - use vector_dim from settings
        vectorizer = TfidfVectorizer(max_features=self.vector_dim)
        vectorizer.fit(all_texts)
        
        # Transform the input text
        vector = vectorizer.transform([text_data]).toarray()[0]
        vector = vector.astype(np.float32)
        
        if update_db:
            recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
            if recipe:
                recipe.text_feature_vector = vector.tolist()
                db.commit()
                
                # Update the FAISS index
                if self.text_index:
                    self.text_index.add(np.array([vector]))
                    # Update the recipe ID mapping as well
                    next_idx = self.text_index.ntotal - 1
                    self.text_recipe_map[next_idx] = recipe_id
        
        return vector
    
    def generate_image_feature_vector(self, db: Session, *, recipe_id: int, image_path: str, update_db: bool = True) -> np.ndarray:
        """
        Generate image feature vector for a recipe and optionally update the database
        
        This is a simplified implementation. In a real application, you'd use 
        pretrained models like ResNet or ViT for image feature extraction.
        """
        # Import here to avoid circular imports
        from PIL import Image
        import numpy as np
        
        try:
            # Load and resize image
            img = Image.open(image_path).resize((224, 224))
            img_array = np.array(img)
            
            # Simple feature extraction (average color channels)
            # In a real application, use a proper CNN for feature extraction
            features = np.mean(img_array, axis=(0, 1))
            features = features / 255.0  # Normalize
            
            # Pad to fixed size if needed - use vector_dim from settings
            padded_features = np.zeros(self.vector_dim, dtype=np.float32)
            padded_features[:len(features)] = features
            
            if update_db:
                recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
                if recipe:
                    recipe.image_feature_vector = padded_features.tolist()
                    db.commit()
                    
                    # Update the FAISS index
                    if self.image_index:
                        self.image_index.add(np.array([padded_features]))
                        # Update the recipe ID mapping as well
                        next_idx = self.image_index.ntotal - 1
                        self.image_recipe_map[next_idx] = recipe_id
            
            return padded_features
        except Exception as e:
            print(f"Error generating image feature vector: {e}")
            return np.zeros(self.vector_dim, dtype=np.float32)
    
    def update_feature_vectors(self, db: Session, *, recipe_id: int) -> None:
        """Update feature vectors for a recipe"""
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            return
            
        # Generate text feature vector
        text_data = f"{recipe.title} {recipe.description or ''} {' '.join(recipe.ingredients)} {' '.join(recipe.instructions)}"
        self.generate_feature_vector(db, recipe_id=recipe_id, text_data=text_data)
        
        # Generate image feature vector if image exists
        if recipe.image_url:
            self.generate_image_feature_vector(db, recipe_id=recipe_id, image_path=recipe.image_url)
    
    def search_by_text_vector(self, db: Session, *, query_vector: np.ndarray, k: int = 10) -> List[Recipe]:
        """
        Search recipes by text feature vector using FAISS
        """
        if self.text_index is None or self.text_index.ntotal == 0:
            return []
            
        # Make sure vector is the right shape
        query_vector = query_vector.reshape(1, -1).astype(np.float32)
        
        # Search the FAISS index
        distances, indices = self.text_index.search(query_vector, k)
        
        # Convert FAISS indices to recipe IDs
        recipe_ids = [self.text_recipe_map[int(idx)] for idx in indices[0] if idx >= 0 and int(idx) in self.text_recipe_map]
        
        # Fetch recipes from database
        if recipe_ids:
            recipes = db.query(Recipe).filter(Recipe.id.in_(recipe_ids)).all()
            
            # Sort recipes in the same order as the search results
            recipe_dict = {recipe.id: recipe for recipe in recipes}
            sorted_recipes = [recipe_dict[rid] for rid in recipe_ids if rid in recipe_dict]
            
            return sorted_recipes
        return []
    
    def search_by_image_vector(self, db: Session, *, query_vector: np.ndarray, k: int = 10) -> List[Recipe]:
        """
        Search recipes by image feature vector using FAISS
        """
        if self.image_index is None or self.image_index.ntotal == 0:
            return []
            
        # Make sure vector is the right shape
        query_vector = query_vector.reshape(1, -1).astype(np.float32)
        
        # Search the FAISS index
        distances, indices = self.image_index.search(query_vector, k)
        
        # Convert FAISS indices to recipe IDs
        recipe_ids = [self.image_recipe_map[int(idx)] for idx in indices[0] if idx >= 0 and int(idx) in self.image_recipe_map]
        
        # Fetch recipes from database
        if recipe_ids:
            recipes = db.query(Recipe).filter(Recipe.id.in_(recipe_ids)).all()
            
            # Sort recipes in the same order as the search results
            recipe_dict = {recipe.id: recipe for recipe in recipes}
            sorted_recipes = [recipe_dict[rid] for rid in recipe_ids if rid in recipe_dict]
            
            return sorted_recipes
        return []
    
    def search_by_text_query(self, db: Session, *, query: str, k: int = 10) -> List[Recipe]:
        """
        Search recipes by text query
        1. Convert text query to feature vector
        2. Use FAISS to find similar recipes
        """
        # Convert query to feature vector
        query_vector = self.generate_feature_vector(db, recipe_id=-1, text_data=query, update_db=False)
        
        # Search using the vector
        return self.search_by_text_vector(db, query_vector=query_vector, k=k)
    
    def search_by_image_path(self, db: Session, *, image_path: str, k: int = 10) -> List[Recipe]:
        """
        Search recipes by image path
        1. Convert image to feature vector
        2. Use FAISS to find similar recipes
        """
        # Convert image to feature vector
        query_vector = self.generate_image_feature_vector(db, recipe_id=-1, image_path=image_path, update_db=False)
        
        # Search using the vector
        return self.search_by_image_vector(db, query_vector=query_vector, k=k)
    
    def hybrid_search(self, db: Session, *, text_query: str = None, image_path: str = None, k: int = 10) -> List[Recipe]:
        """
        Perform hybrid search using both text and image if available
        """
        results = []
        
        # Text search
        if text_query:
            text_results = self.search_by_text_query(db, query=text_query, k=k)
            results.extend(text_results)
            
        # Image search
        if image_path:
            image_results = self.search_by_image_path(db, image_path=image_path, k=k)
            results.extend(image_results)
            
        # Remove duplicates and limit to k results
        unique_results = []
        seen_ids = set()
        
        for recipe in results:
            if recipe.id not in seen_ids:
                seen_ids.add(recipe.id)
                unique_results.append(recipe)
                
                if len(unique_results) >= k:
                    break
                    
        return unique_results

recipe_repository = RecipeRepository(Recipe) 