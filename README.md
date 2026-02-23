# Invoice Processing API

Converts PDF invoices into structured JSON via a 5-step pipeline (PDF → Markdown → CSV → Processed CSV → JSON), served over a FastAPI endpoint.

---

## Pipeline Overview

```
invoice.pdf
    │
    ▼  Step 1 – pdf_to_markdown.py
invoice.md
    │
    ▼  Step 2 – markdown_to_csv.py
invoice.csv
    │
    ▼  Step 3 – preprocessing.py
invoice_processed.csv
    │
    ▼  Step 4 – verify_totals.py
invoice_validation.csv
    │
    ▼  Step 5 – csv_to_json.py
invoice_processed.json  +  invoice_validation.json
```

All outputs are saved under `processed_outputs/<uuid>/`.

---

## Requirements

```bash
pip install -r requirements.txt
# or, if using the virtual environment:
.venv\Scripts\pip install -r requirements.txt
```

Key dependencies: `fastapi`, `uvicorn`, `docling`, `python-multipart`.

---

## Running Locally

### Option A — Run the full pipeline from the command line (no API needed)

```bash
# Using venv Python (recommended)
.venv\Scripts\python.exe run_pipeline.py "pdf_sample\invoice.pdf"

# With a custom output folder
.venv\Scripts\python.exe run_pipeline.py "pdf_sample\invoice.pdf" -o "my_output"
```

### Option B — Start the API server

```bash
# Direct
python api.py

# Or via uvicorn (with hot-reload for development)
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The API is now available at:

| URL                           | Purpose                  |
| ----------------------------- | ------------------------ |
| `http://localhost:8000`       | Base URL                 |
| `http://localhost:8000/docs`  | Swagger UI (interactive) |
| `http://localhost:8000/redoc` | ReDoc docs               |

---

## API Reference

### `POST /process-invoice/`

Upload a PDF invoice and receive structured JSON back.

**Request**

| Field  | Type                  | Description             |
| ------ | --------------------- | ----------------------- |
| `file` | `multipart/form-data` | The PDF file to process |

**Success Response `200`**

```json
{
  "status": "success",
  "job_id": "c86d8e52-1a2b-...",
  "processed_data": [
    {
      "Page": 1,
      "Product Code": "1002379",
      "Product Description": "SUNPLY SK NEXTA SERUM ESSN 70G",
      "Trans. Date": "28/11/2025",
      "WM Sales Qty": 1.0,
      "EM Sales Qty": 0.0,
      "Rate": 8.89,
      "Adj. Basis": "%of Sales",
      "Total Invoiced": 6.8,
      "Supplier ID": "1049785110",
      "Invoice No": "10596752",
      "Create Date": "24/11/2025 To 30/11/2025"
    }
  ],
  "validation_data": [
    {
      "Product Code": "1002379",
      "Status": "MATCH",
      "CSV Total": 13.6,
      "MD Total": 13.6
    }
  ]
}
```

**Error Responses**

| Code  | Meaning                                                                |
| ----- | ---------------------------------------------------------------------- |
| `499` | Client disconnected – pipeline was cancelled and temp files cleaned up |
| `500` | Pipeline error or JSON parse failure                                   |
| `404` | Output JSON file not found after pipeline run                          |

---

## Usage Examples

### cURL

```bash
curl -X POST "http://localhost:8000/process-invoice/" \
     -F "file=@path/to/invoice.pdf"
```

### Python (`requests`)

```python
import requests

url = "http://localhost:8000/process-invoice/"

with open("path/to/invoice.pdf", "rb") as f:
    response = requests.post(url, files={"file": f})

if response.status_code == 200:
    result = response.json()
    print("Job ID:", result["job_id"])
    print("Rows:", len(result["processed_data"]))
else:
    print("Error:", response.text)
```

### JavaScript / Browser

```javascript
const formData = new FormData();
formData.append("file", document.querySelector('input[type="file"]').files[0]);

const response = await fetch("http://localhost:8000/process-invoice/", {
  method: "POST",
  body: formData,
});

const result = await response.json();
console.log("Job ID:", result.job_id);
console.log("Data:", result.processed_data);
```

### Postman

1. Method → **POST**
2. URL → `http://localhost:8000/process-invoice/`
3. Body tab → **form-data**
4. Key: `file`, type: **File**
5. Value: select your PDF
6. **Send**

---

## Exposing the API Online (ngrok)

Use [ngrok](https://ngrok.com/) to give the local server a public HTTPS URL without any deployment.

### One-time Setup

1. [Download ngrok](https://ngrok.com/download) and place `ngrok.exe` somewhere accessible (e.g. `C:\ngrok\ngrok.exe`).
2. Sign up at ngrok.com and copy your auth token.
3. Authenticate once:
   ```bash
   C:\ngrok\ngrok.exe config add-authtoken <YOUR_TOKEN>
   ```

### Every Time You Want to Go Live

**Terminal 1 — Start the API:**

```bash
python api.py
```

**Terminal 2 — Start ngrok tunnel:**

```bash
C:\ngrok\ngrok.exe http 8000
```

ngrok will print something like:

```
Forwarding  https://a1b2-123-456-789.ngrok-free.app -> http://localhost:8000
```

Share that HTTPS URL with whoever needs it. Requests to it are forwarded to your local server in real time.

**Example — call the public URL:**

```bash
curl -X POST "https://a1b2-123-456-789.ngrok-free.app/process-invoice/" \
     -F "file=@invoice.pdf"
```

> **Note:** The free ngrok URL changes every time you restart ngrok. For a stable URL, use a paid ngrok plan or deploy to a cloud service (see below).

---

## Deploying to the Cloud (optional)

If you need a permanent public endpoint without running ngrok, deploy to any Python-friendly host:

| Platform              | How                                                                                           |
| --------------------- | --------------------------------------------------------------------------------------------- |
| **Railway**           | Connect your GitHub repo → set start command to `uvicorn api:app --host 0.0.0.0 --port $PORT` |
| **Render**            | New Web Service → same start command                                                          |
| **Fly.io**            | `fly launch` → set `CMD` in `Dockerfile` to `uvicorn api:app --host 0.0.0.0 --port 8080`      |
| **Azure / AWS / GCP** | Deploy as a container or App Service; expose port `8000`                                      |

---

## Notes

- **Cancellation**: If the client disconnects mid-request, the pipeline is cancelled and the output directory is cleaned up automatically.
- **Concurrency**: Each request gets a unique UUID job directory, so multiple uploads can run simultaneously without interference.
- **Intermediate files**: All intermediate files (`.md`, `.csv`, `.json`) are kept in `processed_outputs/<job_id>/` for debugging.
