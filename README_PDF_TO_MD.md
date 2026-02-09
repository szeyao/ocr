# PDF to Markdown Converter

This script uses **Docling** to convert PDF files to Markdown format while preserving all table details across multiple pages.

## Features

- ✅ Converts PDF files to clean Markdown format
- ✅ Preserves table structures across pages
- ✅ Maintains all table data and formatting
- ✅ Handles complex multi-page documents
- ✅ Automatic OCR for scanned documents
- ✅ Simple command-line interface

## Installation

The required dependencies are already installed in your virtual environment:

```bash
# Dependencies (already in pyproject.toml)
docling>=2.71.0
```

## Usage

### 🚀 Recommended: Full Pipeline

Run the end-to-end automation (PDF -> Markdown -> CSV -> Verification):

```bash
.venv\Scripts\python.exe run_pipeline.py "pdf_sample\WAT-1049785110-ROHTO-MC10596752DN.pdf"
```

**Syntax:**

```bash
python run_pipeline.py <pdf_file> [-o output_dir]
```

### Component Scripts (Advanced)

If you only need specific steps, you can run individual scripts:

#### 1. Convert PDF to Markdown

```bash
python pdf_to_markdown.py "input.pdf"
```

**Arguments:**

- `pdf_file` (required): Path to the input PDF file
- `output_file` (optional): Path for the output Markdown file. If not provided, defaults to `<pdf_directory>/output/<pdf_name>.md`

## Example Output

For the sample PDF `WAT-1049785110-ROHTO-MC10596752DN.pdf`:

```
Converting PDF: C:\Users\kkyao\Desktop\ocr\pdf_sample\WAT-1049785110-ROHTO-MC10596752DN.pdf
Output will be saved to: C:\Users\kkyao\Desktop\ocr\pdf_sample\output\WAT-1049785110-ROHTO-MC10596752DN.md
Processing document...
This may take a moment for documents with complex tables...
Exporting to Markdown format...

[SUCCESS] Conversion complete!
[SUCCESS] Markdown file saved: C:\Users\kkyao\Desktop\ocr\pdf_sample\output\WAT-1049785110-ROHTO-MC10596752DN.md
[SUCCESS] File size: 85,134 bytes

Document Statistics:
  - Pages processed: 14
  - Tables found: 14
```

## How It Works

1. **Document Loading**: Docling loads the PDF file using its advanced PDF processing engine
2. **Table Detection**: Automatically detects tables across all pages using TableFormer technology
3. **Structure Preservation**: Maintains table structure, including:
   - Column headers
   - Row data
   - Multi-line cells
   - Tables spanning multiple pages
4. **Markdown Export**: Converts the entire document to clean Markdown format with proper table syntax

## Table Preservation

The script ensures that:

- ✅ All table rows and columns are preserved
- ✅ Multi-page tables are correctly merged
- ✅ Cell data is accurately extracted
- ✅ Table formatting is maintained in Markdown syntax
- ✅ Headers are properly identified

## Output Format

The generated Markdown file includes:

- Document headers and metadata
- Tables in standard Markdown table format
- Text content between tables
- Page markers (if present in the PDF)

Example table in output:

```markdown
| Product Code | Product Description | Trans. Date | Sales Qty WM | Sales Qty EM | Rate | Adj. Basis | Total Invoiced |
| ------------ | ------------------- | ----------- | ------------ | ------------ | ---- | ---------- | -------------- |
| 1002379      | SUNPLY SK NEXTA     | 28/11/2025  | 1            | 0            | 8.89 | %of Sales  | 6.80           |
```

## Troubleshooting

### Issue: Module not found error

**Solution**: Make sure you're using the virtual environment Python:

```bash
.venv\Scripts\python.exe pdf_to_markdown.py <file>
```

### Issue: Conversion takes a long time

**Solution**: This is normal for large PDFs with many tables. The script will show progress messages.

### Issue: Tables not properly formatted

**Solution**: Docling uses advanced AI models for table detection. If tables are very complex or poorly formatted in the PDF, some manual cleanup may be needed.

## Advanced Configuration

The script can be modified to adjust:

- OCR settings (`pipeline_options.do_ocr`)
- Table detection accuracy
- Output format options

See the source code comments in `pdf_to_markdown.py` for details.

## License

This script uses the Docling library. Please refer to Docling's license for usage terms.
