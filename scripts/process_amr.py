"""
AMR Processing Script for GraPES Evaluation
- Processes CSV files containing AMR annotations
- Extracts and cleans AMR graphs from specified columns
- Validates AMR syntax using penman library
- Handles duplicate triples and invalid graphs
"""

import re
import pandas as pd
from penman import decode, DecodeError
from collections import defaultdict
import os
import argparse

def clean_amr(amr_str):
    """
    Clean AMR string with enhanced fixes:
    1. Fix multi-word node names
    2. Ensure space after roles
    3. Balance parentheses
    4. Remove extra closing parentheses
    """
    # Remove ::snt line and empty lines
    lines = [line.strip() for line in amr_str.split('\n') if line.strip()]
    if lines and lines[0].startswith("# ::snt"):
        lines = lines[1:]
    
    cleaned_lines = []
    for line in lines:
        # Fix multi-word node names (micro biology → micro_biology)
        if line.startswith("(") and "/" in line:
            parts = line.split("/", 1)
            node_name = parts[1].strip().replace(" ", "_")
            line = f"{parts[0]}/{node_name}"
        
        # Add space after roles (:ARG0(... → :ARG0 (...))
        line = re.sub(r"(:[\w-]+)(?=[^\s/])", r"\1 ", line)
        
        cleaned_lines.append(line)
    
    # Join lines and fix parentheses balance
    cleaned = "\n".join(cleaned_lines)
    
    # Add missing closing parentheses for node definitions
    cleaned = re.sub(r"(\([a-z0-9]+\s+/[^)]+)(\n|$)", r"\1)\2", cleaned)
    
    # Remove extra closing parentheses
    stack = []
    fixed = []
    for char in cleaned:
        if char == '(':
            stack.append(char)
            fixed.append(char)
        elif char == ')':
            if stack:
                stack.pop()
                fixed.append(char)
        else:
            fixed.append(char)
    
    # Add missing closing parentheses at the end
    return ''.join(fixed) + ')' * len(stack)

def remove_duplicate_triples(amr_str):
    """
    Remove duplicate triples while preserving order
    Returns cleaned AMR string and number of duplicates removed
    """
    seen = set()
    cleaned_lines = []
    duplicates_removed = 0
    
    for line in amr_str.split('\n'):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            cleaned_lines.append(line)
            continue
            
        # Check for duplicate triple patterns
        if stripped in seen:
            duplicates_removed += 1
            continue
            
        seen.add(stripped)
        cleaned_lines.append(line)
    
    return "\n".join(cleaned_lines), duplicates_removed

def validate_amr(amr_str):
    """Validate AMR syntax and return (is_valid, cleaned_amr)"""
    try:
        decode(amr_str)
        return True, amr_str
    except DecodeError:
        # Try to fix common errors
        try:
            # Add missing closing parenthesis
            fixed = amr_str + ")" * (amr_str.count("(") - amr_str.count(")"))
            decode(fixed)
            return True, fixed
        except:
            # Fallback to dummy AMR
            return False, "(g / gggggg)"
    except Exception:
        return False, "(g / gggggg)"

def process_csv(input_csv, output_dir):
    """
    Main processing function:
    1. Read input CSV
    2. Process specified AMR columns
    3. Save cleaned AMRs to output directory
    4. Generate validation report
    """
    # Validate input file
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Read CSV data
    df = pd.read_csv(input_csv)
    
    # Process each AMR column
    results = {}
    for col in ['amr_graph', 'generated_amr']:
        if col not in df.columns:
            raise ValueError(f"Column {col} not found in CSV")
            
        valid_count = 0
        invalid_count = 0
        total_duplicates = 0
        
        output_file = os.path.join(output_dir, f"{col}.txt")
        
        with open(output_file, "w") as f:
            for amr in df[col]:
                # Clean AMR
                cleaned = clean_amr(str(amr))
                
                # Remove duplicates
                cleaned, duplicates = remove_duplicate_triples(cleaned)
                total_duplicates += duplicates
                
                # Validate
                is_valid = validate_amr(cleaned)
                
                if is_valid:
                    valid_count += 1
                    f.write(cleaned + "\n\n")
                else:
                    invalid_count += 1
                    f.write(f"# INVALID AMR\n{cleaned}\n\n")
        
        results[col] = {
            'total': len(df),
            'valid': valid_count,
            'invalid': invalid_count,
            'duplicates_removed': total_duplicates
        }
    
    # Print validation report
    print("\nValidation Report:")
    for col, stats in results.items():
        print(f"\nColumn: {col}")
        print(f"  Total AMRs: {stats['total']}")
        print(f"  Valid AMRs: {stats['valid']} ({stats['valid']/stats['total']:.1%})")
        print(f"  Invalid AMRs: {stats['invalid']} ({stats['invalid']/stats['total']:.1%})")
        print(f"  Duplicates removed: {stats['duplicates_removed']}")

if __name__ == "__main__":
    # Configure command-line arguments
    parser = argparse.ArgumentParser(
        description="Process AMR CSV files for GraPES evaluation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--csv",
        required=True,
        help="Path to input CSV file containing AMR data"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for processed AMR files"
    )
    
    args = parser.parse_args()
    
    # Run main processing
    try:
        process_csv(args.csv, args.output)
        print("\nProcessing completed successfully")
    except Exception as e:
        print(f"\nError processing file: {str(e)}")
        exit(1)