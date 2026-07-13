#!/usr/bin/env python3
"""
Split evaluation results by company (CID) - Thai version

This script reads Thai evaluation result JSON files and splits them into 
separate files per company while maintaining the original structure and summary statistics.

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


def recalculate_metrics(results: List[Dict]) -> Dict:
    """
    Recalculate summary metrics for a subset of results
    
    Args:
        results: List of query results
    
    Returns:
        Dictionary of summary metrics
    """
    import numpy as np
    
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


def split_results_by_company(input_file: Path, output_dir: Path):
    """
    Split evaluation results by company
    
    Args:
        input_file: Path to input JSON file
        output_dir: Directory to save split results
    """
    print(f"\n{'='*80}")
    print(f"Processing: {input_file.name}")
    print(f"{'='*80}")
    
    # Load original results
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✓ Loaded {data['summary']['num_queries']} queries")
    print(f"  Model: {data['model']}")
    print(f"  Industry: {data.get('industry', 'N/A')}")
    print(f"  Language: {data.get('language', 'thai')}")
    
    # Group results by company
    company_results = defaultdict(list)
    
    for result in data['results']:
        cid = result['CID']
        company = get_company_name(cid)
        company_results[company].append(result)
    
    print(f"\n📊 Found {len(company_results)} companies:")
    for company, results in sorted(company_results.items()):
        print(f"   • {company}: {len(results)} queries")
    
    # Create output directory for this industry
    industry = data.get('industry', 'unknown')
    industry_dir = output_dir / industry
    industry_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results for each company
    print(f"\n💾 Saving company-specific results...")
    
    for company, results in company_results.items():
        # Recalculate summary for this company
        company_summary = recalculate_metrics(results)
        
        # Create company-specific data structure
        company_data = {
            "company": company,
            "industry": data.get('industry', ''),
            "language": data.get('language', 'thai'),
            "model": data['model'],
            "evaluation_date": data['evaluation_date'],
            "summary": company_summary,
            "efficiency": data['efficiency'],
            "results": results
        }
        
        # Save to file
        company_slug = company.lower().replace(' ', '_')
        output_file = industry_dir / f"results_{company_slug}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(company_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✓ {output_file.name}")
    
    print(f"\n✅ Company split complete for {industry}!")
    print(f"   Output directory: {industry_dir}")
    print(f"{'='*80}\n")


def process_all_results(results_dir: str, output_base: str):
    """
    Process all result files in the directory
    
    Args:
        results_dir: Directory containing result files
        output_base: Base output directory name
    """
    base_dir = Path(__file__).resolve().parent
    results_path = base_dir / results_dir
    output_dir = base_dir / output_base
    
    if not results_path.exists():
        print(f"\n❌ Error: Results directory not found: {results_path}")
        return
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*80}")
    print(f"SPLITTING THAI EVALUATION RESULTS BY COMPANY")
    print(f"{'='*80}")
    print(f"Input directory: {results_path}")
    print(f"Output directory: {output_dir}")
    
    # Find all JSON result files
    json_files = list(results_path.glob("results_*.json"))
    
    if not json_files:
        print(f"\n❌ Error: No result files found in {results_path}")
        print(f"   Looking for files matching pattern: results_*.json")
        return
    
    print(f"\nFound {len(json_files)} result files:")
    for jf in sorted(json_files):
        print(f"   • {jf.name}")
    
    # Process each result file
    total_files = 0
    for json_file in sorted(json_files):
        split_results_by_company(json_file, output_dir)
        total_files += 1
    
    print(f"\n{'='*80}")
    print(f"✅ ALL DONE!")
    print(f"   Processed {total_files} files total")
    print(f"   Results saved to: {output_dir}")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Split Thai evaluation results by company (CID)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process default result directory
  python split_results_by_company_thai.py
  
  # Process specific directory
  python split_results_by_company_thai.py --input results_colqwen_eval_thai
  
  # Specify custom output directory
  python split_results_by_company_thai.py --output results_by_company_thai
        """
    )
    
    parser.add_argument(
        '--input',
        default='results_colqwen_eval_thai',
        help='Input result directory (default: results_colqwen_eval_thai)'
    )
    
    parser.add_argument(
        '--output',
        default='results_by_company_thai',
        help='Output base directory name (default: results_by_company_thai)'
    )
    
    args = parser.parse_args()
    
    # Process all results
    process_all_results(args.input, args.output)


if __name__ == "__main__":
    main()