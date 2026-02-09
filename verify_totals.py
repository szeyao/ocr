import pandas as pd
import re
import csv
import argparse
import sys
import os
from pathlib import Path

def parse_markdown_totals(markdown_path):
    """
    Parses the Markdown file to extract 'Item Total' lines and the associated Product Code.
    Returns a dictionary or DataFrame: {ProductCode: {WM_Qty: ..., EM_Qty: ..., Total: ...}}
    """
    totals_data = []
    
    if not os.path.exists(markdown_path):
        print(f"Error: Markdown file not found: {markdown_path}")
        return pd.DataFrame()

    with open(markdown_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_product_code = None
    
    # Simple state machine
    for line in lines:
        if not line.strip().startswith('|'):
            continue
            
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if not cells:
            continue
            
        # Check for header
        if 'Product Code' in cells[0]:
            continue
            
        # Check for separator line (e.g., |---|---|)
        # Often contains only dashes, colons, spaces
        # Must ensure cells[0] is not empty, otherwise we skip Item Total lines which start with empty cell!
        if cells[0] and set(cells[0]) <= {'-', ':', ' '}:
            continue

        # Check for Item Total
        # Based on cleaned file: | | Item Total: | | 155 | 28 | | | 344.04 |
        # cells[1] is 'Item Total:'
        is_item_total = False
        if len(cells) > 1 and 'Item Total' in cells[1]:
            is_item_total = True
        elif len(cells) > 0 and 'Item Total' in cells[0]: # Fallback
            is_item_total = True
            
        if is_item_total:
            if current_product_code:
                try:
                    # Extract values. 
                    # Usually: [0]='', [1]='Item Total:', [2]='', [3]=WM, [4]=EM, [5]='', [6]='', [7]=Total
                    
                    # Helper to clean number strings
                    def clean_num(s):
                        return float(s.replace(',', '').replace(' ', '')) if s.strip() else 0.0

                    # Find position of Sales Qty columns. 
                    wm_qty = 0
                    em_qty = 0
                    total = 0.0
                    
                    if len(cells) >= 8:
                        # Try standard indices
                        try:
                            wm_qty = clean_num(cells[3])
                            em_qty = clean_num(cells[4])
                            total = clean_num(cells[7])
                        except ValueError:
                            pass # parsing error
                            
                    totals_data.append({
                        'Product Code': current_product_code,
                        'MD_WM_Qty': wm_qty,
                        'MD_EM_Qty': em_qty,
                        'MD_Total_Invoiced': total
                    })
                    
                except Exception as e:
                    print(f"Error parsing line for product {current_product_code}: {line}\n{e}")
            
            # Reset product code after finding total
            current_product_code = None 
            
        else:
            # Check if this row defines a new Product Code
            if len(cells) > 0 and cells[0].strip() != '':
                possible_code = cells[0].strip()
                current_product_code = possible_code

    return pd.DataFrame(totals_data)

def verify(csv_path, md_path, output_path):
    # 1. Load CSV and Calculate Sums
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        return

    print(f"Loading Processed CSV: {csv_path}")
    df_csv = pd.read_csv(csv_path)
    
    # Ensure numeric types
    cols_to_sum = ['WM Sales Qty', 'EM Sales Qty', 'Total Invoiced']
    for col in cols_to_sum:
        if col in df_csv.columns:
            if df_csv[col].dtype == 'object':
                 df_csv[col] = df_csv[col].astype(str).str.replace(',', '', regex=False)
            df_csv[col] = pd.to_numeric(df_csv[col], errors='coerce').fillna(0)
    
    # Aggregate
    if 'Product Code' in df_csv.columns and 'Page' in df_csv.columns:
        csv_agg = df_csv.groupby('Product Code').agg({
            'WM Sales Qty': 'sum',
            'EM Sales Qty': 'sum',
            'Total Invoiced': 'sum',
            'Page': ['min', 'max']
        }).reset_index()
        
        # Flatten columns
        csv_agg.columns = ['Product Code', 'CSV_WM_Qty', 'CSV_EM_Qty', 'CSV_Total_Invoiced', 'Page_Min', 'Page_Max']
        
        # Create page range string
        def format_pages(row):
            if row['Page_Min'] == row['Page_Max']:
                return str(row['Page_Min'])
            return f"{row['Page_Min']}-{row['Page_Max']}"
        
        csv_agg['Pages'] = csv_agg.apply(format_pages, axis=1)
        csv_sums = csv_agg[['Product Code', 'CSV_WM_Qty', 'CSV_EM_Qty', 'CSV_Total_Invoiced', 'Pages']]
        csv_sums['Product Code'] = csv_sums['Product Code'].astype(str)
    else:
        print("Error: content missing required columns (Product Code, Page)")
        return

    # 2. Extract Markdown Totals
    print(f"Parsing Markdown Totals: {md_path}")
    md_totals = parse_markdown_totals(md_path)
    if not md_totals.empty:
        md_totals['Product Code'] = md_totals['Product Code'].astype(str)
    else:
        print("Warning: No totals found in Markdown file.")
    
    # 3. Merge and Compare
    print("Comparing...")
    if md_totals.empty:
        merged = csv_sums.copy()
        merged['MD_WM_Qty'] = 0
        merged['MD_EM_Qty'] = 0
        merged['MD_Total_Invoiced'] = 0
    else:
        merged = pd.merge(csv_sums, md_totals, on='Product Code', how='outer')
    
    # Calculate Differences
    merged['Diff_WM_Qty'] = merged['CSV_WM_Qty'] - merged['MD_WM_Qty'].fillna(0)
    merged['Diff_EM_Qty'] = merged['CSV_EM_Qty'] - merged['MD_EM_Qty'].fillna(0)
    merged['Diff_Total_Invoiced'] = merged['CSV_Total_Invoiced'] - merged['MD_Total_Invoiced'].fillna(0)
    
    # Handle missing values
    merged = merged.fillna(0)
    
    # Flag discrepancies
    tolerance = 0.01
    merged['Match_Status'] = 'Match'
    
    mask_diff = (
        (merged['Diff_WM_Qty'].abs() > tolerance) | 
        (merged['Diff_EM_Qty'].abs() > tolerance) | 
        (merged['Diff_Total_Invoiced'].abs() > tolerance)
    )
    merged.loc[mask_diff, 'Match_Status'] = 'Mismatch'
    
    # Reorder columns
    cols = [
        'Pages', 'Product Code', 'Match_Status',
        'CSV_WM_Qty', 'MD_WM_Qty', 'Diff_WM_Qty',
        'CSV_EM_Qty', 'MD_EM_Qty', 'Diff_EM_Qty',
        'CSV_Total_Invoiced', 'MD_Total_Invoiced', 'Diff_Total_Invoiced'
    ]
    # Ensure columns exist (Pages might be 0 if product only in MD)
    for c in cols:
        if c not in merged.columns:
            merged[c] = 0 # or empty string? 0 is safer for now
            
    merged = merged[cols]
    
    # 4. Save Summary
    merged.to_csv(output_path, index=False)
    print(f"Summary saved to: {output_path}")
    
    # Print Mismatches
    mismatches = merged[merged['Match_Status'] == 'Mismatch']
    if not mismatches.empty:
        print(f"\n[WARNING] Found {len(mismatches)} mismatches:")
        print(mismatches[['Product Code', 'Diff_WM_Qty', 'Diff_EM_Qty', 'Diff_Total_Invoiced']])
    else:
        print("\n[SUCCESS] All totals match perfectly!")

    # Print total stats
    print(f"\nTotal Products Processed: {len(merged)}")
    print(f"Total CSV Invoiced Sum: {merged['CSV_Total_Invoiced'].sum():,.2f}")
    print(f"Total MD Invoiced Sum: {merged['MD_Total_Invoiced'].sum():,.2f}")

def main():
    parser = argparse.ArgumentParser(description='Verify invoice totals between CSV and Markdown.')
    parser.add_argument('csv_file', help='Path to processed CSV file')
    parser.add_argument('md_file', help='Path to source Markdown file')
    parser.add_argument('-o', '--output', help='Path to output summary CSV', default='comparison_summary.csv')
    
    args = parser.parse_args()
    
    verify(args.csv_file, args.md_file, args.output)

if __name__ == "__main__":
    main()
