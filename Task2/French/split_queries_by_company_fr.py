#!/usr/bin/env python3
"""
Split French query files by company (CID)

This script reads French query JSON files and splits them into separate files
per company while maintaining the original structure.
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
    """
    Process both queries_regcom and queries_regcom_mixed directories
    """
    base_dir = Path(__file__).resolve().parent
    
    # Configuration for both directories
    configs = [
        {
            'query_dir': 'queries_regcom',
            'output_dir': 'queries_by_company'
        },
        {
            'query_dir': 'queries_regcom_mixed',
            'output_dir': 'queries_by_company_mixed'
        }
    ]
    
    print(f"\n{'#'*80}")
    print(f"# FRENCH DATASET: SPLIT QUERIES BY COMPANY")
    print(f"# Processing 2 directories: queries_regcom and queries_regcom_mixed")
    print(f"{'#'*80}\n")
    
    # Process each configuration
    for i, config in enumerate(configs, 1):
        print(f"\n{'*'*80}")
        print(f"* STEP {i}/2: Processing {config['query_dir']}")
        print(f"{'*'*80}")
        
        process_all_query_files(config['query_dir'], config['output_dir'])
    
    print(f"\n{'#'*80}")
    print(f"# ✅ ALL PROCESSING COMPLETE!")
    print(f"# Both directories have been split by company")
    print(f"{'#'*80}\n")


if __name__ == "__main__":
    main()
