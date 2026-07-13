#!/usr/bin/env python3
"""
Split query files by company (CID)

This script reads query JSON files and splits them into separate files
per company while maintaining the original structure.
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import argparse


# =====================================================
# CID to Company Name Mapping (Same as results script)
# =====================================================
CID_TO_COMPANY = {
    # Exact matches (with or without .pdf extension)
    "06-21_gb-_lvmh_rse2022.pdf": "LVMH",
    "06-21_gb-_lvmh_rse2022": "LVMH",
    
    "2022-Baytex-ESG-Report-FINAL.pdf": "Baytex_Energy",
    "2022-Baytex-ESG-Report-FINAL": "Baytex_Energy",
    
    "Burberry_2020-21_ESG.pdf": "Burberry",
    "Burberry_2020-21_ESG": "Burberry",
    
    "CanNickel-ESG-Report2023-print.pdf": "Canada_Nickel",
    "CanNickel-ESG-Report2023-print": "Canada_Nickel",
    
    "esg-2022.pdf": "Greenergy",
    "esg-2022": "Greenergy",
    
    "esg-report-2022.pdf": "Arab_Bank",
    "esg-report-2022": "Arab_Bank",
    
    "ESG-Report-2022-Final_ADA.pdf": "US_Bancorp",
    "ESG-Report-2022-Final_ADA": "US_Bancorp",
    
    "ESGReport2022.pdf": "Standard_Bank",
    "ESGReport2022": "Standard_Bank",
    
    "Kering_Sustainability_Progress_Report_2020_2023_7d06687606.pdf": "Kering",
    "Kering_Sustainability_Progress_Report_2020_2023_7d06687606": "Kering",
}


def get_company_name(cid: str) -> str:
    """
    Extract company name from CID (PDF filename) using mapping table
    
    Args:
        cid: PDF filename like "2022-Baytex-ESG-Report-FINAL.pdf"
    
    Returns:
        Company name like "Baytex_Energy"
    """
    # Try exact match first (with .pdf)
    if cid in CID_TO_COMPANY:
        return CID_TO_COMPANY[cid]
    
    # Try without .pdf extension
    cid_stem = Path(cid).stem
    if cid_stem in CID_TO_COMPANY:
        return CID_TO_COMPANY[cid_stem]
    
    # Fallback: auto-extract from filename
    print(f"⚠️  Warning: No mapping found for CID '{cid}', using auto-extraction")
    
    # Remove .pdf extension
    name = cid_stem
    
    # Remove common patterns: year, "ESG", "Report", "FINAL", etc.
    parts = name.split('-')
    
    # Filter out common non-company words
    excluded_words = {'2020', '2021', '2022', '2023', '2024', 
                     'ESG', 'Report', 'FINAL', 'Final', 'final',
                     'Sustainability', 'Annual', 'SR'}
    
    company_parts = [p for p in parts if p not in excluded_words and not p.isdigit()]
    
    # Return the first meaningful part (usually the company name)
    if company_parts:
        return company_parts[0]
    else:
        # Last resort: return the stem
        return cid_stem


def split_queries_by_company(input_file: Path, output_dir: Path):
    """
    Split query file by company
    
    Args:
        input_file: Path to input query JSON file (e.g., queries_energy.json)
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
        industry_dir = output_dir / industry
        industry_dir.mkdir(parents=True, exist_ok=True)
        
        for company, queries_list in companies.items():
            # Create company-specific query file
            company_data = {
                "queries": queries_list
            }
            
            # Save to file
            output_file = industry_dir / f"queries_{company.lower()}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(company_data, f, ensure_ascii=False, indent=2)
            
            print(f"   ✓ {industry}/{output_file.name} ({len(queries_list)} queries)")
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
    print(f"SPLITTING QUERY FILES BY COMPANY")
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
        description="Split query files by company (CID)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process default query directory
  python split_queries_by_company.py
  
  # Process specific query directory
  python split_queries_by_company.py --query-dir queries_regcom_mixed
  
  # Specify custom output directory
  python split_queries_by_company.py --output queries_by_company
  
  # Both custom input and output
  python split_queries_by_company.py --query-dir queries_regcom_mixed --output queries_by_company_mixed
        """
    )
    
    parser.add_argument(
        '--query-dir',
        default='queries_regcom',
        help='Query directory name (default: queries_regcom)'
    )
    
    parser.add_argument(
        '--output',
        default='queries_by_company',
        help='Output base directory name (default: queries_by_company)'
    )
    
    args = parser.parse_args()
    
    # Process all query files
    process_all_query_files(args.query_dir, args.output)


if __name__ == "__main__":
    main()