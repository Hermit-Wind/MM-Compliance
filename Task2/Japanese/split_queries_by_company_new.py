#!/usr/bin/env python3
"""
Split query files by company (CID) - Japanese version with industry support (NEW FORMAT)

This script reads Japanese query JSON files (organized by industry) and splits them 
into separate files per company while maintaining the original structure.

Uses NEW query dataset built from new_mixed.json with PDF_Page field.

Directory structure:
  Input:  queries_japanese_new_by_industry/
          ├── automotive/queries_automotive.json
          ├── energy/queries_energy.json
          └── trading_companies/queries_trading_companies.json
  
  Output: queries_by_company_japanese_new/
          ├── automotive/
          │   ├── queries_honda_motor.json
          │   ├── queries_nissan_motor.json
          │   └── queries_mazda_motor.json
          ├── energy/
          │   ├── queries_tokyo_gas.json
          │   └── queries_toho_gas.json
          └── trading_companies/
              ├── queries_itochu_corp.json
              └── queries_marubeni_corp.json
"""

import json
from pathlib import Path
from collections import defaultdict
import argparse


def get_company_name(cid: str) -> str:
    """
    Get company name from CID
    For Japanese data, CID is already the company name
    
    Args:
        cid: Company name like "Honda Motor"
    
    Returns:
        Company name (same as input)
    """
    return cid


def split_queries_by_company(input_file: Path, output_dir: Path, industry: str):
    """
    Split query file by company for a specific industry
    
    Args:
        input_file: Path to input query JSON file
        output_dir: Base output directory
        industry: Industry name (e.g., "automotive", "energy")
    """
    print(f"\n{'='*80}")
    print(f"Processing: {input_file.name} ({industry}) [NEW FORMAT]")
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
        
        # Convert company name to filename-safe format
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
        input_dir: Directory containing industry subdirectories
        output_dir: Base output directory
    """
    if not input_dir.exists():
        print(f"❌ Error: Input directory not found: {input_dir}")
        return
    
    # Find all industry subdirectories with query files
    industry_dirs = [d for d in input_dir.iterdir() if d.is_dir()]
    
    if not industry_dirs:
        print(f"❌ Error: No industry directories found in {input_dir}")
        return
    
    print(f"\n{'='*80}")
    print(f"SPLITTING JAPANESE QUERY FILES BY COMPANY (NEW FORMAT)")
    print(f"{'='*80}")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Found {len(industry_dirs)} industry directories")
    print(f"\n[INFO] Using NEW query dataset with PDF_Page field")
    print(f"{'='*80}")
    
    total_files_created = 0
    industries_processed = []
    
    for industry_dir in sorted(industry_dirs):
        industry = industry_dir.name
        
        # Look for query file in industry directory
        query_file = industry_dir / f"queries_{industry}.json"
        
        if not query_file.exists():
            print(f"⚠ Warning: Query file not found for {industry}: {query_file}")
            continue
        
        try:
            files_created = split_queries_by_company(query_file, output_dir, industry)
            total_files_created += files_created
            industries_processed.append(industry)
        except Exception as e:
            print(f"❌ Error processing {industry}: {e}")
            continue
    
    # Print final summary
    print(f"\n{'='*80}")
    print(f"✅ ALL INDUSTRIES PROCESSED! (NEW FORMAT)")
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
        description="Split Japanese query files by company (CID) with industry organization (NEW FORMAT)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all industries from default directory (NEW FORMAT)
  python split_queries_by_company_japanese_new.py
  
  # Specify custom input directory
  python split_queries_by_company_japanese_new.py --input queries_japanese_new_by_industry
  
  # Specify custom output directory
  python split_queries_by_company_japanese_new.py --output queries_by_company_japanese_new
  
  # Both custom directories
  python split_queries_by_company_japanese_new.py --input my_queries --output my_output
        """
    )
    
    parser.add_argument(
        '--input',
        default='queries_japanese_new_by_industry',  # NEW: use new query directory
        help='Input directory containing industry subdirectories (default: queries_japanese_new_by_industry)'
    )
    
    parser.add_argument(
        '--output',
        default='queries_by_company_japanese_new',  # NEW: output to new directory
        help='Output base directory (default: queries_by_company_japanese_new)'
    )
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / args.input
    output_dir = base_dir / args.output
    
    process_all_industries(input_dir, output_dir)


if __name__ == "__main__":
    main()