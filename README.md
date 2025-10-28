# VRDF Service

A FastAPI service for converting NIfTI medical imaging files to VRDF format for Unity DVR rendering.

## Overview

This service provides a REST API to convert NIfTI files (.nii/.nii.gz) to VRDF format using different conversion modes. It's designed to work with study-based file organization and supports background processing for large file conversions.

## Features

- **REST API**: Easy-to-use HTTP endpoints for file conversion
- **Background Processing**: Non-blocking conversion with task status tracking
- **Study-based Organization**: Files are organized by study codes
- **Multiple Conversion Modes**: Support for different VRDF export modes
- **Health Monitoring**: Health check endpoint for service monitoring
- **File Download**: Direct download of converted files

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

### Convert File

```
POST /convert
```

**Request Body:**

```json
{
  "study_code": "study123",
  "filename": "brain_scan.nii.gz",
  "mode": "labelmap_weighted4d",
  "config_path": "./config.json"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Conversion started",
  "task_id": "uuid-task-id",
  "output_file": "/path/to/output.vrdf"
}
```

### Get Task Status

```
GET /convert/status/{task_id}
```

Returns the current status of a conversion task.

### Download Converted File

```
GET /download/{task_id}
```

Downloads the converted VRDF file once the conversion is complete.

## File Organization

The service expects files to be organized as follows:

```
storage/
  studies/
    {study_code}/
      {filename}.nii.gz
      vrdf_output/
        {filename}_converted.vrdf
```

## Conversion Modes

- `labelmap`: Single discrete volume
- `continuous4d`: Continuous volumes (MRI/CT), split along T
- `labelmap_weighted4d`: Labels + tumor weights (fused or split)
- `multi_overlay4d`: One overlay .vrdf per channel

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

### Using the Python Client

```python
from client_example import VRDFClient

client = VRDFClient("http://localhost:8000")

# Check service health
if client.health_check():
    # Convert a file
    result, status = client.convert_file("study123", "brain_scan.nii.gz")

    if status == 200:
        task_id = result['task_id']

        # Wait for completion
        final_status = client.wait_for_completion(task_id)

        if final_status['status'] == 'completed':
            # Download the result
            client.download_file(task_id, "output.vrdf")
```

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Start conversion
curl -X POST http://localhost:8000/convert \
  -H "Content-Type: application/json" \
  -d '{
    "study_code": "study123",
    "filename": "brain_scan.nii.gz",
    "mode": "labelmap_weighted4d"
  }'

# Check status
curl http://localhost:8000/convert/status/{task_id}

# Download file
curl -O http://localhost:8000/download/{task_id}
```

## Original Command Line Tool

The original encode.py script can still be used directly:

```bash
python encode.py --nifti INPUT_FILE --mode labelmap_weighted4d --config config.json --vrdf-out OUTPUT_FILE
```

## Docker Support

The service includes Docker configuration for easy deployment:

- **Dockerfile**: Builds the service container
- **docker-compose.yml**: Orchestrates the service with volume mounts
- **External network**: Connects to `holonauts-network`
- **Volume mounting**: Maps study data from external volume

## Testing

Run the test script to verify the service is working:

```bash
python test_service.py
```

## Dependencies

- FastAPI: Web framework
- uvicorn: ASGI server
- nibabel: NIfTI file handling
- numpy: Numerical operations
- pydantic: Data validation
