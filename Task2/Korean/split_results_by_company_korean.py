#!/usr/bin/env python3
"""
Split evaluation results by company (CID) - Korean version with industry and mode support

Directory structure:
  Input:  results_colqwen_eval_korean/
          ├── hardware/
          │   ├── mixed/results_hardware_mixed.json
          │   └── complete_yes/results_hardware_complete_yes.json
          └── ...
  
  Output: results_by_company_korean/
          ├── hardware/
          │   ├── mixed/
          │   │   ├── results_samsung_electronics.json
          │   │   └── results_bh.json
          │   └── complete_yes/
          │       └── ...
          └── ...
"""

import json
from pathlib import Path
from collections import defaultdict
import argparse
import numpy as np


def get_company_name(cid: str) -> str:
    return Path(cid).stem


def recalculate_metrics(results: list) -> dict:
    if not results:
        return {}
    
    metrics = defaultdict(list)
    for r in results:
        for key, value in r['metrics'].items():
            metrics[key].append(value)
    
    summary = {k: float(np.mean(v)) for k, v in metrics.items()}
    summary['num_queries'] = len(results)
    summary['avg_relevant_pages'] = float(np.mean([r['num_relevant_pages'] for r in results]))
    
    return summary


def split_results_by_company(input_file: Path, output_dir: Path, industry: str, mode: str):
    print(f"\n{'='*80}")
    print(f"Processing: {input_file.name} ({industry}, {mode})")
    print(f"{'='*80}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✓ Loaded {data['summary']['num_queries']} queries")
    print(f"  Industry: {data.get('industry', 'N/A')}")
    print(f"  Mode: {data.get('mode', 'N/A')}")
    
    # Group by company
    company_results = defaultdict(list)
    for result in data['results']:
        company = get_company_name(result['CID'])
        company_results[company].append(result)
    
    print(f"\n📊 Found {len(company_results)} companies:")
    for company, results in sorted(company_results.items()):
        print(f"   • {company}: {len(results)} queries")
    
    # Create output directory
    mode_output_dir = output_dir / industry / mode
    mode_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Saving company-specific results...")
    
    total_files = 0
    for company, results in company_results.items():
        company_summary = recalculate_metrics(results)
        
        company_data = {
            "company": company,
            "industry": data.get('industry', industry),
            "mode": data.get('mode', mode),
            "language": data.get('language', 'korean'),
            "model": data['model'],
            "evaluation_date": data['evaluation_date'],
            "summary": company_summary,
            "efficiency": data.get('efficiency', {}),
            "results": results
        }
        
        output_file = mode_output_dir / f"results_{company}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(company_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✓ {output_file.name} ({len(results)} queries)")
        total_files += 1
    
    print(f"\n✅ Split complete!")
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
    print(f"SPLITTING KOREAN EVALUATION RESULTS BY COMPANY")
    print(f"{'='*80}")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"{'='*80}")
    
    total_files_created = 0
    
    for industry_dir in sorted(industry_dirs):
        industry = industry_dir.name
        
        # Process both modes
        for mode in ['mixed', 'complete_yes']:
            mode_dir = industry_dir / mode
            if not mode_dir.exists():
                continue
            
            result_file = mode_dir / f"results_{industry}_{mode}.json"
            
            if not result_file.exists():
                print(f"⚠ Warning: Not found: {result_file}")
                continue
            
            try:
                files = split_results_by_company(result_file, output_dir, industry, mode)
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
        description="Split Korean evaluation results by company"
    )
    
    parser.add_argument('--input', default='results_colqwen_eval_korean')
    parser.add_argument('--output', default='results_by_company_korean')
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).resolve().parent
    process_all_industries(base_dir / args.input, base_dir / args.output)


if __name__ == "__main__":
    main()