import shutil
import os
import uuid
import sys
import json
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from run_pipeline import run_pipeline

# Ensure the current directory is in sys.path
sys.path.append(str(Path(__file__).parent))

app = FastAPI(title="Invoice Processing API")

# Permanent storage for outputs if you want them to persist, 
# or keep using temp_jobs for one-time downloads.
OUTPUT_ROOT = Path("processed_outputs")
OUTPUT_ROOT.mkdir(exist_ok=True)

@app.post("/process-invoice/")
async def process_invoice(file: UploadFile = File(...)):
    """
    1. Saves file to unique dir.
    2. Runs pipeline.
    3. Returns both processed and validation JSON data.
    """
    
    job_id = str(uuid.uuid4())
    temp_dir = OUTPUT_ROOT / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_path = temp_dir / file.filename
    
    # 1. Save Uploaded File
    try:
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # 2. Run Pipeline
    try:
        # Note: run_pipeline now also generates JSON files
        success = run_pipeline(str(pdf_path), output_dir=str(temp_dir))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")
    
    if not success:
        raise HTTPException(status_code=500, detail="Pipeline failed to process the invoice.")

    # 3. Locate the JSON files
    # Based on the pipeline, files are named: [filename]_processed.json and [filename]_validation.json
    base_name = Path(file.filename).stem
    processed_json_name = f"{base_name}_processed.json"
    validation_json_name = f"{base_name}_validation.json"
    processed_json_path = temp_dir / processed_json_name
    validation_json_path = temp_dir / validation_json_name

    # 4. Read and Return JSON Data
    try:
        if not processed_json_path.exists():
            raise HTTPException(status_code=404, detail="Processed JSON not found.")
        if not validation_json_path.exists():
            raise HTTPException(status_code=404, detail="Validation JSON not found.")
        
        # Read both JSON files
        with open(processed_json_path, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)
        
        with open(validation_json_path, 'r', encoding='utf-8') as f:
            validation_data = json.load(f)
        
        # Return both JSON datasets
        return JSONResponse(content={
            "status": "success",
            "job_id": job_id,
            "processed_data": processed_data,
            "validation_data": validation_data
        })
    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading JSON files: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 