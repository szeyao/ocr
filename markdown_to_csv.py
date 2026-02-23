#!/usr/bin/env python3
"""
Convert Markdown invoice tables to CSV format.

This script parses the Markdown file containing invoice tables and converts
them to a CSV file with the following columns:
- Page
- Product Code
- Product Description
- Trans. Date
- WM Sales Qty
- EM Sales Qty
- Rate
- Adj. Basis
- Total Invoiced
- Supplier ID
- Invoice No
- Create Date
"""

import re
import csv
import sys
from pathlib import Path


def is_page_boundary(text: str) -> bool:
    """Detect a page boundary via the <!-- image --> marker between pages."""
    return '<!-- image -->' in text


def extract_metadata(lines: list) -> dict:
    """
    Extract metadata from the markdown file header.
    
    Returns a dict with:
        - supplier_id: Supplier ID
        - invoice_no: Invoice Number
        - create_date: Invoice Create Date range
    """
    metadata = {
        'supplier_id': '',
        'invoice_no': '',
        'create_date': ''
    }
    
    # Search in the first 30 lines for metadata
    for line in lines[:30]:
        line = line.strip()
        
        # Extract Create Date from "For Invoice Create Date DD/MM/YYYY To DD/MM/YYYY"
        if 'For Invoice Create Date' in line:
            match = re.search(r'For Invoice Create Date\s+(\d{2}/\d{2}/\d{4}\s+To\s+\d{2}/\d{2}/\d{4})', line)
            if match:
                metadata['create_date'] = match.group(1)
        
        # Extract Supplier ID (matches exactly 10 digits on a line)
        if re.match(r'^\d{10}$', line):
            metadata['supplier_id'] = line
        
        # Extract Invoice No (matches exactly 8 digits on a line)
        if re.match(r'^\d{8}$', line):
            metadata['invoice_no'] = line
    
    return metadata


def parse_markdown_to_csv(markdown_file: Path, csv_file: Path):
    """
    Parse Markdown invoice file and convert to CSV.
    
    Args:
        markdown_file: Path to input Markdown file
        csv_file: Path to output CSV file
    """
    with open(markdown_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Extract metadata from the file header
    metadata = extract_metadata(lines)
    
    # CSV output
    csv_rows = []
    
    # State tracking
    # Page counter starts at 0; it is incremented each time we encounter a
    # <!-- image --> marker, which appears at the top of every page section.
    current_page = 0
    in_table = False
    current_product_code = ""
    current_product_desc = ""
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Detect page boundary: <!-- image --> appears once per page at the top.
        # We increment the page number here so that all table rows that follow
        # are tagged with the correct page number.
        if is_page_boundary(line):
            current_page += 1
            in_table = False
            current_product_code = ""
            current_product_desc = ""
            i += 1
            continue
        
        # Detect table separator (e.g., |---|---|)
        if re.match(r'^\s*\|[\s\-:|]+\|\s*$', line):
            in_table = True
            i += 1
            continue
        
        # Check if we're in a table and this is a data row
        if in_table and line.startswith('|') and not line.startswith('|---'):
            # Parse table row
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            
            # Skip if this is a header row
            if len(cells) >= 8 and 'Product Code' in cells[0]:
                i += 1
                continue
            
            # Skip empty rows or malformed rows
            if len(cells) < 8:
                i += 1
                continue
            
            # Skip "Item Total:" rows (we don't need subtotals in CSV)
            if 'Item Total:' in cells[1]:
                i += 1
                continue
            
            # Skip "Total Amount:" rows
            if 'Total Amount:' in cells[1]:
                i += 1
                continue
            
            # Extract data
            product_code = cells[0].strip()
            product_desc = cells[1].strip()
            trans_date = cells[2].strip()
            wm_sales_qty = cells[3].strip()
            em_sales_qty = cells[4].strip()
            rate = cells[5].strip()
            adj_basis = cells[6].strip()
            total_invoiced = cells[7].strip()
            
            # Update current product code and description if present
            if product_code:
                current_product_code = product_code
            if product_desc and product_desc != 'Item Total:':
                current_product_desc = product_desc
            
            # Only add rows with transaction dates (actual data rows)
            if trans_date and trans_date != '':
                csv_rows.append({
                    'Page': current_page,
                    'Product Code': current_product_code,
                    'Product Description': current_product_desc,
                    'Trans. Date': trans_date,
                    'WM Sales Qty': wm_sales_qty,
                    'EM Sales Qty': em_sales_qty,
                    'Rate': rate,
                    'Adj. Basis': adj_basis,
                    'Total Invoiced': total_invoiced,
                    'Supplier ID': metadata['supplier_id'],
                    'Invoice No': metadata['invoice_no'],
                    'Create Date': metadata['create_date']
                })
        else:
            # Not in table anymore
            if in_table and (line == '' or not line.startswith('|')):
                in_table = False
                current_product_code = ""
                current_product_desc = ""
        
        i += 1
    
    # Write to CSV
    if csv_rows:
        fieldnames = [
            'Page',
            'Product Code',
            'Product Description',
            'Trans. Date',
            'WM Sales Qty',
            'EM Sales Qty',
            'Rate',
            'Adj. Basis',
            'Total Invoiced',
            'Supplier ID',
            'Invoice No',
            'Create Date'
        ]
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)
        
        print(f"[SUCCESS] CSV file created: {csv_file}")
        print(f"[SUCCESS] Total rows: {len(csv_rows)}")
    else:
        print("[WARNING] No data rows found in the Markdown file")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python markdown_to_csv.py <markdown_file> [output_csv]")
        print("\nExample:")
        print("  python markdown_to_csv.py invoice.md")
        print("  python markdown_to_csv.py invoice.md output.csv")
        sys.exit(1)
    
    markdown_file = Path(sys.argv[1])
    
    if not markdown_file.exists():
        print(f"[ERROR] File not found: {markdown_file}")
        sys.exit(1)
    
    # Determine output CSV file
    if len(sys.argv) >= 3:
        csv_file = Path(sys.argv[2])
    else:
        csv_file = markdown_file.with_suffix('.csv')
    
    print(f"Converting: {markdown_file}")
    print(f"Output to: {csv_file}")
    print()
    
    parse_markdown_to_csv(markdown_file, csv_file)


if __name__ == "__main__":
    main()
