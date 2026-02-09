# Invoice Processing API Documentation

This API wraps the PDF-to-CSV pipeline in a robust FastAPI service, allowing you to process invoices programmatically.

## 🏃 Getting Started

### 1. Start the Server

Run the API using `uvicorn` (the ASGI server):

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

- The API will be available at: `http://localhost:8000`
- **Interactive Docs (Swagger UI)**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🛠️ API Reference

### `POST /process-invoice/`

Uploads a PDF invoice, processes it, and returns the generated files.

**Request:**

- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Body**:
  - `file`: The PDF file (binary).

**Response:**

- **Status**: `200 OK`
- **Content-Type**: `application/json`
- **JSON Body**:
  ```json
  {
    "status": "success",
    "job_id": "c86d8e52-...",
    "processed_data": [
      {
        "Item": "Product Name",
        "Quantity": "10",
        "Unit Price": "25.00",
        "Total": "250.00"
      },
      ...
    ],
    "validation_data": [
      {
        "Metric": "Total Amount",
        "CSV Value": "1250.00",
        "Markdown Value": "1250.00",
        "Match": "Yes"
      },
      ...
    ]
  }
  ```

---

## 💻 Usage Examples

Here is how other systems or users can integrate with the API:

### 1. cURL (Command Line)

Great for quick testing.

```bash
curl -X POST "http://localhost:8000/process-invoice/" \
     -F "file=@path/to/invoice.pdf"
```

This will return a JSON response with both `processed_data` and `validation_data`.

### 2. Python (using `requests`)

Ideal for integration into other Python apps.

```python
import requests

url = "http://localhost:8000/process-invoice/"
file_path = "path/to/invoice.pdf"

with open(file_path, "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)

if response.status_code == 200:
    result = response.json()
    print("Success!", result["status"])
    print("Job ID:", result["job_id"])
    print("Processed Data:", result["processed_data"])
    print("Validation Data:", result["validation_data"])
else:
    print("Error:", response.text)
```

### 3. JavaScript (Node.js / Browser)

Using the native `fetch` API.

```javascript
const formData = new FormData();
// Assuming 'fileInput' is an <input type="file"> element or a Buffer
formData.append("file", fileInput.files[0]);

const response = await fetch("http://localhost:8000/process-invoice/", {
  method: "POST",
  body: formData,
});

const result = await response.json();
console.log("Status:", result.status);
console.log("Job ID:", result.job_id);
console.log("Processed Data:", result.processed_data);
console.log("Validation Data:", result.validation_data);
```

### 4. Postman

1.  Set Method to **POST**.
2.  Enter URL: `http://localhost:8000/process-invoice/`.
3.  Go to **Body** tab -> Select **form-data**.
4.  Key: `file` (Change type from Text to **File** inside the cell).
5.  Value: Select your PDF file.
6.  Send!

---

## ⚠️ Important Notes

- **JSON Response**: The API returns both processed and validation data as JSON in the response body, making it easy to integrate with other applications.
- **File Storage**: All intermediate files (MD, CSV, JSON) are stored in the `processed_outputs` directory with unique job IDs for reference.
- **Concurrency**: Each request gets a unique Job ID (`uuid`), so multiple users can upload files simultaneously without conflicts.
- **Pipeline Steps**: The pipeline now includes 5 steps:
  1. PDF → Markdown conversion
  2. Markdown → CSV extraction
  3. CSV preprocessing
  4. Data verification
  5. **CSV → JSON transformation** (new!)

Open a first terminal and run your API: python api.py (Keep this terminal running!)
Open a second terminal and start ngrok: "C:\ngrok\ngrok.exe" http 8000
