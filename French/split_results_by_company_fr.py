#split_results_by_company_fr.py
#!/usr/bin/env python3
"""
Split French evaluation results by company (CID)

This script reads French evaluation result JSON files and splits them into separate files
per company while maintaining the original structure and summary statistics.
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import argparse


# =====================================================
# CID to Company Name Mapping for French Dataset
# =====================================================
CID_TO_COMPANY = {
    # Exact matches (with or without .pdf extension)
    "20230630_RAPPORTESG2022_COVEAFINANCE_VF.pdf": "COVEA_FINANCE",
    "20230630_RAPPORTESG2022_COVEAFINANCE_VF": "COVEA_FINANCE",
    
    "extrait-rse-filieres-dapprovisionnement.pdf": "Hermes",
    "extrait-rse-filieres-dapprovisionnement": "Hermes",
    
    "GUERLAIN_RAPPORT_DEVELOPPEMENT_DURABLE_2022-2023.pdf": "GUERLAIN",
    "GUERLAIN_RAPPORT_DEVELOPPEMENT_DURABLE_2022-2023": "GUERLAIN",
    
    "INE_ESG-REPORT_FR_FINAL.pdf": "INE",
    "INE_ESG-REPORT_FR_FINAL": "INE",
    
    "malakoff-humanis-rapport-ESG-climat-article-29-loi-energie-climat-exercice-2022-mh-22365-2306-192.pdf": "MALAKOFF_HUMANIS",
    "malakoff-humanis-rapport-ESG-climat-article-29-loi-energie-climat-exercice-2022-mh-22365-2306-192": "MALAKOFF_HUMANIS",
    
    "Rapport-ESG-GAM.pdf": "GAM",
    "Rapport-ESG-GAM": "GAM",
    
    "REMY_COINTREAU_RAPPORT_RSE_2023.pdf": "REMY_COINTREAU",
    "REMY_COINTREAU_RAPPORT_RSE_2023": "REMY_COINTREAU",
    
    "RSE2022_web_0.pdf": "EDF",
    "RSE2022_web_0": "EDF",
    
    "totalenergies_sustainability-climate-2024-progress-report_2024_fr_pdf.pdf": "TOTALENERGIES",
    "totalenergies_sustainability-climate-2024-progress-report_2024_fr_pdf": "TOTALENERGIES",
}


def get_company_name(cid: str) -> str:
    """
    Extract company name from CID (PDF filename) using mapping table
    
    Args:
        cid: PDF filename like "20230630_RAPPORTESG2022_COVEAFINANCE_VF.pdf"
    
    Returns:
        Company name like "COVEA_FINANCE"
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
                     'Sustainability', 'Annual', 'SR', 'RSE', 'RAPPORT'}
    
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
    print(f"SPLITTING FRENCH EVALUATION RESULTS BY COMPANY")
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
        description="Split French evaluation results by company (CID)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all default result directories
  python split_results_by_company_fr.py
  
  # Process specific directories
  python split_results_by_company_fr.py --dirs results_colqwen_eval results_colqwen_eval_mixed
  
  # Specify custom output directory
  python split_results_by_company_fr.py --output results_by_company
        """
    )
    
    parser.add_argument(
        '--dirs',
        nargs='+',
        default=[
            'results_colqwen_eval',
            'results_colqwen_eval_mixed'
        ],
        help='List of result directories to process (default: both eval and eval_mixed)'
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