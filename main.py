from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
import logging

from controllers.vrdf_controller import (
    perform_segmentation_and_conversion_from_filename
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VRDF Service",
    description="Service to convert NIfTI files to VRDF format with mandatory segmentation",
    version="1.0.0"
)

class ConvertRequest(BaseModel):
    study_code: str
    filename: str
    seg_filename: str
    config_path: Optional[str] = "./config.json"

class ConvertResponse(BaseModel):
    success: bool
    message: str
    vrdf_file: str

@app.get("/health")
async def health_check():
    """Health check endpoint to verify the service is running"""
    return {"status": "healthy", "service": "vrdf-service"}

@app.post("/convert", response_model=ConvertResponse)
async def convert_nifti_to_vrdf(request: ConvertRequest):
    """
    Convert a NIfTI file to VRDF format with mandatory segmentation
    
    Args:
        request: ConvertRequest containing study_code, filename, seg_filename, and config_path
        
    Returns:
        ConvertResponse with success status and both output file paths
    """
    try:
        # Perform segmentation and conversion directly
        segmented_file, vrdf_file = perform_segmentation_and_conversion_from_filename(
            study_code=request.study_code,
            filename=request.filename,
            seg_filename=request.seg_filename,
            config_path=request.config_path
        )
        
        logger.info(f"Conversion completed: {vrdf_file}")
        
        return ConvertResponse(
            success=True,
            message=f"Segmentation and conversion completed for {request.filename}",
            vrdf_file=vrdf_file
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in convert endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
