#!/usr/bin/env python3
"""
Split query files by company (CID) - Thai version

This script reads Thai query JSON files and splits them into separate files
per company while maintaining the original structure.

For Thai data: CID = Company symbol (e.g., "CPALL", "KBANK")
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import argparse


def get_company_name(cid: str) -> str:
    """
    Get company name from CID
    For Thai data, CID is the company symbol
    
    Args:
        cid: Company symbol like "CPALL"
    
    Returns:
        Company name (same as input)
    """
    return cid


def split_queries_by_company(input_file: Path, output_dir: Path):
    """
    Split query file by company
    
    Args:
        input_file: Path to input query JSON file
        output_dir: Base output directory
    """
    print(f"\n{'='*80}")
    print(f"Processing: {input_file.name}")
    print(f"{'='*80}")
    
    # Load original queries
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    queries = data.get('queries', [])
    print(f"✓ Loaded {len(queries)} queries")
    
    # Group queries by industry and company
    # Structure: {industry: {company: [queries]}}
    grouped_queries = defaultdict(lambda: defaultdict(list))
    
    for query in queries:
        cid = query['CID']
        industry = query.get('industry', 'Unknown').lower()
        company = get_company_name(cid)
        
        grouped_queries[industry][company].append(query)
    
    # Print summary
    print(f"\n📊 Grouped by industry and company:")
    for industry, companies in sorted(grouped_queries.items()):
        print(f"\n   {industry.upper()}:")
        for company, queries_list in sorted(companies.items()):
            print(f"      • {company}: {len(queries_list)} queries")
    
    # Save queries for each industry/company combination
    print(f"\n💾 Saving company-specific query files...")
    
    total_files = 0
    for industry, companies in grouped_queries.items():
        # Create industry directory
        industry_slug = industry.replace(' ', '_')
        industry_dir = output_dir / industry_slug
        industry_dir.mkdir(parents=True, exist_ok=True)
        
        for company, queries_list in companies.items():
            # Create company-specific query file
            company_data = {
                "queries": queries_list
            }
            
            # Save to file
            company_slug = company.lower().replace(' ', '_')
            output_file = industry_dir / f"queries_{company_slug}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(company_data, f, ensure_ascii=False, indent=2)
            
            print(f"   ✓ {industry_slug}/{output_file.name} ({len(queries_list)} queries)")
            total_files += 1
    
    print(f"\n✅ Split complete!")
    print(f"   Total files created: {total_files}")
    print(f"   Output directory: {output_dir}")
    print(f"{'='*80}\n")


def process_all_query_files(query_dir: str, output_base: str):
    """
    Process all query files in the directory
    
    Args:
        query_dir: Directory containing query files
        output_base: Base output directory name
    """
    base_dir = Path(__file__).resolve().parent
    queries_dir = base_dir / query_dir
    output_dir = base_dir / output_base
    
    if not queries_dir.exists():
        print(f"\n❌ Error: Query directory not found: {queries_dir}")
        return
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*80}")
    print(f"SPLITTING THAI QUERY FILES BY COMPANY")
    print(f"{'='*80}")
    print(f"Input directory: {queries_dir}")
    print(f"Output directory: {output_dir}")
    
    # Find all query JSON files
    query_files = list(queries_dir.glob("queries_*.json"))
    
    if not query_files:
        print(f"\n❌ Error: No query files found in {queries_dir}")
        print(f"   Looking for files matching pattern: queries_*.json")
        return
    
    print(f"\nFound {len(query_files)} query files:")
    for qf in sorted(query_files):
        print(f"   • {qf.name}")
    
    # Process each query file
    for query_file in sorted(query_files):
        split_queries_by_company(query_file, output_dir)
    
    print(f"\n{'='*80}")
    print(f"✅ ALL DONE!")
    print(f"   Processed {len(query_files)} query files")
    print(f"   Results saved to: {output_dir}")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Split Thai query files by company (CID)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process default query directory
  python split_queries_by_company_thai.py
  
  # Process specific query directory
  python split_queries_by_company_thai.py --query-dir queries_thai
  
  # Specify custom output directory
  python split_queries_by_company_thai.py --output queries_by_company_thai
        """
    )
    
    parser.add_argument(
        '--query-dir',
        default='queries_thai',
        help='Query directory name (default: queries_thai)'
    )
    
    parser.add_argument(
        '--output',
        default='queries_by_company_thai',
        help='Output base directory name (default: queries_by_company_thai)'
    )
    
    args = parser.parse_args()
    
    # Process all query files
    process_all_query_files(args.query_dir, args.output)


if __name__ == "__main__":
    main()