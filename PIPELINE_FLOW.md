# Updated Pipeline Flow

## Pipeline Steps (run_pipeline.py)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Invoice Processing Pipeline                  │
└─────────────────────────────────────────────────────────────────┘

Input: invoice.pdf
   │
   ▼
┌──────────────────────────────────────┐
│ Step 1: PDF → Markdown               │
│ Module: pdf_to_markdown.py           │
│ Output: invoice.md                   │
└──────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────┐
│ Step 2: Markdown → CSV               │
│ Module: markdown_to_csv.py           │
│ Output: invoice.csv                  │
└──────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────┐
│ Step 3: CSV Preprocessing            │
│ Module: preprocessing.py             │
│ Output: invoice_processed.csv        │
└──────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────┐
│ Step 4: Data Verification            │
│ Module: verify_totals.py             │
│ Output: invoice_validation.csv       │
└──────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────┐
│ Step 5: CSV → JSON (NEW!)            │
│ Module: csv_to_json.py               │
│ Outputs:                             │
│   - invoice_processed.json           │
│   - invoice_validation.json          │
└──────────────────────────────────────┘
   │
   ▼
Final Outputs:
  ✓ invoice.md
  ✓ invoice.csv
  ✓ invoice_processed.csv
  ✓ invoice_processed.json     ← NEW
  ✓ invoice_validation.csv
  ✓ invoice_validation.json    ← NEW
```

## API Response (api.py)

```
POST /process-invoice/
   │
   ▼
┌──────────────────────────────────────┐
│ 1. Save uploaded PDF                 │
│ 2. Run pipeline (all 5 steps)        │
│ 3. Read JSON files                   │
│ 4. Return JSON response               │
└──────────────────────────────────────┘
   │
   ▼
Response:
{
  "status": "success",
  "job_id": "uuid-here",
  "processed_data": [
    {
      "Item": "...",
      "Quantity": "...",
      "Unit Price": "...",
      "Total": "..."
    },
    ...
  ],
  "validation_data": [
    {
      "Metric": "...",
      "CSV Value": "...",
      "Markdown Value": "...",
      "Match": "..."
    },
    ...
  ]
}
```

## Key Benefits

1. **JSON Format**: Easy to consume in web apps, mobile apps, and other services
2. **Complete Data**: Both processed invoice items AND validation results
3. **Single Request**: Get everything you need in one API call
4. **Structured**: Well-organized data ready for immediate use
5. **Backward Compatible**: CSV files still generated for legacy systems
