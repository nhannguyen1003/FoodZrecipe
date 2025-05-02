# TODO: Implement admin API endpoints
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.core.security import get_current_admin_user
from backend.models.user import User
from backend.services.lsh_service import lsh_service
from database.session import get_db
from database.repositories.user_repository import user_repository
from database.repositories.recipe_repository import recipe_repository

router = APIRouter()

@router.get("/dashboard", response_model=Dict[str, Any])
def get_admin_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Get admin dashboard data including:
    - System stats (total recipes, users)
    - Search indices status
    - LSH parameters 
    """
    try:
        # Get basic stats
        recipe_count = db.query(recipe_repository.model).count()
        user_count = db.query(user_repository.model).count()
        
        # Get LSH index info
        text_index_size = getattr(recipe_repository.text_index, 'ntotal', 0)
        image_index_size = getattr(recipe_repository.image_index, 'ntotal', 0)
        
        # Return stats
        return {
            "system_stats": {
                "total_recipes": recipe_count,
                "total_users": user_count,
                "text_index_entries": text_index_size,
                "image_index_entries": image_index_size
            },
            "lsh_parameters": {
                "vector_dim": getattr(lsh_service, 'vector_dim', 128),
                "hash_bits": getattr(lsh_service, 'hash_bits', 32)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard data: {str(e)}")

@router.get("/performance", response_model=Dict[str, Any])
def get_algorithm_performance(
    test_size: int = 10,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get algorithm performance metrics using a sample of the database as test data
    
    This runs a small-scale performance evaluation by:
    1. Selecting random recipes as queries
    2. Finding ground truth matches using regular search
    3. Comparing with LSH results
    4. Reporting precision, recall, and speed metrics
    """
    try:
        # Get a sample of recipes for evaluation
        recipes = db.query(recipe_repository.model).limit(test_size).all()
        
        if not recipes:
            return {"error": "No recipes available for evaluation"}
        
        # Collect query vectors for the recipes
        query_vectors = []
        ground_truth = []
        
        for recipe in recipes:
            if recipe.text_feature_vector:
                # Use each recipe's vector as a query
                query_vectors.append(recipe.text_feature_vector)
                
                # Find ground truth matches for this recipe through full scan
                # (simplified approach - in real system use more sophisticated ground truth)
                # Get recipes with similar title/categories
                similar = db.query(recipe_repository.model).filter(
                    recipe_repository.model.id != recipe.id,
                    recipe_repository.model.categories.overlap(recipe.categories)
                ).limit(5).all()
                
                ground_truth.append([r.id for r in similar])
        
        # Skip evaluation if we don't have enough data
        if not query_vectors:
            return {"error": "No feature vectors available for evaluation"}
        
        # Run evaluation using the LSH service
        if not hasattr(lsh_service, 'evaluate'):
            return {"error": "LSH evaluation not implemented"}
        
        import time
        
        # Build LSH index if not already done
        if not getattr(lsh_service, 'is_initialized', False):
            lsh_service.initialize()
            lsh_service.build_indices(db.query(recipe_repository.model).all())
        
        # Measure search speed
        start_time = time.time()
        metrics = lsh_service.evaluate(
            query_vectors=query_vectors[:min(5, len(query_vectors))],  # Limit for speed
            ground_truth=ground_truth[:min(5, len(ground_truth))],
            k=5
        )
        search_time = time.time() - start_time
        
        # Add time metrics
        metrics["avg_search_time_ms"] = (search_time * 1000) / min(5, len(query_vectors))
        metrics["total_evaluation_time_ms"] = search_time * 1000
        metrics["test_size"] = len(query_vectors)
        
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating performance: {str(e)}")

@router.post("/lsh-parameters", response_model=Dict[str, Any])
def update_lsh_parameters(
    parameters: Dict[str, Any] = Body(...),
    rebuild_indices: bool = True,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update LSH parameters and optionally rebuild indices
    
    Parameters:
    - vector_dim: Dimension of feature vectors
    - hash_bits: Number of hash bits for LSH
    - rebuild_indices: Whether to rebuild indices immediately
    """
    try:
        # Extract parameters
        vector_dim = parameters.get("vector_dim")
        hash_bits = parameters.get("hash_bits")
        
        # Update LSH service parameters
        lsh_service.update_parameters(vector_dim=vector_dim, hash_bits=hash_bits)
        
        # Rebuild indices if requested
        if rebuild_indices:
            recipes = db.query(recipe_repository.model).all()
            lsh_service.build_indices(recipes)
            
            # Update record count
            text_index_size = getattr(lsh_service.text_index, 'ntotal', 0)
            image_index_size = getattr(lsh_service.image_index, 'ntotal', 0)
            
            return {
                "message": "Parameters updated and indices rebuilt",
                "parameters": {
                    "vector_dim": getattr(lsh_service, 'vector_dim', None),
                    "hash_bits": getattr(lsh_service, 'hash_bits', None)
                },
                "indices": {
                    "text_index_size": text_index_size,
                    "image_index_size": image_index_size
                }
            }
        else:
            return {
                "message": "Parameters updated",
                "parameters": {
                    "vector_dim": getattr(lsh_service, 'vector_dim', None),
                    "hash_bits": getattr(lsh_service, 'hash_bits', None)
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating LSH parameters: {str(e)}")

@router.post("/rebuild-indices", response_model=Dict[str, Any])
def rebuild_indices(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """
    Rebuild all LSH indices
    
    This is useful after adding many new recipes or changing LSH parameters
    """
    try:
        # Get all recipes
        recipes = db.query(recipe_repository.model).all()
        
        # Build recipes in both the repository and service
        recipe_repository.load_faiss_indices(db)
        
        # Update record count
        text_index_size = getattr(recipe_repository.text_index, 'ntotal', 0)
        image_index_size = getattr(recipe_repository.image_index, 'ntotal', 0)
        
        return {
            "message": "Indices rebuilt successfully",
            "indices": {
                "text_index_size": text_index_size,
                "image_index_size": image_index_size,
                "recipe_count": len(recipes)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rebuilding indices: {str(e)}")