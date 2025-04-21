from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Date, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

from app.core.database import Base


# SQLAlchemy ORM models
class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Relationships
    product = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("category.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="product")


class DataProduct(Base):
    __tablename__ = "data_and_product"

    id = Column(Integer, primary_key=True, index=True)
    crop_type = Column(String(30))
    satellite = Column(String(50))
    time_interval = Column(String(50))
    season = Column(String(200))
    from_date = Column(Date)
    to_date = Column(Date)
    calibration = Column(String(50))
    status = Column(String(50))
    active = Column(Boolean)  # Using Boolean instead of tinyint
    created_by = Column(Integer, ForeignKey("user.id"))
    created_on = Column(DateTime, default=func.now())
    job_id = Column(Integer)
    direction = Column(String(100))
    input_path = Column(String(2000))
    vv_output_path = Column(String(2000))
    polarization = Column(String(100))
    category = Column(String(100))
    coordinates = Column(String(3000))
    bands = Column(Integer)
    request_type = Column(Integer)
    vh_output_path = Column(String(2000))
    crop_id = Column(Integer)
    area = Column(BigInteger)
    perimeter = Column(BigInteger)
    extent = Column(String(2000))
    
    # Relationships
    user = relationship("User")
    blocks = relationship("DPBlocks", back_populates="data_and_product")
    mask_noise = relationship("DPMaskNoise", back_populates="data_and_product")
    product = relationship("DPProduct", back_populates="data_and_product")


class DPBlocks(Base):
    __tablename__ = "data_product_block"

    id = Column(Integer, primary_key=True, index=True)
    data_product_id = Column(Integer, ForeignKey("data_and_product.id"))
    block_size = Column(Integer)
    block_count = Column(Integer)
    
    # Relationships
    data_and_product = relationship("DataProduct")


class DPMaskNoise(Base):
    __tablename__ = "data_product_mask_noise"

    id = Column(Integer, primary_key=True, index=True)
    data_product_id = Column(Integer, ForeignKey("data_and_product.id"))
    mask_type = Column(String(50))
    noise_level = Column(Float)
    
    # Relationships
    data_and_product = relationship("DataProduct")


class DPProduct(Base):
    __tablename__ = "data_product_product"

    id = Column(Integer, primary_key=True, index=True)
    data_product_id = Column(Integer, ForeignKey("data_and_product.id"))
    product_id = Column(Integer, ForeignKey("product.id"))
    
    # Relationships
    data_and_product = relationship("DataProduct")
    product = relationship("Product")

class Satellite(Base):
    __tablename__ = "satellite"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20))
    is_premium = Column(Boolean)
    active = Column(Boolean, default=True)
    created_by = Column(String(30))
    created_on = Column(DateTime, default=func.now())


# Pydantic models for API
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: int


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    category: CategoryResponse
    
    class Config:
        from_attributes = True


class DPBlocksBase(BaseModel):
    block_size: int
    block_count: int


class DPBlocksCreate(DPBlocksBase):
    data_product_id: int


class DPBlocksResponse(DPBlocksBase):
    id: int
    data_product_id: int
    
    class Config:
        from_attributes = True


class DPMaskNoiseBase(BaseModel):
    mask_type: str
    noise_level: float


class DPMaskNoiseCreate(DPMaskNoiseBase):
    data_product_id: int


class DPMaskNoiseResponse(DPMaskNoiseBase):
    id: int
    data_product_id: int
    
    class Config:
        from_attributes = True


class DataProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    file_type: Optional[str] = None


class DataProductCreate(DataProductBase):
    pass


class DataProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DataProductResponse(DataProductBase):
    id: int
    file_path: Optional[str] = None
    size: Optional[float] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_active: bool
    user_id: int
    
    class Config:
        from_attributes = True


class DataProductDetailResponse(DataProductResponse):
    blocks: Optional[DPBlocksResponse] = None
    mask_noise: List[DPMaskNoiseResponse] = []
    products: List[ProductResponse] = []
    
    class Config:
        from_attributes = True