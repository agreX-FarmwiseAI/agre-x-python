from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.data_product import (
    DataProduct, DataProductCreate, DataProductUpdate, DataProductResponse,
    DataProductDetailResponse, Category, CategoryCreate, CategoryResponse,
    Product, ProductCreate, ProductResponse, DPBlocks, DPBlocksCreate,
    DPMaskNoise, DPMaskNoiseCreate, Satellite
)
from app.models.user import User
from app.core.exceptions import ResourceNotFoundException
from app.core.config import settings

router = APIRouter()


@router.post("/", response_model=DataProductResponse, status_code=status.HTTP_201_CREATED)
async def create_data_product(
    data_product: DataProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new data product
    """
    db_data_product = DataProduct(
        name=data_product.name,
        description=data_product.description,
        file_type=data_product.file_type,
        user_id=current_user.id
    )
    db.add(db_data_product)
    db.commit()
    db.refresh(db_data_product)
    return db_data_product


@router.post("/upload/{data_product_id}", response_model=DataProductResponse)
async def upload_data_product_file(
    data_product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a file for a data product
    """
    # Verify data product exists and belongs to user
    data_product = db.query(DataProduct).filter(DataProduct.id == data_product_id).first()
    if not data_product:
        raise ResourceNotFoundException("DataProduct", data_product_id)
    
    if data_product.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this data product"
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(settings.UPLOAD_FOLDER, f"user_{current_user.id}")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, f"data_product_{data_product_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update data product
    data_product.file_path = file_path
    data_product.file_type = os.path.splitext(file.filename)[1].lstrip(".")
    data_product.size = os.path.getsize(file_path)
    db.commit()
    db.refresh(data_product)
    
    return data_product


@router.get("/", response_model=List[DataProductResponse])
async def get_data_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all data products for the current user
    """
    data_products = db.query(DataProduct).filter(
        DataProduct.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return data_products


@router.get("/{data_product_id}", response_model=DataProductDetailResponse)
async def get_data_product(
    data_product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a data product by ID
    """
    data_product = db.query(DataProduct).filter(DataProduct.id == data_product_id).first()
    if not data_product:
        raise ResourceNotFoundException("DataProduct", data_product_id)
    
    return data_product


@router.put("/{data_product_id}", response_model=DataProductResponse)
async def update_data_product(
    data_product_id: int,
    data_product_update: DataProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a data product
    """
    data_product = db.query(DataProduct).filter(DataProduct.id == data_product_id).first()
    if not data_product:
        raise ResourceNotFoundException("DataProduct", data_product_id)
    
    if data_product.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this data product"
        )
    
    # Update fields if provided
    if data_product_update.name is not None:
        data_product.name = data_product_update.name
    if data_product_update.description is not None:
        data_product.description = data_product_update.description
    if data_product_update.is_active is not None:
        data_product.is_active = data_product_update.is_active
    
    db.commit()
    db.refresh(data_product)
    return data_product


@router.delete("/{data_product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_product(
    data_product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a data product
    """
    data_product = db.query(DataProduct).filter(DataProduct.id == data_product_id).first()
    if not data_product:
        raise ResourceNotFoundException("DataProduct", data_product_id)
    
    if data_product.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this data product"
        )
    
    # Delete file if exists
    if data_product.file_path and os.path.exists(data_product.file_path):
        os.remove(data_product.file_path)
    
    # Delete data product and related entities
    db.delete(data_product)
    db.commit()
    return None


@router.get("/download/{data_product_id}")
async def download_data_product(
    data_product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Download a data product file
    """
    data_product = db.query(DataProduct).filter(DataProduct.id == data_product_id).first()
    if not data_product or not data_product.file_path:
        raise ResourceNotFoundException("DataProduct", data_product_id)
    
    if not os.path.exists(data_product.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    return FileResponse(
        path=data_product.file_path,
        filename=os.path.basename(data_product.file_path),
        media_type=f"application/{data_product.file_type}"
    )


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new category
    """
    db_category = Category(
        name=category.name,
        description=category.description
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all categories
    """
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new product
    """
    # Check if category exists
    category = db.query(Category).filter(Category.id == product.category_id).first()
    if not category:
        raise ResourceNotFoundException("Category", product.category_id)
    
    db_product = Product(
        name=product.name,
        description=product.description,
        category_id=product.category_id
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("/products", response_model=List[ProductResponse])
async def get_products(
    db: Session = Depends(get_db),
    category_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get all products, optionally filtered by category
    """
    query = db.query(Product)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    products = query.offset(skip).limit(limit).all()
    return products


@router.post("/blocks", response_model=DPBlocksCreate, status_code=status.HTTP_201_CREATED)
async def create_dp_blocks(
    blocks: DPBlocksCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create blocks for a data product
    """
    # Check if data product exists
    data_product = db.query(DataProduct).filter(DataProduct.id == blocks.data_product_id).first()
    if not data_product:
        raise ResourceNotFoundException("DataProduct", blocks.data_product_id)
    
    # Check if user is authorized
    if data_product.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this data product"
        )
    
    db_blocks = DPBlocks(
        data_product_id=blocks.data_product_id,
        block_size=blocks.block_size,
        block_count=blocks.block_count
    )
    db.add(db_blocks)
    db.commit()
    db.refresh(db_blocks)
    return db_blocks


@router.post("/mask-noise", response_model=DPMaskNoiseCreate, status_code=status.HTTP_201_CREATED)
async def create_dp_mask_noise(
    mask_noise: DPMaskNoiseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create mask noise for a data product
    """
    # Check if data product exists
    data_product = db.query(DataProduct).filter(DataProduct.id == mask_noise.data_product_id).first()
    if not data_product:
        raise ResourceNotFoundException("DataProduct", mask_noise.data_product_id)
    
    # Check if user is authorized
    if data_product.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this data product"
        )
    
    db_mask_noise = DPMaskNoise(
        data_product_id=mask_noise.data_product_id,
        mask_type=mask_noise.mask_type,
        noise_level=mask_noise.noise_level
    )
    db.add(db_mask_noise)
    db.commit()
    db.refresh(db_mask_noise)
    return db_mask_noise

@router.get("/getSatellite")
def get_satellite(
    db: Session = Depends(get_db),
):
    """
    getSatellite function
    """
    return db.query(Satellite).all()