# VRDF Service

A FastAPI service for converting NIfTI medical imaging files to VRDF format for Unity DVR rendering with mandatory segmentation.

## Overview

This service provides a REST API to convert NIfTI files (.nii/.nii.gz) to VRDF format specifically for BraTS-style medical data. It performs segmentation followed by VRDF conversion in a single streamlined process, designed for study-based file organization.

## Features

- **REST API**: Simple synchronous HTTP endpoints for file conversion
- **Mandatory Segmentation**: Uses BraTS-style 4D segmentation before conversion
- **Study-based Organization**: Files are organized by study codes
- **VRDF Export**: Converts to Unity-compatible VRDF format using labelmap_weighted4d mode
- **Health Monitoring**: Health check endpoint for service monitoring
- **Automatic Cleanup**: Removes intermediate segmented files after conversion
- **Simple Workflow**: Direct response without task tracking system

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the service:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Or using Docker:

```bash
docker-compose up
```

## API Endpoints

### Health Check

```
GET /health
```

Returns the health status of the service.

**Response:**

```json
{
  "status": "healthy",
  "service": "vrdf-service"
}
```

### Convert File

```
POST /convert
```

**Request Body:**

```json
{
  "study_code": "patient123",
  "filename": "patient123-t1n.nii.gz",
  "seg_filename": "patient123-seg.nii.gz",
  "config_path": "./config.json"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Segmentation and conversion completed for patient123-t1n.nii.gz",
  "vrdf_file": "patient123-t1n_lw.vrdf"
}
```

## File Organization

The service expects files to be organized as follows:

```
storage/
  studies/
    {study_code}/
      {filename}.nii.gz           # Input modality file
      {seg_filename}.nii.gz       # Segmentation mask file
      {filename}_lw.vrdf          # Generated VRDF output
```

## Process Flow

1. **Input Validation**: Validates that both input NIfTI file and segmentation file exist in the study directory
2. **Segmentation Processing**: Creates 4D segmented volume using BraTS-style processing (brain regions + tumor labels)
3. **VRDF Conversion**: Converts the segmented 4D volume to Unity-compatible VRDF format using labelmap_weighted4d mode
4. **Automatic Cleanup**: Removes intermediate segmented .nii.gz files to save disk space
5. **Direct Response**: Returns the final VRDF filename immediately (no task tracking)

## Configuration

The service uses a JSON configuration file (`config.json`) to define transfer functions for different label types:

```json
{
  "transfer_function": {
    "labels": {
      "0": { "name": "background", "color": [0.0, 0.0, 0.0], "alpha": 0.0 },
      "1": { "name": "Brain", "color": [0.8, 0.8, 0.8], "alpha": 0.1 },
      "2": {
        "name": "Enhancing tumor",
        "color": [0.0, 1.0, 0.0],
        "alpha": 0.4
      },
      "3": { "name": "Core tumor", "color": [0.0, 0.0, 1.0], "alpha": 0.5 },
      "4": { "name": "Glioma", "color": [1.0, 1.0, 0.0], "alpha": 1.0 }
    }
  }
}
```

## Usage Examples

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Convert file with segmentation
curl -X POST http://localhost:8000/convert \
  -H "Content-Type: application/json" \
  -d '{
    "study_code": "patient123",
    "filename": "patient123-t1n.nii.gz",
    "seg_filename": "patient123-seg.nii.gz",
    "config_path": "./config.json"
  }'
```

### Using Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Convert file
data = {
    "study_code": "patient123",
    "filename": "patient123-t1n.nii.gz",
    "seg_filename": "patient123-seg.nii.gz",
    "config_path": "./config.json"
}

response = requests.post("http://localhost:8000/convert", json=data)
result = response.json()

if result["success"]:
    print(f"VRDF file created: {result['vrdf_file']}")
else:
    print(f"Conversion failed: {result['message']}")
```

## Docker Support

The service includes Docker configuration for easy deployment:

- **Dockerfile**: Builds the service container
- **docker-compose.yml**: Orchestrates the service with volume mounts
- **External network**: Connects to `holonauts-network`
- **Volume mounting**: Maps study data from external volume

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run manually
docker build -t vrdf-service .
docker run -p 8000:8000 -v /path/to/storage:/app/storage vrdf-service
```

## Error Handling

The service provides detailed error messages for common issues:

- **File not found**: When input NIfTI or segmentation files don't exist
- **Invalid study code**: When the study directory is not accessible
- **Segmentation failures**: When the 4D segmentation process fails
- **VRDF conversion errors**: When the encoding process encounters issues

## Performance Notes

- The segmentation and VRDF conversion process is CPU-intensive
- Large NIfTI files may take several minutes to process
- Intermediate files are automatically cleaned up to conserve disk space
- The service processes requests synchronously (one at a time)

## Dependencies

- **FastAPI**: Web framework for the REST API
- **uvicorn**: ASGI server for serving the application
- **nibabel**: NIfTI file reading and writing
- **numpy**: Numerical operations for medical imaging data
- **pydantic**: Data validation and request/response models

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure the `encode.py` module is in the correct path
2. **File permissions**: Check that the service has read/write access to the storage directory
3. **Memory issues**: Large NIfTI files may require sufficient RAM for processing
4. **Path issues**: Verify that study directories and files exist before making requests

### Logs

The service logs important events including:

- File processing start/completion
- Error details with stack traces
- Cleanup operations
- Performance timing information
