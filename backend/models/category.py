from sqlalchemy import Column, Integer, String, Text, DateTime, Index, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.session import Base

# Association table for many-to-many relationship between recipes and categories
recipe_category = Table(
    "recipe_category",
    Base.metadata,
    Column("recipe_id", Integer, ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)
)

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship to recipes
    recipes = relationship("Recipe", secondary=recipe_category, back_populates="category_relations")
    
    # Add index for performance
    __table_args__ = (
        Index('idx_category_name', 'name'),
    )
    
    def __repr__(self):
        return f"<Category {self.name}>" 