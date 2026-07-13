#!/usr/bin/env python3
"""
Split evaluation results by company (CID) - Chinese version with industry support

This script reads Chinese evaluation result JSON files (organized by industry) 
and splits them into separate files per company while maintaining the original 
structure and recalculating summary statistics.

Directory structure:
  Input:  results_colqwen_eval_chinese/
          ├── semiconductor/results_semiconductor.json
          ├── finance/results_finance.json
          └── energy/results_energy.json
  
  Output: results_by_company_chinese/
          ├── semiconductor/
          │   ├── results_alchip.json
          │   ├── results_tsmc.json
          │   └── results_psi.json
          ├── finance/
          │   ├── results_e.sun.json
          │   └── results_tcfh.json
          └── energy/
              ├── results_fpcc.json
              └── results_npc.json
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import argparse
import numpy as np


def get_company_name(cid: str) -> str:
    """
    Extract company name from CID (PDF filename)
    For Chinese data, CID is already the company name
    
    Args:
        cid: PDF filename like "Alchip.pdf"
    
    Returns:
        Company name like "Alchip"
    """
    return Path(cid).stem


def recalculate_metrics(results: List[Dict]) -> Dict:
    """
    Recalculate summary metrics for a subset of results
    
    Args:
        results: List of query results
    
    Returns:
        Dictionary of summary metrics
    """
    if not results:
        return {}
    
    # Collect all metrics
    metrics = defaultdict(list)
    
    for r in results:
        for key, value in r['metrics'].items():
            metrics[key].append(value)
    
    # Calculate averages
    summary = {k: float(np.mean(v)) for k, v in metrics.items()}
    
    # Add metadata
    summary['num_queries'] = len(results)
    summary['avg_relevant_pages'] = float(np.mean([r['num_relevant_pages'] for r in results]))
    
    return summary


def split_results_by_company(input_file: Path, output_dir: Path, industry: str):
    """
    Split evaluation results by company for a specific industry
    
    Args:
        input_file: Path to input JSON file
        output_dir: Base output directory
        industry: Industry name (e.g., "semiconductor", "finance")
    """
    print(f"\n{'='*80}")
    print(f"Processing: {input_file.name} ({industry})")
    print(f"{'='*80}")
    
    # Load original results
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✓ Loaded {data['summary']['num_queries']} queries")
    print(f"  Industry: {data.get('industry', 'N/A')}")
    print(f"  Model: {data['model']}")
    print(f"  Language: {data['language']}")
    
    # Group results by company
    company_results = defaultdict(list)
    
    for result in data['results']:
        cid = result['CID']
        company = get_company_name(cid)
        company_results[company].append(result)
    
    print(f"\n📊 Found {len(company_results)} companies:")
    for company, results in sorted(company_results.items()):
        print(f"   • {company}: {len(results)} queries")
    
    # Create industry-specific output directory
    industry_output_dir = output_dir / industry
    industry_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results for each company
    print(f"\n💾 Saving company-specific results...")
    
    total_files = 0
    for company, results in company_results.items():
        # Recalculate summary for this company
        company_summary = recalculate_metrics(results)
        
        # Create company-specific data structure
        company_data = {
            "company": company,
            "industry": data.get('industry', industry),
            "language": data['language'],
            "model": data['model'],
            "evaluation_date": data['evaluation_date'],
            "summary": company_summary,
            "efficiency": data.get('efficiency', {}),
            "results": results
        }
        
        # Save to file
        company_slug = company.lower().replace('.', '').replace(' ', '_')
        output_file = industry_output_dir / f"results_{company_slug}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(company_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✓ {output_file.name} ({len(results)} queries)")
        total_files += 1
    
    print(f"\n✅ Company split complete for {industry}!")
    print(f"   Total files created: {total_files}")
    print(f"   Output directory: {industry_output_dir}")
    print(f"{'='*80}\n")
    
    return total_files


def process_all_industries(input_dir: Path, output_dir: Path):
    """
    Process all industry result files
    
    Args:
        input_dir: Base directory containing industry subdirectories
        output_dir: Base output directory
    """
    if not input_dir.exists():
        print(f"❌ Error: Input directory not found: {input_dir}")
        return
    
    # Find all industry subdirectories with result files
    industry_dirs = [d for d in input_dir.iterdir() if d.is_dir()]
    
    if not industry_dirs:
        print(f"❌ Error: No industry directories found in {input_dir}")
        return
    
    print(f"\n{'='*80}")
    print(f"SPLITTING CHINESE EVALUATION RESULTS BY COMPANY")
    print(f"{'='*80}")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Found {len(industry_dirs)} industry directories")
    print(f"{'='*80}")
    
    total_files_created = 0
    industries_processed = []
    
    for industry_dir in sorted(industry_dirs):
        industry = industry_dir.name
        
        # Look for result file in industry directory
        result_file = industry_dir / f"results_{industry}.json"
        
        if not result_file.exists():
            print(f"⚠ Warning: Result file not found for {industry}: {result_file}")
            continue
        
        try:
            files_created = split_results_by_company(result_file, output_dir, industry)
            total_files_created += files_created
            industries_processed.append(industry)
        except Exception as e:
            print(f"❌ Error processing {industry}: {e}")
            continue
    
    # Print final summary
    print(f"\n{'='*80}")
    print(f"✅ ALL INDUSTRIES PROCESSED!")
    print(f"{'='*80}")
    print(f"Industries processed: {len(industries_processed)}")
    for industry in sorted(industries_processed):
        industry_dir = output_dir / industry
        num_companies = len(list(industry_dir.glob("results_*.json")))
        print(f"   • {industry}: {num_companies} companies")
    print(f"\nTotal company files created: {total_files_created}")
    print(f"Output structure: {output_dir}/[industry]/results_[company].json")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Split Chinese evaluation results by company (CID) with industry organization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all industries from default directory
  python split_results_by_company_chinese.py
  
  # Specify custom input directory
  python split_results_by_company_chinese.py --input results_colqwen_eval_chinese
  
  # Specify custom output directory
  python split_results_by_company_chinese.py --output results_by_company_chinese
  
  # Both custom directories
  python split_results_by_company_chinese.py --input my_results --output my_output

Directory structure:
  Input:  results_colqwen_eval_chinese/
          ├── semiconductor/results_semiconductor.json
          ├── finance/results_finance.json
          └── energy/results_energy.json
  
  Output: results_by_company_chinese/
          ├── semiconductor/
          │   ├── results_alchip.json
          │   └── results_tsmc.json
          ├── finance/
          │   ├── results_e.sun.json
          │   └── results_tcfh.json
          └── energy/
              ├── results_fpcc.json
              └── results_npc.json
        """
    )
    
    parser.add_argument(
        '--input',
        type=str,
        default='results_colqwen_eval_chinese',
        help='Input base directory containing industry subdirectories (default: results_colqwen_eval_chinese)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='results_by_company_chinese',
        help='Output base directory (default: results_by_company_chinese)'
    )
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / args.input
    output_dir = base_dir / args.output
    
    process_all_industries(input_dir, output_dir)
    
    print(f"\n{'='*80}")
    print(f"✅ ALL DONE!")
    print(f"   Results saved to: {output_dir}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()