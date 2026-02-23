import shutil
import subprocess
import sys
import uuid
import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

# Ensure the current directory is in sys.path
sys.path.append(str(Path(__file__).parent))

app = FastAPI(title="Invoice Processing API")

# Permanent storage for outputs
OUTPUT_ROOT = Path("processed_outputs")
OUTPUT_ROOT.mkdir(exist_ok=True)

# Python executable to use (same interpreter that started api.py)
PYTHON = sys.executable


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.post("/process-invoice/")
async def process_invoice(request: Request, file: UploadFile = File(...)):
    """
    1. Saves the uploaded PDF to a unique directory.
    2. Runs the pipeline as a *subprocess* so it can be truly killed if the
       client disconnects (threads cannot be force-stopped; subprocesses can).
    3. Returns both processed_data and validation_data as JSON.

    Cancellation behaviour
    ─────────────────────
    The endpoint polls for client disconnection every 0.5 s.  If the client
    drops (browser closed, network lost, etc.) the subprocess is sent SIGTERM
    (or taskkill on Windows) and the output directory is deleted.
    """

    job_id = str(uuid.uuid4())
    temp_dir = OUTPUT_ROOT / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = temp_dir / file.filename

    # ── 1. Save uploaded file ────────────────────────────────────────────────
    try:
        contents = await file.read()
        pdf_path.write_bytes(contents)
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # ── 2. Launch pipeline as a subprocess ──────────────────────────────────
    # Use subprocess.Popen instead of asyncio.create_subprocess_exec because
    # the latter raises NotImplementedError on Windows under uvicorn's reloader.
    proc = subprocess.Popen(
        [PYTHON, "run_pipeline.py", str(pdf_path), "-o", str(temp_dir)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,   # merge stderr into stdout
        cwd=str(Path(__file__).parent),
    )

    def kill_and_cleanup():
        """Terminate the subprocess and remove its output directory."""
        try:
            proc.kill()
            proc.wait(timeout=5)
        except Exception:
            pass
        shutil.rmtree(temp_dir, ignore_errors=True)

    # ── 3. Wait for subprocess, polling for client disconnect ────────────────
    loop = asyncio.get_event_loop()
    try:
        while proc.poll() is None:
            if await request.is_disconnected():
                await loop.run_in_executor(None, kill_and_cleanup)
                raise HTTPException(
                    status_code=499,
                    detail="Client disconnected – pipeline was cancelled and cleaned up."
                )
            # Give the subprocess 0.5 s then re-check
            try:
                await asyncio.wait_for(
                    loop.run_in_executor(None, proc.wait, 0.5),
                    timeout=1.0,
                )
            except (asyncio.TimeoutError, subprocess.TimeoutExpired):
                pass   # subprocess still running – loop again

    except HTTPException:
        raise
    except Exception as e:
        await loop.run_in_executor(None, kill_and_cleanup)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")

    # ── 4. Check exit code ───────────────────────────────────────────────────
    if proc.returncode != 0:
        # Capture any output for the error message
        stdout_bytes = b""
        if proc.stdout:
            try:
                stdout_bytes = proc.stdout.read()
            except Exception:
                pass
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline failed (exit {proc.returncode}): "
                   f"{stdout_bytes.decode(errors='replace')[-500:]}"
        )

    # ── 5. Locate output JSON files ──────────────────────────────────────────
    base_name = Path(file.filename).stem
    processed_json_path = temp_dir / f"{base_name}_processed.json"
    validation_json_path = temp_dir / f"{base_name}_validation.json"

    # ── 6. Read and return ───────────────────────────────────────────────────
    try:
        if not processed_json_path.exists():
            raise HTTPException(status_code=404, detail="Processed JSON not found.")
        if not validation_json_path.exists():
            raise HTTPException(status_code=404, detail="Validation JSON not found.")

        processed_data = json.loads(processed_json_path.read_text(encoding="utf-8"))
        validation_data = json.loads(validation_json_path.read_text(encoding="utf-8"))

        return JSONResponse(content={
            "status": "success",
            "job_id": job_id,
            "processed_data": processed_data,
            "validation_data": validation_data,
        })

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading output files: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)