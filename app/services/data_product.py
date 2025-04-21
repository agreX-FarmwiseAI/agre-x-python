from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import logging
from datetime import datetime

from app.models.data_product import (
    DataProduct, DataProductCreate, DataProductUpdate, Category, 
    CategoryCreate, Product, ProductCreate, DPBlocks, DPMaskNoise
)
from app.models.user import User
from app.core.config import settings
from app.utils.file_upload import FileUpload
from app.core.exceptions import ResourceNotFoundException

logger = logging.getLogger(__name__)


class DataProductService:
    @staticmethod
    async def create_data_product(
        db: Session,
        data_product: DataProductCreate,
        current_user: User
    ) -> DataProduct:
        """Create a new data product"""
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

    @staticmethod
    async def upload_file(
        db: Session,
        data_product_id: int,
        file: UploadFile,
        current_user: User
    ) -> DataProduct:
        """Upload a file for a data product"""
        data_product = db.query(DataProduct).filter(DataProduct.id == data_product_id).first()
        if not data_product:
            raise ResourceNotFoundException("DataProduct", data_product_id)

        if data_product.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this data product")

        # Create upload directory
        upload_dir = os.path.join(settings.UPLOAD_FOLDER, f"user_{current_user.id}")
        os.makedirs(upload_dir, exist_ok=True)

        # Generate file path and save file
        file_path = FileUpload.get_file_path(current_user.id, "data_product", file.filename)
        success, error = await FileUpload.save_upload_file(file, file_path)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {error}")

        # Update data product
        data_product.file_path = file_path
        data_product.file_type = os.path.splitext(file.filename)[1].lstrip(".")
        data_product.size = os.path.getsize(file_path)
        data_product.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(data_product)
        return data_product

    @staticmethod
    async def get_data_products(
        db: Session,
        current_user: User,
        skip: int = 0,
        limit: int = 100
    ) -> List[DataProduct]:
        """Get all data products for a user"""
        return db.query(DataProduct).filter(
            DataProduct.user_id == current_user.id
        ).offset(skip).limit(limit).all()

    @staticmethod
    async def get_data_product(
        db: Session,
        data_product_id: int,
        current_user: User
    ) -> DataProduct:
        """Get a specific data product"""
        data_product = db.query(DataProduct).filter(DataProduct.id == data_product_id).first()
        if not data_product:
            raise ResourceNotFoundException("DataProduct", data_product_id)
        
        if data_product.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this data product")
        
        return data_product

    @staticmethod
    async def update_data_product(
        db: Session,
        data_product_id: int,
        data_product_update: DataProductUpdate,
        current_user: User
    ) -> DataProduct:
        """Update a data product"""
        data_product = db.query(DataProduct).filter(DataProduct.id == data_product_id).first()
        if not data_product:
            raise ResourceNotFoundException("DataProduct", data_product_id)

        if data_product.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this data product")

        # Update fields if provided
        if data_product_update.name is not None:
            data_product.name = data_product_update.name
        if data_product_update.description is not None:
            data_product.description = data_product_update.description
        if data_product_update.is_active is not None:
            data_product.is_active = data_product_update.is_active

        data_product.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(data_product)
        return data_product

    @staticmethod
    async def delete_data_product(
        db: Session,
        data_product_id: int,
        current_user: User
    ) -> None:
        """Delete a data product"""
        data_product = db.query(DataProduct).filter(DataProduct.id == data_product_id).first()
        if not data_product:
            raise ResourceNotFoundException("DataProduct", data_product_id)

        if data_product.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this data product")

        # Delete associated file
        if data_product.file_path and os.path.exists(data_product.file_path):
            try:
                os.remove(data_product.file_path)
            except Exception as e:
                logger.error(f"Error deleting file {data_product.file_path}: {str(e)}")

        # Delete data product and related entities
        db.delete(data_product)
        db.commit()

    @staticmethod
    async def create_category(
        db: Session,
        category: CategoryCreate
    ) -> Category:
        """Create a new category"""
        db_category = Category(
            name=category.name,
            description=category.description
        )
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category

    @staticmethod
    async def get_categories(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Category]:
        """Get all categories"""
        return db.query(Category).offset(skip).limit(limit).all()

    @staticmethod
    async def create_product(
        db: Session,
        product: ProductCreate
    ) -> Product:
        """Create a new product"""
        # Verify category exists
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

    @staticmethod
    async def get_products(
        db: Session,
        category_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """Get all products, optionally filtered by category"""
        query = db.query(Product)
        if category_id:
            query = query.filter(Product.category_id == category_id)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    async def create_blocks(
        db: Session,
        data_product_id: int,
        block_size: int,
        block_count: int,
        current_user: User
    ) -> DPBlocks:
        """Create blocks for a data product"""
        data_product = db.query(DataProduct).filter(DataProduct.id == data_product_id).first()
        if not data_product:
            raise ResourceNotFoundException("DataProduct", data_product_id)

        if data_product.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this data product")

        db_blocks = DPBlocks(
            data_product_id=data_product_id,
            block_size=block_size,
            block_count=block_count
        )
        db.add(db_blocks)
        db.commit()
        db.refresh(db_blocks)
        return db_blocks

    @staticmethod
    async def create_mask_noise(
        db: Session,
        data_product_id: int,
        mask_type: str,
        noise_level: float,
        current_user: User
    ) -> DPMaskNoise:
        """Create mask noise for a data product"""
        data_product = db.query(DataProduct).filter(DataProduct.id == data_product_id).first()
        if not data_product:
            raise ResourceNotFoundException("DataProduct", data_product_id)

        if data_product.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this data product")

        db_mask_noise = DPMaskNoise(
            data_product_id=data_product_id,
            mask_type=mask_type,
            noise_level=noise_level
        )
        db.add(db_mask_noise)
        db.commit()
        db.refresh(db_mask_noise)
        return db_mask_noise