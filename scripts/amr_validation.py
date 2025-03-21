"""
AMR Validation Script (Fixed Version)
- Handles malformed AMR content
- Better error recovery
"""

from penman import decode
from collections import defaultdict
import argparse
import sys

def analyze_amr_file(input_path):
    """
    Analyze AMR file with enhanced error handling
    """
    try:
        with open(input_path, 'r') as f:
            content = f.read().split('\n\n')
    except FileNotFoundError:
        print(f"Error: File not found - {input_path}", file=sys.stderr)
        sys.exit(1)

    total = len(content)
    valid = 0
    duplicates = defaultdict(int)
    error_lines = []

    for idx, amr_str in enumerate(content):
        amr_str = amr_str.strip()
        if not amr_str:
            continue
            
        try:
            graph = decode(amr_str)
            valid += 1
            # Track duplicates within single AMR
            seen = set()
            for t in graph.triples:
                key = (t.source, t.relation, t.target)
                if key in seen:
                    duplicates[key] += 1
                seen.add(key)
        except Exception as e:
            error_lines.append(idx+1)  # 1-based indexing

    # Cross-AMR duplicate detection
    cross_duplicates = sum(1 for v in duplicates.values() if v > 1)
    
    return (total, valid, cross_duplicates, error_lines)

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='AMR file validation and analysis tool',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('input_file', help='Path to AMR file to analyze')
    parser.add_argument('--show-errors', action='store_true',
                       help='Display line numbers with errors')
    args = parser.parse_args()

    total, valid, duplicates, errors = analyze_amr_file(args.input_file)
    
    print(f"AMR Analysis Report: {args.input_file}")
    print(f"Total graphs: {total}")
    print(f"Valid graphs: {valid} ({valid/total:.1%})")
    print(f"Invalid graphs: {total-valid} (lines: {len(errors)})")
    print(f"Duplicate triples: {duplicates}")
    
    if args.show_errors and errors:
        print("\nInvalid AMR locations:")
        print("Line numbers:", ', '.join(map(str, errors)))

if __name__ == "__main__":
    main()