from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import logging
import threading
from app.core.database import get_db
from app.models.data_product import (
    DataProduct, DataProductCreate, DataProductUpdate, DataProductResponse,
    DataProductDetailResponse, Category, CategoryCreate, CategoryResponse,
    Product, ProductCreate, ProductResponse, DPBlocks, DPBlocksCreate,
    DPMaskNoise, DPMaskNoiseCreate, Satellite, DataProductRequest
)
from app.models.user import User
from app.core.exceptions import ResourceNotFoundException
from app.core.config import settings

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PythonService(threading.Thread):
    def __init__(self, args, script_path):
        threading.Thread.__init__(self)
        self.args = args
        self.script_path = script_path
        
    def run(self):
        try:
            cmd = [self.script_path] + self.args
            logger.info(f"Executing command: {' '.join(cmd)}")
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("Script execution initiated")
        except Exception as e:
            logger.error(f"Error executing script: {e}")

def get_model_output_path(crop_id: int, db: Session):
    # This would implement the logic of getModelOutputPath in the Java code
    crop = db.query(DataProduct).filter(DataProduct.crop_id == crop_id).first()
    if crop:
        return f"/output/path/for/crop/{crop_id}"
    return "/default/output/path"

@router.post("/", response_model=DataProductResponse, status_code=status.HTTP_201_CREATED)
async def create_data_product(
    user_id:int,
    data_product: DataProductCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new data product
    """
    db_data_product = DataProduct(
        name=data_product.name,
        description=data_product.description,
        file_type=data_product.file_type,
        user_id=user_id
    )
    db.add(db_data_product)
    db.commit()
    db.refresh(db_data_product)
    return db_data_product

@router.get("/getSatellite")
def get_satellite(
    db: Session = Depends(get_db),
):
    """
    getSatellite function
    """
    return db.query(Satellite).all()


@router.post("/upload/{data_product_id}", response_model=DataProductResponse)
async def upload_data_product_file(
    user_id: int,
    data_product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a file for a data product
    """
    # Verify data product exists and belongs to user
    data_product = db.query(DataProduct).filter(DataProduct.id == data_product_id).first()
    if not data_product:
        raise ResourceNotFoundException("DataProduct", data_product_id)
    
    if data_product.created_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this data product"
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(settings.UPLOAD_FOLDER, f"user_{user_id}")
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
    user_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all data products for the current user
    """
    data_products = db.query(DataProduct).filter(
        DataProduct.created_by == user_id
    ).offset(skip).limit(limit).all()
    
    return data_products


@router.get("/{data_product_id}", response_model=DataProductDetailResponse)
async def get_data_product(
    data_product_id: int,
    db: Session = Depends(get_db)
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
    user_id:int,
    data_product_update: DataProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a data product
    """
    data_product = db.query(DataProduct).filter(DataProduct.id == data_product_id).first()
    if not data_product:
        raise ResourceNotFoundException("DataProduct", data_product_id)
    
    if data_product.user_id != user_id:
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
    user_id :int,
    data_product_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a data product
    """
    data_product = db.query(DataProduct).filter(DataProduct.id == data_product_id).first()
    if not data_product:
        raise ResourceNotFoundException("DataProduct", data_product_id)
    
    if data_product.created_by != user_id:
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    user_id : int,
    blocks: DPBlocksCreate,
    db: Session = Depends(get_db)
):
    """
    Create blocks for a data product
    """
    # Check if data product exists
    data_product = db.query(DataProduct).filter(DataProduct.id == blocks.data_product_id).first()
    if not data_product:
        raise ResourceNotFoundException("DataProduct", blocks.data_product_id)
    
    # Check if user is authorized
    if data_product.created_by != user_id:
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
    user_id: int,
    mask_noise: DPMaskNoiseCreate,
    db: Session = Depends(get_db)
):
    """
    Create mask noise for a data product
    """
    # Check if data product exists
    data_product = db.query(DataProduct).filter(DataProduct.id == mask_noise.data_product_id).first()
    if not data_product:
        raise ResourceNotFoundException("DataProduct", mask_noise.data_product_id)
    
    # Check if user is authorized
    if data_product.created_by != user_id:
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

@router.post("/download", status_code=201)
def download_dp(dp_request: DataProductRequest, db: Session = Depends(get_db)):
    try:
        dp = DataProduct(
            crop_type=dp_request.crop_type,
            satellite=dp_request.satellite,
            time_interval=dp_request.time_interval,
            season=dp_request.season,
            from_date=dp_request.from_date,
            to_date=dp_request.to_date,
            calibration=dp_request.calibration,
            status=dp_request.status,
            active=dp_request.active,
            created_by=dp_request.created_by,
            created_on=datetime.now(),
            job_id=dp_request.job_id,
            direction=dp_request.direction,
            input_path=dp_request.input_path,
            polarization=dp_request.polarization,
            category=dp_request.category,
            coordinates=dp_request.coordinates,
            bands=dp_request.bands,
            request_type=dp_request.request_type,
            crop_id=dp_request.crop_id
        )
        
        db.add(dp)
        db.commit()
        db.refresh(dp)
        logger.info(f"After saved to database: {dp.id}")
        
        dp_req_arg_list = []
        dp_req_arg_list.append(str(dp.created_by))
        dp_req_arg_list.append(str(dp.job_id))
        
        from_date_formatted = dp.from_date.strftime("%Y-%m-%d")
        to_date_formatted = dp.to_date.strftime("%Y-%m-%d")
        logger.info(f"From date: {from_date_formatted}")
        logger.info(f"To date: {to_date_formatted}")
        
        dp_req_arg_list.append(from_date_formatted)
        dp_req_arg_list.append(to_date_formatted)
        dp_req_arg_list.append(dp.input_path)
        dp_req_arg_list.append("GRD")
        
        if dp.request_type == 2:
            dp_req_arg_list.append(dp.crop_type)
        else:
            dp_req_arg_list.append("Rice")
        
        dp_req_arg_list.append(str(dp.request_type))
        logger.info(f"REQUEST TYPE: {dp.request_type}")
        
        if dp.request_type == 2:
            logger.info("GETTING MODEL OUTPUT PATH")
            dp_req_arg_list.append(get_model_output_path(dp.crop_id, db))
        else:
            dp_req_arg_list.append("path")
        
        logger.info(f"Arguments for script: {dp_req_arg_list}")
        
        script_path = "/home/ubuntu/AgriX-Api/Crop_Analyser/data_and_product.sh"
        
        python_service = PythonService(dp_req_arg_list, script_path)
        python_service.start()
        
        logger.info(f"Executed Analysis For user_id - {dp.created_by} job_id - {dp.job_id} product_type - {dp.crop_type}")
        
        return {"success": True, "message": "Data product processing initiated"}
    
    except Exception as ex:
        logger.error(f"Error in download data products: {ex}")
        raise HTTPException(status_code=500, detail=f"Failed to process data product: {str(ex)}")