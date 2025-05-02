# TODO: Implement recipe-specific repository operations
from typing import List, Optional, Any, Dict, Tuple, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, desc, text
import numpy as np
import faiss
import json
from backend.models.recipe import Recipe, recipe_category
from backend.schemas.recipe import RecipeCreate, RecipeUpdate
from database.repositories.base_repository import BaseRepository
from config import settings
from backend.models.category import Category

class RecipeRepository(BaseRepository[Recipe, RecipeCreate, RecipeUpdate]):
    def __init__(self, db: Session):
        super().__init__(Recipe)
        self.db = db
        self.text_index = None
        self.image_index = None
        self.recipe_ids = []  # To maintain mapping between FAISS indices and recipe IDs
        self.text_recipe_map = {}
        self.image_recipe_map = {}
        
        # Get LSH parameters from settings
        self.vector_dim = getattr(settings, 'LSH_VECTOR_DIM', 128)
        self.hash_bits = getattr(settings, 'LSH_HASH_BITS', 32)
        
        # Multi-field indices
        self.title_index = None
        self.ingredients_index = None
        self.instructions_index = None
        self.title_recipe_map = {}
        self.ingredients_recipe_map = {}
        self.instructions_recipe_map = {}
        
        # Multi-field dimensions
        self.title_dim = getattr(settings, 'TITLE_VECTOR_DIM', 64)
        self.ingredients_dim = getattr(settings, 'INGREDIENTS_VECTOR_DIM', 128)
        self.instructions_dim = getattr(settings, 'INSTRUCTIONS_VECTOR_DIM', 256)
        
        # Multi-field hash bits
        self.title_bits = getattr(settings, 'TITLE_HASH_BITS', 32)
        self.ingredients_bits = getattr(settings, 'INGREDIENTS_HASH_BITS', 64)
        self.instructions_bits = getattr(settings, 'INSTRUCTIONS_HASH_BITS', 128)
        
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
        text_data = f"{recipe.title} {recipe.description or ''} {' '.join(recipe.ingredients)} {recipe.instructions}"
        self.generate_feature_vector(db, recipe_id=recipe_id, text_data=text_data)
        
        # Generate image feature vector if image exists
        if recipe.image_url:
            self.generate_image_feature_vector(db, recipe_id=recipe_id, image_path=recipe.image_url)
            
        # Generate field-specific feature vectors
        self.generate_multi_field_vectors(db, recipe_id=recipe_id)
    
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
        
        # Convert indices to recipe IDs
        recipe_ids = [self.text_recipe_map.get(int(idx)) for idx in indices[0] if idx >= 0 and int(idx) in self.text_recipe_map]
        
        # Fetch the recipes
        recipes = db.query(Recipe).filter(Recipe.id.in_(recipe_ids)).all()
        
        # Sort recipes to match the original order from FAISS
        sorted_recipes = []
        for recipe_id in recipe_ids:
            for recipe in recipes:
                if recipe.id == recipe_id:
                    # Convert array instructions to string if needed
                    if recipe.instructions and isinstance(recipe.instructions, list):
                        recipe.instructions = "\n".join(recipe.instructions)
                    sorted_recipes.append(recipe)
                    break
        
        return sorted_recipes
    
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
        
        # Convert indices to recipe IDs
        recipe_ids = [self.image_recipe_map.get(int(idx)) for idx in indices[0] if idx >= 0 and int(idx) in self.image_recipe_map]
        
        # Fetch the recipes
        recipes = db.query(Recipe).filter(Recipe.id.in_(recipe_ids)).all()
        
        # Sort recipes to match the original order from FAISS
        sorted_recipes = []
        for recipe_id in recipe_ids:
            for recipe in recipes:
                if recipe.id == recipe_id:
                    # Convert array instructions to string if needed
                    if recipe.instructions and isinstance(recipe.instructions, list):
                        recipe.instructions = "\n".join(recipe.instructions)
                    sorted_recipes.append(recipe)
                    break
        
        return sorted_recipes
    
    def search_by_text_query(self, db: Session, *, query: str, k: int = 10) -> List[Recipe]:
        """
        Search recipes by text query using feature vectors
        """
        # Generate feature vector for the query text
        # This is a simplified approach - in a real app, you'd use the same NLP model
        # that was used to generate feature vectors for the recipes
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        # Get all recipe texts for the vectorizer
        all_recipes = db.query(Recipe).all()
        all_texts = [
            f"{r.title} {r.description or ''} {' '.join(r.ingredients)} {r.instructions if isinstance(r.instructions, str) else ' '.join(r.instructions)}"
            for r in all_recipes
        ]
        
        # Create and fit the vectorizer
        vectorizer = TfidfVectorizer(max_features=self.vector_dim)
        vectorizer.fit(all_texts)
        
        # Transform the query text
        query_vector = vectorizer.transform([query]).toarray()[0]
        query_vector = query_vector.astype(np.float32)
        
        # Search using the query vector
        results = self.search_by_text_vector(db, query_vector=query_vector, k=k)
        
        # Convert array instructions to string if needed
        for recipe in results:
            if recipe.instructions and isinstance(recipe.instructions, list):
                recipe.instructions = "\n".join(recipe.instructions)
                
        return results
    
    def search_by_image_path(self, db: Session, *, image_path: str, k: int = 10) -> List[Recipe]:
        """
        Search recipes by image path
        1. Extract features from the image
        2. Use FAISS to find similar recipes
        """
        # Generate image feature vector
        query_vector = self.generate_image_feature_vector(db, recipe_id=-1, image_path=image_path, update_db=False)
        
        # Search using the vector
        results = self.search_by_image_vector(db, query_vector=query_vector, k=k)
        
        # Convert array instructions to string if needed
        for recipe in results:
            if recipe.instructions and isinstance(recipe.instructions, list):
                recipe.instructions = "\n".join(recipe.instructions)
                
        return results
    
    def hybrid_search(self, db: Session, *, text_query: str = None, image_path: str = None, k: int = 10) -> List[Recipe]:
        """
        Combines text and image search for a more comprehensive search experience
        
        1. If text query is provided, perform text search
        2. If image path is provided, perform image search
        3. Combine and rank results
        """
        all_results = {}
        
        # Perform text search if query is provided
        if text_query:
            text_results = self.search_by_text_query(db, query=text_query, k=k*2)
            for i, recipe in enumerate(text_results):
                if recipe.id not in all_results:
                    all_results[recipe.id] = {"recipe": recipe, "text_rank": i+1, "image_rank": 999}
                else:
                    all_results[recipe.id]["text_rank"] = i+1
        
        # Perform image search if image is provided
        if image_path:
            image_results = self.search_by_image_path(db, image_path=image_path, k=k*2)
            for i, recipe in enumerate(image_results):
                if recipe.id not in all_results:
                    all_results[recipe.id] = {"recipe": recipe, "text_rank": 999, "image_rank": i+1}
                else:
                    all_results[recipe.id]["image_rank"] = i+1
        
        # Sort and return top k recipes
        # Lower combined rank (text_rank + image_rank) is better
        results = [item["recipe"] for item in sorted(all_results.values(), 
                                         key=lambda x: x["text_rank"] + x["image_rank"])[:k]]
        
        # Convert array instructions to string if needed (should already be handled by the sub-methods)
        for recipe in results:
            if recipe.instructions and isinstance(recipe.instructions, list):
                recipe.instructions = "\n".join(recipe.instructions)
                
        return results

    def advanced_search(self, db: Session, *, query: str, categories: List[str] = None, 
                       sort_by: str = "relevance", skip: int = 0, limit: int = 100) -> List[Recipe]:
        """
        Advanced search with filtering and sorting options
        
        Args:
            query: Text search query
            categories: Optional list of categories to filter by
            sort_by: Sorting option - relevance, newest, or popular
            skip: Pagination offset
            limit: Number of results to return
        """
        # Import at the function level to avoid scope issues
        from sqlalchemy import func, or_
        
        search_query = f"%{query}%"
        
        # Start with base query
        base_query = db.query(Recipe).filter(
            or_(
                Recipe.title.ilike(search_query),
                Recipe.description.ilike(search_query),
                func.array_to_string(Recipe.ingredients, ' ').ilike(search_query),
                func.array_to_string(Recipe.instructions, ' ').ilike(search_query)
            )
        )
        
        # Apply category filtering if specified
        if categories and len(categories) > 0:
            # Create a condition that checks if any category is in the categories list
            category_conditions = []
            for category in categories:
                # Using the array_to_string function to check if a category exists in the array
                category_conditions.append(func.array_to_string(Recipe.categories, ',').ilike(f'%{category}%'))
            
            # Combine the conditions with OR
            if category_conditions:
                base_query = base_query.filter(or_(*category_conditions))
        
        # Apply sorting
        if sort_by == "newest":
            base_query = base_query.order_by(Recipe.created_at.desc())
        elif sort_by == "popular":
            # This would ideally use a rating or views field. For now, we'll just use ID as a placeholder
            # In a real application, you would have a rating/views field to sort by
            base_query = base_query.order_by(Recipe.id.desc())
        # Default is relevance, which is the order from the text search
        
        # Apply pagination and return results
        results = base_query.offset(skip).limit(limit).all()
        
        # Convert array instructions to string if needed for schema compatibility
        for recipe in results:
            if recipe.instructions and isinstance(recipe.instructions, list):
                recipe.instructions = "\n".join(recipe.instructions)
                
        return results

    def get_all_categories(self, db: Session) -> List[str]:
        """
        Get all distinct categories from recipes in the database
        
        Returns a sorted list of unique categories from all recipes
        """
        # Query for all recipes
        recipes = db.query(Recipe).all()
        
        # Collect all categories
        all_categories = set()
        for recipe in recipes:
            if recipe.categories:
                for category in recipe.categories:
                    all_categories.add(category)
        
        # Return sorted list of unique categories
        return sorted(list(all_categories))

    def create_with_user_id(self, db: Session, obj_in: Union[Dict[str, Any], RecipeCreate], user_id: int) -> Recipe:
        """
        Create a recipe and set the user_id field
        
        Args:
            db: Database session
            obj_in: Recipe data
            user_id: ID of the user creating the recipe
            
        Returns:
            Created Recipe object
        """
        obj_in_data = obj_in.dict() if hasattr(obj_in, "dict") else obj_in
        db_obj = Recipe(**obj_in_data, user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_with_categories(self, obj_in: Dict[str, Any], user_id: int, category_ids: Optional[List[int]] = None) -> Recipe:
        """Create a recipe with categories"""
        # Create recipe without categories first
        obj_in_data = obj_in.copy()
        if "category_ids" in obj_in_data:
            obj_in_data.pop("category_ids")
        
        recipe = self.create_with_user_id(None, obj_in_data, user_id)
        
        # Add categories if provided
        if category_ids:
            self.update_recipe_categories(recipe.id, category_ids)
        
        return recipe
    
    def update_with_categories(self, id: int, obj_in: Dict[str, Any]) -> Recipe:
        """Update a recipe with categories"""
        # Update categories if provided
        category_ids = None
        obj_in_data = obj_in.copy()
        
        if "category_ids" in obj_in_data:
            category_ids = obj_in_data.pop("category_ids")
        
        # Update the recipe
        recipe = self.update(id, obj_in_data)
        
        # Update categories if provided
        if category_ids is not None:
            self.update_recipe_categories(id, category_ids)
        
        return recipe
    
    def update_recipe_categories(self, recipe_id: int, category_ids: List[int]) -> None:
        """Update the categories for a recipe"""
        # Get existing category relationships
        existing_relations = (
            self.db.query(recipe_category)
            .filter(recipe_category.c.recipe_id == recipe_id)
            .all()
        )
        
        # Get existing category IDs
        existing_category_ids = [rel.category_id for rel in existing_relations]
        
        # Categories to add
        to_add = [id for id in category_ids if id not in existing_category_ids]
        
        # Categories to remove
        to_remove = [id for id in existing_category_ids if id not in category_ids]
        
        # Add new relationships
        for category_id in to_add:
            stmt = recipe_category.insert().values(
                recipe_id=recipe_id,
                category_id=category_id
            )
            self.db.execute(stmt)
        
        # Remove old relationships
        if to_remove:
            stmt = recipe_category.delete().where(
                and_(
                    recipe_category.c.recipe_id == recipe_id,
                    recipe_category.c.category_id.in_(to_remove)
                )
            )
            self.db.execute(stmt)
        
        self.db.commit()
    
    def get_with_categories(self, id: int) -> Optional[Recipe]:
        """Get a recipe with its categories"""
        return (
            self.db.query(self.model)
            .options(joinedload(self.model.category_relations))
            .filter(self.model.id == id)
            .first()
        )
    
    def filter_by_category(
        self, 
        category_id: int, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Recipe]:
        """Filter recipes by category"""
        return (
            self.db.query(self.model)
            .join(recipe_category)
            .filter(recipe_category.c.category_id == category_id)
            .order_by(desc(self.model.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def search_with_category_filter(
        self,
        search_query: str,
        limit: int = 10,
        offset: int = 0,
        category_ids: Optional[List[int]] = None,
        sort_by: str = "relevance"
    ) -> Tuple[List[Recipe], int]:
        """Search recipes with optional category filter"""
        # ... existing search code ...
        
        # Start with the base query
        base_query = self.db.query(self.model)
        
        # Apply category filter if provided
        if category_ids:
            base_query = base_query.join(recipe_category).filter(recipe_category.c.category_id.in_(category_ids))
        
        # ... continue with existing search logic ...
        
        return recipes, total_count

    def load_multi_field_indices(self, db: Session) -> None:
        """
        Load field-specific feature vectors into FAISS indices
        """
        recipes = db.query(Recipe).all()
        
        # Reset recipe ID mapping
        self.recipe_ids = [recipe.id for recipe in recipes]
        
        # Title vectors
        title_vectors = []
        title_recipe_ids = []
        for i, recipe in enumerate(recipes):
            if recipe.title_feature_vector:
                title_vectors.append(np.array(recipe.title_feature_vector, dtype=np.float32))
                title_recipe_ids.append(i)
                self.title_recipe_map[i] = recipe.id
        
        # Ingredients vectors
        ingredients_vectors = []
        ingredients_recipe_ids = []
        for i, recipe in enumerate(recipes):
            if recipe.ingredients_feature_vector:
                ingredients_vectors.append(np.array(recipe.ingredients_feature_vector, dtype=np.float32))
                ingredients_recipe_ids.append(i)
                self.ingredients_recipe_map[i] = recipe.id
        
        # Instructions vectors
        instructions_vectors = []
        instructions_recipe_ids = []
        for i, recipe in enumerate(recipes):
            if recipe.instructions_feature_vector:
                instructions_vectors.append(np.array(recipe.instructions_feature_vector, dtype=np.float32))
                instructions_recipe_ids.append(i)
                self.instructions_recipe_map[i] = recipe.id
        
        # Create FAISS indices for each field
        if title_vectors:
            # Convert list of vectors to a 2D numpy array
            title_array = np.vstack(title_vectors)
            
            # Create FAISS index
            self.title_index = faiss.IndexFlatL2(self.title_dim)
            self.title_index.add(title_array)
            
        if ingredients_vectors:
            # Convert list of vectors to a 2D numpy array
            ingredients_array = np.vstack(ingredients_vectors)
            
            # Create FAISS index
            self.ingredients_index = faiss.IndexFlatL2(self.ingredients_dim)
            self.ingredients_index.add(ingredients_array)
            
        if instructions_vectors:
            # Convert list of vectors to a 2D numpy array
            instructions_array = np.vstack(instructions_vectors)
            
            # Create FAISS index
            self.instructions_index = faiss.IndexFlatL2(self.instructions_dim)
            self.instructions_index.add(instructions_array)
    
    def generate_multi_field_vectors(self, db: Session, *, recipe_id: int) -> None:
        """
        Generate field-specific feature vectors for a recipe
        
        Args:
            db: Database session
            recipe_id: ID of the recipe to update
        """
        from backend.services.multi_field_search_service import multi_field_search_service
        
        # Get the recipe
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            return
            
        # Generate embeddings using the multi-field search service
        updated_recipe = multi_field_search_service.generate_embeddings_for_recipe(recipe)
        
        # Update the recipe in the database
        db.add(updated_recipe)
        db.commit()
    
    def update_multi_field_vectors(self, db: Session) -> None:
        """
        Update field-specific feature vectors for all recipes
        """
        from backend.services.multi_field_search_service import multi_field_search_service
        
        # Generate embeddings for all recipes
        multi_field_search_service.generate_embeddings_for_all_recipes(db)
        
        # Rebuild indices
        self.load_multi_field_indices(db)
    
    def search_by_title_vector(self, db: Session, *, query_vector: np.ndarray, k: int = 10) -> Tuple[List[int], List[float]]:
        """
        Search recipes by title feature vector using FAISS
        
        Args:
            db: Database session
            query_vector: Title vector to search for
            k: Number of results to return
            
        Returns:
            Tuple of (recipe_ids, similarity_scores)
        """
        if self.title_index is None or self.title_index.ntotal == 0:
            return [], []
            
        # Make sure vector is the right shape
        query_vector = query_vector.reshape(1, -1).astype(np.float32)
        
        # Search the FAISS index
        distances, indices = self.title_index.search(query_vector, k)
        
        # Convert FAISS distances to similarity scores (0-1 range)
        max_distance = np.max(distances) if distances.size > 0 else 1.0
        similarities = 1.0 - (distances[0] / max_distance if max_distance > 0 else distances[0])
        
        # Convert indices to recipe IDs
        recipe_ids = [self.title_recipe_map.get(int(idx)) for idx in indices[0] if idx >= 0 and int(idx) in self.title_recipe_map]
        
        return recipe_ids, similarities.tolist()
    
    def search_by_ingredients_vector(self, db: Session, *, query_vector: np.ndarray, k: int = 10) -> Tuple[List[int], List[float]]:
        """
        Search recipes by ingredients feature vector using FAISS
        
        Args:
            db: Database session
            query_vector: Ingredients vector to search for
            k: Number of results to return
            
        Returns:
            Tuple of (recipe_ids, similarity_scores)
        """
        if self.ingredients_index is None or self.ingredients_index.ntotal == 0:
            return [], []
            
        # Make sure vector is the right shape
        query_vector = query_vector.reshape(1, -1).astype(np.float32)
        
        # Search the FAISS index
        distances, indices = self.ingredients_index.search(query_vector, k)
        
        # Convert FAISS distances to similarity scores (0-1 range)
        max_distance = np.max(distances) if distances.size > 0 else 1.0
        similarities = 1.0 - (distances[0] / max_distance if max_distance > 0 else distances[0])
        
        # Convert indices to recipe IDs
        recipe_ids = [self.ingredients_recipe_map.get(int(idx)) for idx in indices[0] if idx >= 0 and int(idx) in self.ingredients_recipe_map]
        
        return recipe_ids, similarities.tolist()
    
    def search_by_instructions_vector(self, db: Session, *, query_vector: np.ndarray, k: int = 10) -> Tuple[List[int], List[float]]:
        """
        Search recipes by instructions feature vector using FAISS
        
        Args:
            db: Database session
            query_vector: Instructions vector to search for
            k: Number of results to return
            
        Returns:
            Tuple of (recipe_ids, similarity_scores)
        """
        if self.instructions_index is None or self.instructions_index.ntotal == 0:
            return [], []
            
        # Make sure vector is the right shape
        query_vector = query_vector.reshape(1, -1).astype(np.float32)
        
        # Search the FAISS index
        distances, indices = self.instructions_index.search(query_vector, k)
        
        # Convert FAISS distances to similarity scores (0-1 range)
        max_distance = np.max(distances) if distances.size > 0 else 1.0
        similarities = 1.0 - (distances[0] / max_distance if max_distance > 0 else distances[0])
        
        # Convert indices to recipe IDs
        recipe_ids = [self.instructions_recipe_map.get(int(idx)) for idx in indices[0] if idx >= 0 and int(idx) in self.instructions_recipe_map]
        
        return recipe_ids, similarities.tolist()
    
    def search_multi_field(
        self,
        db: Session,
        *,
        title_vector: Optional[np.ndarray] = None,
        ingredients_vector: Optional[np.ndarray] = None,
        instructions_vector: Optional[np.ndarray] = None,
        weights: Optional[Dict[str, float]] = None,
        k: int = 10
    ) -> List[Recipe]:
        """
        Search recipes using weighted combination of field-specific searches
        
        Args:
            db: Database session
            title_vector: Title embedding vector (optional)
            ingredients_vector: Ingredients embedding vector (optional)
            instructions_vector: Instructions embedding vector (optional)
            weights: Dictionary with weights for each field (optional)
            k: Number of results to return
            
        Returns:
            List of Recipe objects sorted by weighted similarity
        """
        # Default weights if not provided
        if weights is None:
            weights = {
                "title": 0.3,
                "ingredients": 0.4,
                "instructions": 0.3
            }
        
        # Initialize results dictionary to track scores
        recipe_scores = {}
        
        # Search title index if vector provided
        if title_vector is not None and weights.get("title", 0) > 0:
            title_weight = weights.get("title", 0.3)
            title_ids, title_scores = self.search_by_title_vector(db, query_vector=title_vector, k=k*2)
            
            # Add weighted scores to results
            for idx, recipe_id in enumerate(title_ids):
                if recipe_id not in recipe_scores:
                    recipe_scores[recipe_id] = 0
                recipe_scores[recipe_id] += title_scores[idx] * title_weight
        
        # Search ingredients index if vector provided
        if ingredients_vector is not None and weights.get("ingredients", 0) > 0:
            ingredients_weight = weights.get("ingredients", 0.4)
            ingredients_ids, ingredients_scores = self.search_by_ingredients_vector(db, query_vector=ingredients_vector, k=k*2)
            
            # Add weighted scores to results
            for idx, recipe_id in enumerate(ingredients_ids):
                if recipe_id not in recipe_scores:
                    recipe_scores[recipe_id] = 0
                recipe_scores[recipe_id] += ingredients_scores[idx] * ingredients_weight
        
        # Search instructions index if vector provided
        if instructions_vector is not None and weights.get("instructions", 0) > 0:
            instructions_weight = weights.get("instructions", 0.3)
            instructions_ids, instructions_scores = self.search_by_instructions_vector(db, query_vector=instructions_vector, k=k*2)
            
            # Add weighted scores to results
            for idx, recipe_id in enumerate(instructions_ids):
                if recipe_id not in recipe_scores:
                    recipe_scores[recipe_id] = 0
                recipe_scores[recipe_id] += instructions_scores[idx] * instructions_weight
        
        # Sort recipes by score
        sorted_results = sorted(recipe_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get top k recipe IDs
        top_ids = [r[0] for r in sorted_results[:k]]
        
        # Fetch recipes for the top IDs
        recipes = db.query(Recipe).filter(Recipe.id.in_(top_ids)).all() if top_ids else []
        
        # Sort recipes to match the original order from scoring
        sorted_recipes = []
        for recipe_id in top_ids:
            for recipe in recipes:
                if recipe.id == recipe_id:
                    sorted_recipes.append(recipe)
                    break
        
        return sorted_recipes
    
    def get_multi_by_ids(self, db: Session, *, ids: List[int]) -> List[Recipe]:
        """Get multiple recipes by their IDs"""
        return db.query(Recipe).filter(Recipe.id.in_(ids)).all() if ids else []

# Create an instance with just the model
recipe_repository = RecipeRepository(None)  # Pass None for db, it will be provided at runtime 