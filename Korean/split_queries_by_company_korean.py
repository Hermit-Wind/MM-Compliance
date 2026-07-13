#!/usr/bin/env python3
"""
Split query files by company (CID) - Korean version with industry and mode support

Directory structure:
  Input:  queries_korean_by_industry/
          ├── hardware/
          │   ├── queries_korean_hardware_mixed.json
          │   └── queries_korean_hardware_complete_yes.json
          └── ...
  
  Output: queries_by_company_korean/
          ├── hardware/
          │   ├── mixed/
          │   │   ├── queries_samsung_electronics.json
          │   │   └── queries_bh.json
          │   └── complete_yes/
          │       ├── queries_samsung_electronics.json
          │       └── queries_bh.json
          └── ...
"""

import json
from pathlib import Path
from collections import defaultdict
import argparse


def get_company_name(cid: str) -> str:
    return Path(cid).stem


def split_queries_by_company(input_file: Path, output_dir: Path, industry: str, mode: str):
    print(f"\n{'='*80}")
    print(f"Processing: {input_file.name} ({industry}, {mode})")
    print(f"{'='*80}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    queries = data.get('queries', [])
    print(f"✓ Loaded {len(queries)} queries")
    
    # Group by company
    company_queries = defaultdict(list)
    for query in queries:
        company = get_company_name(query['CID'])
        company_queries[company].append(query)
    
    print(f"\n📊 Grouped by company:")
    for company, queries_list in sorted(company_queries.items()):
        print(f"   • {company}: {len(queries_list)} queries")
    
    # Create industry/mode output directory
    mode_output_dir = output_dir / industry / mode
    mode_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Saving company-specific files...")
    
    total_files = 0
    for company, queries_list in company_queries.items():
        output_file = mode_output_dir / f"queries_{company}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({"queries": queries_list}, f, ensure_ascii=False, indent=2)
        
        print(f"   ✓ {output_file.name} ({len(queries_list)} queries)")
        total_files += 1
    
    print(f"\n✅ Split complete!")
    print(f"   Total files: {total_files}")
    print(f"   Output: {mode_output_dir}")
    print(f"{'='*80}\n")
    
    return total_files


def process_all_industries(input_dir: Path, output_dir: Path):
    if not input_dir.exists():
        print(f"❌ Error: Input directory not found: {input_dir}")
        return
    
    industry_dirs = [d for d in input_dir.iterdir() if d.is_dir()]
    
    if not industry_dirs:
        print(f"❌ Error: No industry directories found")
        return
    
    print(f"\n{'='*80}")
    print(f"SPLITTING KOREAN QUERY FILES BY COMPANY")
    print(f"{'='*80}")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Found {len(industry_dirs)} industries")
    print(f"{'='*80}")
    
    total_files_created = 0
    
    for industry_dir in sorted(industry_dirs):
        industry = industry_dir.name
        
        # Process both modes
        for mode in ['mixed', 'complete_yes']:
            query_file = industry_dir / f"queries_korean_{industry}_{mode}.json"
            
            if not query_file.exists():
                print(f"⚠ Warning: Not found: {query_file}")
                continue
            
            try:
                files = split_queries_by_company(query_file, output_dir, industry, mode)
                total_files_created += files
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
    
    print(f"\n{'='*80}")
    print(f"✅ ALL DONE!")
    print(f"Total files created: {total_files_created}")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Split Korean query files by company with industry and mode organization"
    )
    
    parser.add_argument('--input', default='queries_korean_by_industry')
    parser.add_argument('--output', default='queries_by_company_korean')
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).resolve().parent
    process_all_industries(base_dir / args.input, base_dir / args.output)


if __name__ == "__main__":
    main()