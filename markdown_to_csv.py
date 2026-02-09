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
"""

import re
import csv
import sys
from pathlib import Path


def extract_page_number(text: str) -> int:
    """Extract page number from text like '/ 4 14' or 'Page 4'."""
    # Pattern: "/ X 14" where X is the page number
    match = re.search(r'/\s*(\d+)\s+14', text)
    if match:
        return int(match.group(1))
    
    # Pattern: "Page X"
    match = re.search(r'Page\s*(\d+)', text)
    if match:
        return int(match.group(1))
    
    return None


def parse_markdown_to_csv(markdown_file: Path, csv_file: Path):
    """
    Parse Markdown invoice file and convert to CSV.
    
    Args:
        markdown_file: Path to input Markdown file
        csv_file: Path to output CSV file
    """
    with open(markdown_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # CSV output
    csv_rows = []
    
    # State tracking
    current_page = 1
    in_table = False
    current_product_code = ""
    current_product_desc = ""
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Extract page number
        page_num = extract_page_number(line)
        if page_num:
            current_page = page_num
        
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
                    'Total Invoiced': total_invoiced
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
            'Total Invoiced'
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
