import shutil
import os
import uuid
import sys
import json
import asyncio
import functools
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from run_pipeline import run_pipeline

# Ensure the current directory is in sys.path
sys.path.append(str(Path(__file__).parent))

app = FastAPI(title="Invoice Processing API")

# Permanent storage for outputs
OUTPUT_ROOT = Path("processed_outputs")
OUTPUT_ROOT.mkdir(exist_ok=True)

# Thread pool for running the blocking pipeline in a non-blocking way
_executor = ThreadPoolExecutor()


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.post("/process-invoice/")
async def process_invoice(request: Request, file: UploadFile = File(...)):
    """
    1. Saves file to unique dir.
    2. Runs pipeline in a thread, monitoring for client disconnection.
    3. Returns both processed and validation JSON data.

    If the client disconnects before the pipeline finishes, the endpoint
    returns early and the output directory is cleaned up.
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
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # 2. Run Pipeline – in a thread so we can watch for client disconnect
    loop = asyncio.get_event_loop()

    # Submit the blocking pipeline call to the thread-pool
    pipeline_fn = functools.partial(run_pipeline, str(pdf_path), output_dir=str(temp_dir))
    future = loop.run_in_executor(_executor, pipeline_fn)

    try:
        while not future.done():
            # Check whether the client has disconnected
            if await request.is_disconnected():
                # Cancel the future (best-effort; the thread may still finish)
                future.cancel()
                shutil.rmtree(temp_dir, ignore_errors=True)
                raise HTTPException(
                    status_code=499,
                    detail="Client disconnected – pipeline cancelled."
                )
            # Poll every 0.5 s so we are responsive to disconnects
            await asyncio.sleep(0.5)

        # Retrieve the result (re-raises any exception thrown in the thread)
        success = await future

    except HTTPException:
        raise  # Re-raise cancellation HTTPException as-is
    except asyncio.CancelledError:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=499, detail="Request was cancelled.")
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")

    if not success:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail="Pipeline failed to process the invoice.")

    # 3. Locate the JSON files
    base_name = Path(file.filename).stem
    processed_json_path = temp_dir / f"{base_name}_processed.json"
    validation_json_path = temp_dir / f"{base_name}_validation.json"

    # 4. Read and Return JSON Data
    try:
        if not processed_json_path.exists():
            raise HTTPException(status_code=404, detail="Processed JSON not found.")
        if not validation_json_path.exists():
            raise HTTPException(status_code=404, detail="Validation JSON not found.")

        with open(processed_json_path, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)

        with open(validation_json_path, 'r', encoding='utf-8') as f:
            validation_data = json.load(f)

        return JSONResponse(content={
            "status": "success",
            "job_id": job_id,
            "processed_data": processed_data,
            "validation_data": validation_data
        })

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading JSON files: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)