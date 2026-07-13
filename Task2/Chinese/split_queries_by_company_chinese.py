#!/usr/bin/env python3
"""
Split query files by company (CID) - Chinese version with industry support

This script reads Chinese query JSON files (organized by industry) and splits them 
into separate files per company while maintaining the original structure.

For Chinese data: CID = PDF filename (e.g., "Alchip.pdf")
Industry structure: queries_chinese_by_industry/ -> queries_by_company_chinese/[industry]/
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import argparse


def get_company_name(cid: str) -> str:
    """
    Get company name from CID
    For Chinese data, CID is already the company name (PDF stem)
    
    Args:
        cid: PDF filename like "Alchip.pdf"
    
    Returns:
        Company name like "Alchip"
    """
    return Path(cid).stem


def split_queries_by_company(input_file: Path, output_dir: Path, industry: str):
    """
    Split query file by company
    
    Args:
        input_file: Path to input query JSON file
        output_dir: Base directory to save split queries
        industry: Industry name (e.g., "semiconductor", "finance")
    """
    print(f"\n{'='*80}")
    print(f"Processing: {input_file.name} ({industry})")
    print(f"{'='*80}")
    
    # Load original queries
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    queries = data.get('queries', [])
    print(f"✓ Loaded {len(queries)} queries")
    
    # Group queries by company
    company_queries = defaultdict(list)
    
    for query in queries:
        cid = query['CID']
        company = get_company_name(cid)
        company_queries[company].append(query)
    
    # Print summary
    print(f"\n📊 Grouped by company:")
    for company, queries_list in sorted(company_queries.items()):
        print(f"   • {company}: {len(queries_list)} queries")
    
    # Create industry-specific output directory
    industry_output_dir = output_dir / industry
    industry_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save queries for each company
    print(f"\n💾 Saving company-specific query files...")
    
    total_files = 0
    for company, queries_list in company_queries.items():
        # Create company-specific query file
        company_data = {
            "queries": queries_list
        }
        
        # Save to file
        company_slug = company.lower().replace(' ', '_')
        output_file = industry_output_dir / f"queries_{company_slug}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(company_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✓ {output_file.name} ({len(queries_list)} queries)")
        total_files += 1
    
    print(f"\n✅ Split complete for {industry}!")
    print(f"   Total files created: {total_files}")
    print(f"   Output directory: {industry_output_dir}")
    print(f"{'='*80}\n")
    
    return total_files


def process_all_industries(input_dir: Path, output_dir: Path):
    """
    Process all industry query files
    
    Args:
        input_dir: Directory containing industry query files
        output_dir: Base output directory
    """
    if not input_dir.exists():
        print(f"❌ Error: Input directory not found: {input_dir}")
        return
    
    # Find all industry query files
    query_files = sorted(input_dir.glob("queries_chinese_*.json"))
    
    if not query_files:
        print(f"❌ Error: No query files found in {input_dir}")
        print(f"   Expected pattern: queries_chinese_*.json")
        return
    
    print(f"\n{'='*80}")
    print(f"SPLITTING CHINESE QUERY FILES BY COMPANY")
    print(f"{'='*80}")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Found {len(query_files)} industry files")
    print(f"{'='*80}")
    
    total_files_created = 0
    industries_processed = []
    
    for query_file in query_files:
        # Extract industry name from filename
        # e.g., "queries_chinese_semiconductor.json" -> "semiconductor"
        filename = query_file.stem
        if filename.startswith("queries_chinese_"):
            industry = filename.replace("queries_chinese_", "")
        else:
            print(f"⚠ Warning: Skipping file with unexpected name: {query_file.name}")
            continue
        
        files_created = split_queries_by_company(query_file, output_dir, industry)
        total_files_created += files_created
        industries_processed.append(industry)
    
    # Print final summary
    print(f"\n{'='*80}")
    print(f"✅ ALL INDUSTRIES PROCESSED!")
    print(f"{'='*80}")
    print(f"Industries processed: {len(industries_processed)}")
    for industry in sorted(industries_processed):
        industry_dir = output_dir / industry
        num_companies = len(list(industry_dir.glob("queries_*.json")))
        print(f"   • {industry}: {num_companies} companies")
    print(f"\nTotal company files created: {total_files_created}")
    print(f"Output structure: {output_dir}/[industry]/queries_[company].json")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Split Chinese query files by company (CID) with industry organization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all industry files from default directory
  python split_queries_by_company_chinese.py
  
  # Specify custom input directory
  python split_queries_by_company_chinese.py --input queries_chinese_by_industry
  
  # Specify custom output directory
  python split_queries_by_company_chinese.py --output queries_by_company_chinese
  
  # Both custom directories
  python split_queries_by_company_chinese.py --input my_queries --output my_output

Directory structure:
  Input:  queries_chinese_by_industry/
          ├── queries_chinese_semiconductor.json
          ├── queries_chinese_finance.json
          └── queries_chinese_energy.json
  
  Output: queries_by_company_chinese/
          ├── semiconductor/
          │   ├── queries_alchip.json
          │   ├── queries_tsmc.json
          │   └── queries_psi.json
          ├── finance/
          │   ├── queries_e.sun.json
          │   └── queries_tcfh.json
          └── energy/
              ├── queries_fpcc.json
              └── queries_npc.json
        """
    )
    
    parser.add_argument(
        '--input',
        default='queries_chinese_by_industry',
        help='Input directory containing industry query files (default: queries_chinese_by_industry)'
    )
    
    parser.add_argument(
        '--output',
        default='queries_by_company_chinese',
        help='Output base directory (default: queries_by_company_chinese)'
    )
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / args.input
    output_dir = base_dir / args.output
    
    process_all_industries(input_dir, output_dir)


if __name__ == "__main__":
    main()