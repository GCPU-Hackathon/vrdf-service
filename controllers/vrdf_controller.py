import glob
import os
import logging
from pathlib import Path
import nibabel as nib
import numpy as np
import re

from encode import (
    load_user_config, 
    export_labelmap_weighted_case,
    compute_spacing_mm
)

logger = logging.getLogger(__name__)

# Segmentation constants
LABELS = [0, 1, 2, 3]

def extract_modality_from_filename(filename):
    """Extract modality (t1n, t1c, t2w, t2f) from filename"""
    # Pattern: *-{modality}.nii.gz
    match = re.search(r'-(t1n|t1c|t2w|t2f)\.nii\.gz$', filename)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract modality from filename: {filename}")

def load_3d(path):
    """Load 3D volume from NIfTI file"""
    img = nib.load(path)
    data = img.get_fdata()
    if data.ndim > 3:
        data = data[..., 0]
    return data.astype(np.float32), img.affine, img.header

def perform_segmentation_from_filename(study_dir: Path, filename: str, seg_filename: str):
    """
    Perform segmentation on BraTS-style files using the provided filename and segmentation file
    Returns the path to the segmented file
    """
    try:
        folder = str(study_dir)
        patient_id = study_dir.name
        
        # Extract modality from filename
        modality = extract_modality_from_filename(filename)
        logger.info(f"Extracted modality: {modality} from filename: {filename}")
        
        # Use provided segmentation file
        seg_file = study_dir / seg_filename
        input_file = study_dir / filename
        
        # Validate files exist
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        if not seg_file.exists():
            raise FileNotFoundError(f"Segmentation file not found: {seg_file}")
        
        logger.info(f"Using segmentation file: {seg_file}")
        logger.info(f"Processing input file: {input_file}")
        
        # Load segmentation
        seg, aff, hdr = load_3d(str(seg_file))
        seg = seg.astype(np.int32)
        
        # Load the input modality file
        vol, _, _ = load_3d(str(input_file))
        
        H, W, Z = vol.shape
        S = len(LABELS)
        
        # Create masks for each label
        masks = [(seg == lab) for lab in LABELS]
        
        # Create output volume
        out = np.zeros((H, W, Z, S), dtype=np.float32)
        for s_idx, mask in enumerate(masks):
            if np.any(mask):
                out[..., s_idx][mask] = vol[mask]
        
        # Prepare output filename: patient-segmented-t1n.nii.gz
        base_name = filename.replace(f'-{modality}.nii.gz', '')
        segmented_filename = f"{base_name}-segmented-{modality}.nii.gz"
        out_path = study_dir / segmented_filename
        
        # Save segmented file
        h = hdr.copy()
        h.set_data_dtype(np.float32)
        nib.save(nib.Nifti1Image(out, aff, header=h), str(out_path))
        logger.info(f"Saved segmented file: {out_path} | shape {out.shape} [H,W,Z,S] | labels {LABELS}")
        
        return str(out_path)
        
    except Exception as e:
        logger.error(f"Segmentation failed: {str(e)}")
        raise

def perform_conversion(input_file: str, output_file: str, config_path: str):
    """
    Perform the actual conversion using the encode.py functionality with default mode
    """
    try:
        logger.info(f"Starting conversion: {input_file} -> {output_file}")
        
        # Load user configuration
        user_cfg = load_user_config(config_path)
        
        # Load the NIfTI file
        img = nib.load(input_file)
        vol_full = img.get_fdata(dtype=np.float32)
        affine = img.affine
        spacing_mm = compute_spacing_mm(affine)
        
        user_tf = None
        if user_cfg is not None and "transfer_function" in user_cfg:
            user_tf = user_cfg["transfer_function"]
        
        logger.info(f"Processing volume with shape: {vol_full.shape}")
        
        # Use default mode: labelmap_weighted4d
        export_labelmap_weighted_case(
            vol_full=vol_full,
            affine=affine,
            spacing_mm=spacing_mm,
            user_tf=user_tf,
            vrdf_out=output_file,
            debug_dump=False,
            split_weight=False
        )
        
        logger.info(f"Conversion completed: {output_file}")
        
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        raise

def perform_segmentation_and_conversion_from_filename(study_code: str, filename: str, seg_filename: str, config_path: str = "./config.json"):
    """
    Perform segmentation and conversion using filename and segmentation file
    Returns tuple: (segmented_file_path, vrdf_file_path)
    """
    try:
        study_dir = Path("storage") / "studies" / study_code
        
        # Validate study directory exists
        if not study_dir.exists():
            raise FileNotFoundError(f"Study directory not found: {study_dir}")
        
        logger.info(f"Starting segmentation and conversion for study {study_code}, file {filename}, seg {seg_filename}")
        
        # Step 1: Perform segmentation
        segmented_file = perform_segmentation_from_filename(study_dir, filename, seg_filename)
        
        # Step 2: Generate VRDF output filename
        modality = extract_modality_from_filename(filename)
        base_name = filename.replace(f'-{modality}.nii.gz', '')
        vrdf_filename = f"{base_name}-{modality}.vrdf"
        vrdf_file = study_dir / vrdf_filename
        
        # Step 3: Perform conversion
        perform_conversion(segmented_file, str(vrdf_file), config_path)
        
        # Step 4: Delete the intermediate segmented file
        segmented_path = Path(segmented_file)
        if segmented_path.exists():
            segmented_path.unlink()
            logger.info(f"Deleted intermediate segmented file: {segmented_file}")
        
        logger.info(f"Pipeline completed: {vrdf_file}")
        # Return the actual filename that encode.py creates (with _lw suffix)
        actual_vrdf_filename = f"{base_name}-{modality}_lw.vrdf"
        return str(segmented_file), actual_vrdf_filename  # Return actual filename
        
    except Exception as e:
        logger.error(f"Segmentation and conversion failed: {str(e)}")
        raise
