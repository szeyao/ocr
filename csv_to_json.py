#!/usr/bin/env python3
"""
CSV to JSON Converter

Converts CSV files to JSON format for easier API consumption.
"""

import csv
import json
from pathlib import Path


def convert_csv_to_json(csv_path, json_path):
    """
    Convert a CSV file to JSON format.
    
    Args:
        csv_path: Path to the input CSV file
        json_path: Path to the output JSON file
    
    Returns:
        bool: True if conversion successful, False otherwise
    """
    try:
        csv_file = Path(csv_path)
        json_file = Path(json_path)
        
        if not csv_file.exists():
            print(f"Error: CSV file not found: {csv_path}")
            return False
        
        # Read CSV and convert to list of dictionaries
        data = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                data.append(row)
        
        # Write to JSON file
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Converted {csv_file.name} to {json_file.name}")
        return True
        
    except Exception as e:
        print(f"Error converting CSV to JSON: {e}")
        return False


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert CSV to JSON')
    parser.add_argument('csv_file', help='Path to the input CSV file')
    parser.add_argument('-o', '--output', help='Output JSON file path (optional)')
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        json_path = args.output
    else:
        csv_path = Path(args.csv_file)
        json_path = csv_path.with_suffix('.json')
    
    success = convert_csv_to_json(args.csv_file, json_path)
    sys.exit(0 if success else 1)
