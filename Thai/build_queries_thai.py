#!/usr/bin/env python3
"""
Build query files for Thai RegCom dataset

Uses Excel annotations to get page numbers and metrics.

Key features:
- Uses file_page_number (physical PDF page number)
- Includes all data (complete=TRUE/FALSE/N/A - mixed dataset)
- Code field already exists in Excel (no need to generate)
- Includes topic field
- Outputs combined file first, then splits by industry

Company to Industry mapping:
- Banking: CIMBT, KBANK, SCB, TISCO
- Commerce: CPALL, CRC, ICC, SCM
- Energy: BAFS, CV, PTTEP
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict
import json


# Company to Industry mapping (based on directory structure)
COMPANY_TO_INDUSTRY = {
    # Banking
    'CIMBT': 'Banking',
    'KBANK': 'Banking',
    'SCB': 'Banking',
    'TISCO': 'Banking',
    # Commerce
    'CPALL': 'Commerce',
    'CRC': 'Commerce',
    'ICC': 'Commerce',
    'SCM': 'Commerce',
    # Energy
    'BAFS': 'Energy',
    'CV': 'Energy',
    'PTTEP': 'Energy',
}


def normalize_space(s: str) -> str:
    """Normalize spaces and handle None safely"""
    if s is None or pd.isna(s):
        return ""
    return " ".join(str(s).split())


def page_to_image(cid: str, page: int) -> str:
    """
    Convert page number to standardized image name
    e.g., "CPALL", page 29 -> "CPALL_p029.png"
    """
    return f"{cid}_p{page:03d}.png"


def load_thai_annotations(excel_file: Path):
    """
    Load Thai Excel annotations
    
    Args:
        excel_file: Path to FinalRound.xlsx
    
    Returns:
        dict: {cid: {metric: {'pages': [pages], 'topic': topic, 'code': code, 'industry': industry}}}
    """
    if not excel_file.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_file}")
    
    print(f"Loading annotations from: {excel_file}")
    
    # Load all sheets (one per company)
    excel_data = pd.ExcelFile(excel_file)
    
    print(f"✓ Found {len(excel_data.sheet_names)} sheets")
    print(f"  Sheets: {excel_data.sheet_names}")
    
    # Structure: {cid: {metric: {'pages': set(), 'topic': str, 'code': str, 'industry': str}}}
    data = defaultdict(lambda: defaultdict(
        lambda: {'pages': set(), 'topic': '', 'code': '', 'industry': ''}
    ))
    
    skipped_no_page = 0
    skipped_no_industry = 0
    total_rows = 0
    
    # Process each sheet (each sheet is a company)
    for sheet_name in excel_data.sheet_names:
        # Sheet name is the company symbol
        cid = sheet_name.strip()
        
        # Get industry for this company
        industry = COMPANY_TO_INDUSTRY.get(cid)
        
        if not industry:
            print(f"\n⚠️  Skipping sheet '{sheet_name}': No industry mapping found")
            continue
        
        print(f"\n📄 Processing sheet: {sheet_name} (Industry: {industry})")
        
        # Read sheet
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        print(f"   Rows: {len(df)}")
        total_rows += len(df)
        
        sheet_skipped_pages = 0
        
        for idx, row in df.iterrows():
            try:
                metric = normalize_space(row.get('metric', ''))
                topic = normalize_space(row.get('topic', ''))
                code = normalize_space(row.get('code', ''))
                file_page = row.get('file_page_number', '')
                
                # Skip if essential fields are missing
                if not metric or not code:
                    continue
                
                # Skip if file_page_number is missing or '-'
                if not file_page or file_page == '-' or pd.isna(file_page):
                    skipped_no_page += 1
                    sheet_skipped_pages += 1
                    continue
                
                # Convert page to int
                try:
                    page_num = int(file_page)
                except (ValueError, TypeError):
                    skipped_no_page += 1
                    sheet_skipped_pages += 1
                    continue
                
                # Add to data structure
                data[cid][metric]['pages'].add(page_num)
                data[cid][metric]['topic'] = topic
                data[cid][metric]['code'] = code
                data[cid][metric]['industry'] = industry
            
            except Exception as e:
                print(f"   ⚠️  Error processing row {idx}: {e}")
                continue
        
        print(f"   ✓ Loaded {len(data[cid])} unique metrics")
        if sheet_skipped_pages > 0:
            print(f"   ⚠️  Skipped {sheet_skipped_pages} rows without valid file_page_number")
    
    print(f"\n{'='*80}")
    print(f"Loading summary:")
    print(f"   Total rows processed: {total_rows}")
    print(f"   Total companies: {len(data)}")
    print(f"   Skipped rows (no page): {skipped_no_page}")
    print(f"{'='*80}")
    
    # Convert sets to sorted lists
    for cid in data:
        for metric in data[cid]:
            data[cid][metric]['pages'] = sorted(data[cid][metric]['pages'])
    
    return data


def build_thai_queries(excel_file: Path, output_dir_combined: Path, output_dir_by_industry: Path):
    """
    Build queries for Thai dataset
    
    Args:
        excel_file: Path to FinalRound.xlsx
        output_dir_combined: Output directory for combined query file
        output_dir_by_industry: Output directory for industry-split files
    """
    print(f"\n{'='*80}")
    print(f"BUILDING THAI QUERIES")
    print(f"{'='*80}")
    print(f"Input file: {excel_file}")
    print(f"Combined output: {output_dir_combined}")
    print(f"Split output: {output_dir_by_industry}")
    print(f"{'='*80}\n")
    
    # Load annotations
    data = load_thai_annotations(excel_file)
    
    # Create output directories
    output_dir_combined.mkdir(parents=True, exist_ok=True)
    output_dir_by_industry.mkdir(parents=True, exist_ok=True)
    
    # Build all queries
    print(f"\n{'='*80}")
    print(f"Building queries")
    print(f"{'='*80}\n")
    
    all_queries = []
    queries_by_industry = defaultdict(list)
    
    for cid in sorted(data.keys()):
        industry = None
        query_count = 0
        
        for metric, metric_data in sorted(data[cid].items()):
            pages = metric_data['pages']
            topic = metric_data['topic']
            code = metric_data['code']
            industry = metric_data['industry']
            
            # Build relevant_docs
            relevant_docs = [page_to_image(cid, page) for page in pages]
            
            # Create query object
            query_obj = {
                "CID": cid,
                "industry": industry,
                "code": code,
                "topic": topic,
                "metric": metric,
                "query_text": metric,
                "relevant_docs": relevant_docs
            }
            
            all_queries.append(query_obj)
            queries_by_industry[industry].append(query_obj)
            query_count += 1
        
        print(f"   {cid} ({industry}): {query_count} queries")
    
    # ====================================================================
    # Step 1: Save combined file
    # ====================================================================
    print(f"\n{'='*80}")
    print(f"STEP 1: Saving combined query file")
    print(f"{'='*80}\n")
    
    combined_file = output_dir_combined / "queries_thai_all.json"
    
    output_data = {"queries": all_queries}
    
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Saved: {combined_file}")
    print(f"  Total queries: {len(all_queries)}")
    
    # ====================================================================
    # Step 2: Split by industry
    # ====================================================================
    print(f"\n{'='*80}")
    print(f"STEP 2: Splitting queries by industry")
    print(f"{'='*80}\n")
    
    for industry in sorted(queries_by_industry.keys()):
        industry_queries = queries_by_industry[industry]
        
        # Create industry subdirectory
        industry_slug = industry.lower().replace(' ', '_')
        industry_dir = output_dir_by_industry / industry_slug
        industry_dir.mkdir(parents=True, exist_ok=True)
        
        # Save industry-specific file
        output_file = industry_dir / f"queries_{industry_slug}.json"
        
        output_data = {"queries": industry_queries}
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ {industry}:")
        print(f"    Queries: {len(industry_queries)}")
        print(f"    File: {output_file}")
    
    # ====================================================================
    # Summary
    # ====================================================================
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    
    # Company statistics
    companies_by_industry = defaultdict(list)
    for cid in data:
        industry = COMPANY_TO_INDUSTRY.get(cid)
        if industry:
            companies_by_industry[industry].append(cid)
    
    print(f"\nCompanies by industry:")
    for industry in sorted(companies_by_industry.keys()):
        companies = companies_by_industry[industry]
        print(f"   {industry}: {len(companies)} companies")
        print(f"      → {', '.join(sorted(companies))}")
    
    print(f"\nQueries by industry:")
    for industry in sorted(queries_by_industry.keys()):
        print(f"   {industry}: {len(queries_by_industry[industry])} queries")
    
    print(f"\nTotal queries: {len(all_queries)}")
    
    # Code statistics
    unique_codes = set(q['code'] for q in all_queries)
    print(f"Unique codes: {len(unique_codes)}")
    
    # Average pages per query
    total_pages = sum(len(q['relevant_docs']) for q in all_queries)
    avg_pages = total_pages / len(all_queries) if all_queries else 0
    print(f"Average pages per query: {avg_pages:.2f}")
    
    print(f"\n{'='*80}\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Build Thai query files from Excel annotations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build queries from default Excel file
  python build_queries_thai.py
  
  # Specify custom paths
  python build_queries_thai.py --input FinalRound.xlsx --output queries_thai

Output:
  queries_thai/
    queries_thai_all.json  (combined file)
  
  queries_thai_by_industry/
    banking/
      queries_banking.json
    commerce/
      queries_commerce.json
    energy/
      queries_energy.json
        """
    )
    
    parser.add_argument(
        '--input',
        type=str,
        default='FinalRound.xlsx',
        help='Input Excel file (default: FinalRound.xlsx)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='queries_thai',
        help='Output base directory (default: queries_thai)'
    )
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).resolve().parent
    excel_file = base_dir / args.input
    output_dir_combined = base_dir / args.output
    output_dir_by_industry = base_dir / (args.output + "_by_industry")
    
    build_thai_queries(excel_file, output_dir_combined, output_dir_by_industry)
    
    print("✅ Done!")


if __name__ == "__main__":
    main()