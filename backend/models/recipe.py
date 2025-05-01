# TODO: Define Recipe database model
from sqlalchemy import Column, Integer, String, Text, ARRAY, ForeignKey, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.session import Base

class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    ingredients = Column(ARRAY(String))
    instructions = Column(ARRAY(Text))
    image_url = Column(String)
    categories = Column(ARRAY(String))
    prep_time = Column(Integer)  # minutes
    cook_time = Column(Integer)  # minutes
    servings = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    
    # TODO: Add relationship to user
    user = relationship("User", back_populates="recipes")
    
    # TODO: Add feature vector column for LSH
    feature_vector = Column(ARRAY(Float))