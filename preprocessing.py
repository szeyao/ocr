import pandas as pd
import argparse
import os
import sys

def process_csv(file_path, output_path=None):
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print(f"Processing: {file_path}")
    
    # Load the data
    df = pd.read_csv(file_path)

    # Forward fill Product Code and convert to integer to remove decimals
    # Using 'Int64' (capital I) allows us to keep the column as integers even if there were NaNs
    if 'Product Code' in df.columns:
        df['Product Code'] = df['Product Code'].ffill()
        df['Product Code'] = pd.to_numeric(df['Product Code'], errors='coerce').astype('Int64')
    
    # Logic to combine unique descriptions within each product group
    def combine_descriptions(group):
        if 'Product Description' not in group.columns:
            return group
            
        descs = group['Product Description'].dropna().unique()
        
        if len(descs) >= 2:
            d1, d2 = str(descs[0]), str(descs[1])
            if d1.strip().lower() != d2.strip().lower():
                group['Product Description'] = f"{d1} {d2}"
            else:
                group['Product Description'] = d1
        elif len(descs) == 1:
            group['Product Description'] = descs[0]
            
        return group

    # Apply grouping and forward fill description
    if 'Product Code' in df.columns:
        # Suppress deprecation warning if possible or just let it be
        df = df.groupby('Product Code', group_keys=False).apply(combine_descriptions)
        if 'Product Description' in df.columns:
            df['Product Description'] = df['Product Description'].ffill()

    # Determine output path
    if output_path is None:
        output_path = file_path.replace(".csv", "_processed.csv")
        
    # Save the processed file
    df.to_csv(output_path, index=False)
    print(f"Success! Processed file saved at:\n{output_path}")

def main():
    parser = argparse.ArgumentParser(description='Process invoice CSV data.')
    parser.add_argument('input_file', help='Path to input CSV file')
    parser.add_argument('-o', '--output', help='Path to output CSV file (optional)')
    
    args = parser.parse_args()
    
    process_csv(args.input_file, args.output)

if __name__ == "__main__":
    main()