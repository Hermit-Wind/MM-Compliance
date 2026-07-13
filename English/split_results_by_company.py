#!/usr/bin/env python3
"""
Split evaluation results by company (CID)

This script reads evaluation result JSON files and splits them into separate files
per company while maintaining the original structure and summary statistics.
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import argparse


# =====================================================
# CID to Company Name Mapping
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


def split_results_by_company(input_file: Path, output_dir: Path, source_dir_name: str):
    """
    Split evaluation results by company
    
    Args:
        input_file: Path to input JSON file
        output_dir: Directory to save split results
        source_dir_name: Name of the source directory (for organizing output)
    """
    print(f"\n{'='*80}")
    print(f"Processing: {input_file.name}")
    print(f"Source: {source_dir_name}")
    print(f"{'='*80}")
    
    # Load original results
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✓ Loaded {data['summary']['num_queries']} queries")
    print(f"  Model: {data['model']}")
    print(f"  Industry: {data['industry']}")
    
    # Group results by company
    company_results = defaultdict(list)
    
    for result in data['results']:
        cid = result['CID']
        company = get_company_name(cid)
        company_results[company].append(result)
    
    print(f"\n📊 Found {len(company_results)} companies:")
    for company, results in sorted(company_results.items()):
        print(f"   • {company}: {len(results)} queries")
    
    # Create output directory: output_dir / source_dir_name / industry
    industry = data['industry']
    industry_dir = output_dir / source_dir_name / industry
    industry_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results for each company
    print(f"\n💾 Saving company-specific results...")
    
    for company, results in company_results.items():
        # Recalculate summary for this company
        company_summary = recalculate_metrics(results)
        
        # Create company-specific data structure
        company_data = {
            "company": company,
            "industry": data['industry'],
            "model": data['model'],
            "evaluation_date": data['evaluation_date'],
            "summary": company_summary,
            "efficiency": data['efficiency'],  # Keep original efficiency stats
            "results": results
        }
        
        # Save to file
        output_file = industry_dir / f"results_{company.lower()}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(company_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✓ {output_file.name}")
    
    print(f"\n✅ Company split complete for {industry}!")
    print(f"   Output directory: {industry_dir}")
    print(f"{'='*80}\n")


def process_all_results(results_dirs: List[str], output_base: str):
    """
    Process all result directories
    
    Args:
        results_dirs: List of result directory names to process
        output_base: Base output directory name
    """
    base_dir = Path(__file__).resolve().parent
    output_dir = base_dir / output_base
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*80}")
    print(f"SPLITTING EVALUATION RESULTS BY COMPANY")
    print(f"{'='*80}")
    print(f"Output directory: {output_dir}")
    
    # Process each result directory
    total_files = 0
    dir_summary = defaultdict(int)
    
    for dir_name in results_dirs:
        results_dir = base_dir / dir_name
        
        if not results_dir.exists():
            print(f"\n⚠️  Warning: Directory not found: {results_dir}")
            continue
        
        # Find all JSON result files
        json_files = list(results_dir.glob("results_*.json"))
        
        if not json_files:
            print(f"\n⚠️  Warning: No result files found in {results_dir}")
            continue
        
        for json_file in sorted(json_files):
            split_results_by_company(json_file, output_dir, dir_name)
            total_files += 1
            dir_summary[dir_name] += 1
    
    print(f"\n{'='*80}")
    print(f"✅ ALL DONE!")
    print(f"   Processed {total_files} files total")
    print(f"\n   Files per directory:")
    for dir_name, count in sorted(dir_summary.items()):
        print(f"   • {dir_name}: {count} files")
    print(f"\n   Results saved to: {output_dir}")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Split evaluation results by company (CID)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all default result directories
  python split_results_by_company.py
  
  # Process specific directories
  python split_results_by_company.py --dirs results_colqwen_eval results_retrieval_eval_mixed
  
  # Specify custom output directory
  python split_results_by_company.py --output results_by_company
        """
    )
    
    parser.add_argument(
        '--dirs',
        nargs='+',
        default=[
            'results_colqwen_eval',
            'results_colqwen_eval_mixed', 
            'results_retrieval_eval',
            'results_retrieval_eval_mixed'
        ],
        help='List of result directories to process (default: all four)'
    )
    
    parser.add_argument(
        '--output',
        default='results_by_company',
        help='Output base directory name (default: results_by_company)'
    )
    
    args = parser.parse_args()
    
    # Process all results
    process_all_results(args.dirs, args.output)


if __name__ == "__main__":
    main()
