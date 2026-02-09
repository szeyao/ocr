#!/usr/bin/env python3
"""
PDF to Markdown Converter using Docling with Table Cleanup
Converts PDF files to Markdown format while preserving all table details across pages.
Includes post-processing to fix table alignment issues.
"""

import sys
import re
from pathlib import Path
from docling.document_converter import DocumentConverter


def clean_markdown_tables(markdown_content: str) -> str:
    """
    Clean up malformed markdown tables.
    
    Args:
        markdown_content: Raw markdown content from Docling
    
    Returns:
        Cleaned markdown content with fixed tables
    """
    lines = markdown_content.split('\n')
    cleaned_lines = []
    in_table = False
    table_col_count = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Detect table separator (e.g., |---|---|)
        if re.match(r'^\s*\|[\s\-:|]+\|\s*$', line):
            in_table = True
            # Count columns from separator
            table_col_count = line.count('|') - 1
            cleaned_lines.append(line)
            i += 1
            continue
        
        # Check if we're in a table
        if in_table and line.strip().startswith('|'):
            # Count pipes in current line
            pipe_count = line.count('|') - 1
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            
            # Check for malformed rows with repetitive content
            # Pattern 1: "166.00 1,134.00 Item Total:" repeated across all columns
            if len(cells) > 0 and len(set(cells)) == 1 and len(cells) > table_col_count:
                # All cells are identical - this is definitely malformed
                # Extract the actual data from the repeated cell
                cell_content = cells[0]
                # Try to parse it as "value1 value2 label:"
                parts = cell_content.split()
                if len(parts) >= 2 and table_col_count > 0:
                    # Reconstruct as proper row: empty cols, then label, then values
                    fixed_cells = [''] * (table_col_count - 2) + [parts[-1]] + [parts[0] if len(parts) > 1 else '']
                    fixed_line = '| ' + ' | '.join(fixed_cells[:table_col_count]) + ' |'
                    cleaned_lines.append(fixed_line)
                    i += 1
                    continue
            
            # Pattern 2: "Item Total:" repeated in first few columns
            if len(cells) >= 3 and cells[0] == cells[1] == cells[2] and 'Item Total' in cells[0]:
                # Reconstruct as proper Item Total row
                # Usually: empty, "Item Total:", empty, qty, qty, empty, empty, total
                if table_col_count == 8:
                    # Find the numeric values in the cells
                    numeric_cells = [c for c in cells if c and c.replace('.', '').replace(',', '').isdigit()]
                    if len(numeric_cells) >= 1:
                        fixed_cells = ['', 'Item Total:', '', '', '', '', '', numeric_cells[-1]]
                        fixed_line = '| ' + ' | '.join(fixed_cells[:table_col_count]) + ' |'
                        cleaned_lines.append(fixed_line)
                        i += 1
                        continue
            
            # Check for too many columns (general case)
            if pipe_count > table_col_count and table_col_count > 0:
                # Try to extract meaningful unique content
                unique_content = []
                seen = set()
                for cell in cells:
                    if cell and cell not in seen:
                        unique_content.append(cell)
                        seen.add(cell)
                
                # If we reduced significantly, use the unique content
                if len(unique_content) <= table_col_count:
                    # Pad with empty cells if needed
                    while len(unique_content) < table_col_count:
                        unique_content.append('')
                    fixed_line = '| ' + ' | '.join(unique_content[:table_col_count]) + ' |'
                    cleaned_lines.append(fixed_line)
                    i += 1
                    continue
                else:
                    # Too many unique values - take first N columns
                    fixed_cells = cells[:table_col_count]
                    fixed_line = '| ' + ' | '.join(fixed_cells) + ' |'
                    cleaned_lines.append(fixed_line)
                    i += 1
                    continue
            
            # Pattern 3: Merged Double Row (Double Dates)
            # Example: | | | 28/11/2025 29/11/2025 | 13.00 18.00 | ...
            if len(cells) > 2:
                # Regex for double date: DD/MM/YYYY DD/MM/YYYY
                date_cell = cells[2].strip()
                double_date_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})', date_cell)
                
                if double_date_match:
                    row1_cells = []
                    row2_cells = []
                    
                    for idx, cell in enumerate(cells):
                        cell = cell.strip()
                        # Date column (idx 2)
                        if idx == 2 and double_date_match:
                            row1_cells.append(double_date_match.group(1))
                            row2_cells.append(double_date_match.group(2))
                            continue
                            
                        # Qty columns (3, 4) - split by space
                        if idx in [3, 4] and ' ' in cell:
                            parts = cell.split()
                            if len(parts) == 2:
                                row1_cells.append(parts[0])
                                row2_cells.append(parts[1])
                                continue
                        
                        # Default: copy values
                        row1_cells.append(cell)
                        row2_cells.append(cell)

                    # Calculate total for Row 1
                    try: 
                        rate = float(row1_cells[5])
                        wm1 = float(row1_cells[3])
                        em1 = float(row1_cells[4])
                        total1 = (wm1 + em1) * rate
                        row1_cells[-1] = f"{total1:.2f}"
                    except:
                        pass
                        
                    cleaned_lines.append('| ' + ' | '.join(row1_cells) + ' |')
                    cleaned_lines.append('| ' + ' | '.join(row2_cells) + ' |')
                    i += 1
                    continue

            # Check for split rows (content split across multiple lines)
            if i + 1 < len(lines) and not lines[i + 1].strip().startswith('|') and not lines[i + 1].strip().startswith('#'):
                # Next line might be continuation
                if len(cells) < table_col_count or (cells and not cells[-1]):
                    next_line = lines[i + 1].strip()
                    if next_line and not next_line.startswith('<!--'):
                        # Append to last non-empty cell or create new cell
                        if cells and cells[-1]:
                            cells[-1] = cells[-1] + ' ' + next_line
                        else:
                            # Find last non-empty cell
                            for j in range(len(cells) - 1, -1, -1):
                                if cells[j]:
                                    cells[j] = cells[j] + ' ' + next_line
                                    break
                        # Pad to correct length
                        while len(cells) < table_col_count:
                            cells.append('')
                        fixed_line = '| ' + ' | '.join(cells[:table_col_count]) + ' |'
                        cleaned_lines.append(fixed_line)
                        i += 2  # Skip next line
                        continue
            
            cleaned_lines.append(line)
        else:
            # Not in table or empty line
            if in_table and (line.strip() == '' or not line.strip().startswith('|')):
                in_table = False
                table_col_count = 0
            cleaned_lines.append(line)
        
        i += 1
    
    return '\n'.join(cleaned_lines)


def convert_pdf_to_markdown(pdf_path: str, output_path: str = None, clean_tables: bool = True) -> str:
    """
    Convert a PDF file to Markdown format using Docling.
    
    Args:
        pdf_path: Path to the input PDF file
        output_path: Optional path for the output Markdown file.
                    If not provided, will use the same name as PDF with .md extension
        clean_tables: Whether to apply table cleanup post-processing
    
    Returns:
        Path to the generated Markdown file
    """
    # Validate input file
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_file.suffix.lower() == '.pdf':
        raise ValueError(f"Input file must be a PDF: {pdf_path}")
    
    # Determine output path
    if output_path is None:
        output_file = pdf_file.parent / "output" / f"{pdf_file.stem}_cleaned.md"
    else:
        output_file = Path(output_path)
    
    # Create output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Converting PDF: {pdf_file}")
    print(f"Output will be saved to: {output_file}")
    
    # Initialize the document converter
    # Docling automatically handles table detection and preservation
    converter = DocumentConverter()
    
    print("Processing document...")
    print("This may take a moment for documents with complex tables...")
    
    # Convert the document
    # Docling will automatically:
    # - Detect and extract tables across pages
    # - Preserve table structure in markdown format
    # - Handle multi-page tables correctly
    result = converter.convert(str(pdf_file))
    
    print("Exporting to Markdown format...")
    
    # Export to Markdown format
    markdown_content = result.document.export_to_markdown()
    
    # Apply table cleanup if requested
    if clean_tables:
        print("Cleaning up table formatting...")
        markdown_content = clean_markdown_tables(markdown_content)
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"\n[SUCCESS] Conversion complete!")
    print(f"[SUCCESS] Markdown file saved: {output_file}")
    print(f"[SUCCESS] File size: {output_file.stat().st_size:,} bytes")
    
    # Print some statistics
    try:
        doc = result.document
        if hasattr(doc, 'pages'):
            num_pages = len(doc.pages)
            num_tables = sum(1 for page in doc.pages for item in page.items if hasattr(item, 'label') and item.label == 'table')
            print(f"\nDocument Statistics:")
            print(f"  - Pages processed: {num_pages}")
            print(f"  - Tables found: {num_tables}")
    except Exception:
        pass  # Skip statistics if not available
    
    return str(output_file)


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_markdown_clean.py <pdf_file> [output_file]")
        print("\nExample:")
        print('  python pdf_to_markdown_clean.py "pdf_sample/WAT-1049785110-ROHTO-MC10596752DN.pdf"')
        print('  python pdf_to_markdown_clean.py "input.pdf" "output/result.md"')
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        convert_pdf_to_markdown(pdf_path, output_path, clean_tables=True)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
