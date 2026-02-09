#!/usr/bin/env python3
"""
End-to-End Invoice Processing Pipeline

This script orchestrates the full conversion process:
1. PDF -> Markdown (with automated table cleanup)
2. Markdown -> CSV (data extraction)
3. CSV -> Processed CSV (unification and formatting)
4. Verification (CSV vs Markdown totals comparison)
"""

import sys
import argparse
import os
import traceback
from pathlib import Path

# Import the component scripts
# (Assuming they are in the same directory)
try:
    import pdf_to_markdown
    import markdown_to_csv
    import preprocessing
    import verify_totals
    import csv_to_json
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure the following scripts are in the directory:")
    print("  - pdf_to_markdown.py")
    print("  - markdown_to_csv.py")
    print("  - preprocessing.py")
    print("  - verify_totals.py")
    print("  - csv_to_json.py")
    sys.exit(1)

def run_pipeline(pdf_path, output_dir=None):
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return False
        
    print(f"=== Starting Pipeline for: {pdf_file.name} ===")
    
    # 1. Determine Output Paths
    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
    else:
        # Default to 'output' folder in input directory
        out_path = pdf_file.parent / "output"
        out_path.mkdir(parents=True, exist_ok=True)

    base_name = pdf_file.stem
    md_file = out_path / f"{base_name}.md"
    csv_file = out_path / f"{base_name}.csv"
    processed_csv_file = out_path / f"{base_name}_processed.csv"
    validation_file = out_path / f"{base_name}_validation.csv"
    processed_json_file = out_path / f"{base_name}_processed.json"
    validation_json_file = out_path / f"{base_name}_validation.json"
    
    try:
        # Step 1: PDF to Markdown
        print("\n[Step 1/4] Converting PDF to Markdown...")
        pdf_to_markdown.convert_pdf_to_markdown(str(pdf_file), str(md_file), clean_tables=True)
        
        if not md_file.exists():
            print("Error: Markdown file generation failed.")
            return False

        # Step 2: Markdown to CSV
        print("\n[Step 2/4] Extracting Data to CSV...")
        markdown_to_csv.parse_markdown_to_csv(md_file, csv_file)
        
        if not csv_file.exists():
            print("Error: CSV extraction failed.")
            return False
            
        # Step 3: Preprocessing
        print("\n[Step 3/4] Cleaning and Processing CSV...")
        preprocessing.process_csv(str(csv_file), str(processed_csv_file))
        
        if not processed_csv_file.exists():
            print("Error: CSV processing failed.")
            return False
            
        # Step 4: Verification
        print("\n[Step 4/5] Verifying Data Integrity...")
        verify_totals.verify(str(processed_csv_file), str(md_file), str(validation_file))
        
        # Step 5: Convert to JSON
        print("\n[Step 5/5] Converting CSV to JSON...")
        csv_to_json.convert_csv_to_json(str(processed_csv_file), str(processed_json_file))
        csv_to_json.convert_csv_to_json(str(validation_file), str(validation_json_file))
        
        if not processed_json_file.exists() or not validation_json_file.exists():
            print("Warning: JSON conversion may have failed.")
        
        print("\n=== Pipeline Complete! ===")
        print(f"Outputs saved to: {out_path}")
        print(f"1. Markdown:         {md_file.name}")
        print(f"2. Raw CSV:          {csv_file.name}")
        print(f"3. Processed CSV:    {processed_csv_file.name}")
        print(f"4. Processed JSON:   {processed_json_file.name}")
        print(f"5. Validation CSV:   {validation_file.name}")
        print(f"6. Validation JSON:  {validation_json_file.name}")
        
        return True

    except Exception as e:
        print(f"\n[PIPELINE ERROR]: {e}")
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Run full PDF-to-CSV invoice processing pipeline.')
    parser.add_argument('pdf_file', help='Path to the input PDF file')
    parser.add_argument('-o', '--output', help='Output directory (optional)')
    
    args = parser.parse_args()
    
    success = run_pipeline(args.pdf_file, args.output)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
