"""
Build query files for Korean RegCom dataset with industry organization

Uses CSV annotations to get page numbers and metrics.

Key features:
- Generates two query files per industry: all data (mixed) and complete=TRUE only
- Includes topic field from CSV
- Includes complete_flag and industry fields
- Code is global (same metric across companies = same code)
- Query is per (CID, Metric) combination
- Organizes output by industry

Format:
- CID = PDF filename (e.g., "bh.pdf")
- Code = auto-generated based on metric text (e.g., "METRIC_001")
- Group by (CID, Metric) → one query per company-metric combination
- relevant_docs = pages from CSV for that (CID, Metric)
- industry = Hardware/Automobile/Semiconductors
"""

import csv
from pathlib import Path
from collections import defaultdict
import json


# Company to Industry mapping
COMPANY_INDUSTRY_MAPPING = {
    # Hardware
    "samsung_electronics.pdf": "Hardware",
    "samsung_electro_mechanics.pdf": "Hardware",
    "bh.pdf": "Hardware",
    
    # Automobile
    "hyundai.pdf": "Automobile",
    "kia.pdf": "Automobile",
    "kgm.pdf": "Automobile",
    
    # Semiconductors
    "skhynix.pdf": "Semiconductors",
    "hana_micron.pdf": "Semiconductors",
    "nepes.pdf": "Semiconductors"
}

# Get list of target industries
TARGET_INDUSTRIES = sorted(set(COMPANY_INDUSTRY_MAPPING.values()))


def normalize_space(s: str) -> str:
    """Normalize spaces and handle None safely"""
    if s is None:
        return ""
    return " ".join(str(s).split())


def page_to_image(cid: str, page: int) -> str:
    """
    Convert page number to standardized image name
    e.g., "bh.pdf", page 53 -> "bh_p053.png"
    """
    stem = Path(cid).stem
    return f"{stem}_p{page:03d}.png"


def get_industry_from_cid(cid: str) -> str:
    """
    Get industry from CID (PDF filename)
    
    Args:
        cid: PDF filename (e.g., "samsung_electronics.pdf")
    
    Returns:
        Industry name or None if not found
    """
    return COMPANY_INDUSTRY_MAPPING.get(cid)


def generate_code_from_metric(metric: str, metric_to_code: dict) -> str:
    """
    Generate or retrieve code for a metric
    Same metric across all companies gets the same code
    
    Args:
        metric: Metric text
        metric_to_code: Dictionary mapping metrics to codes
    
    Returns:
        Code string (e.g., "METRIC_001")
    """
    if metric not in metric_to_code:
        # Generate new code
        code_num = len(metric_to_code) + 1
        metric_to_code[metric] = f"METRIC_{code_num:03d}"
    
    return metric_to_code[metric]


def load_korean_annotations(annotation_dir, filter_complete=False):
    """
    Load all Korean CSV annotations
    
    Args:
        annotation_dir: Path to annotation_csv directory
        filter_complete: If True, only include rows where complete=TRUE
    
    Returns:
        dict: {cid: {metric: {'pages': [pages], 'topic': topic, 'complete_flag': str, 'industry': str}}}
    """
    annotation_dir = Path(annotation_dir)
    
    if not annotation_dir.exists():
        raise FileNotFoundError(f"Annotation directory not found: {annotation_dir}")
    
    # Find all CSV files
    csv_files = list(annotation_dir.glob("*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {annotation_dir}")
    
    print(f"Found {len(csv_files)} CSV files")
    print(f"Filter complete=TRUE only: {filter_complete}")
    
    # Structure: {cid: {metric: {'pages': set(), 'topic': str, 'complete_flag': str, 'industry': str}}}
    data = defaultdict(lambda: defaultdict(lambda: {'pages': set(), 'topic': '', 'complete_flag': '', 'industry': ''}))
    
    skipped_incomplete = 0
    skipped_unknown_company = 0
    
    for csv_file in csv_files:
        # CID is the CSV filename (e.g., "bh.csv" -> "bh.pdf")
        cid = csv_file.stem + ".pdf"
        
        # Get industry from CID
        industry = get_industry_from_cid(cid)
        
        if industry is None:
            print(f"\n⚠️  Skipping unknown company: {cid}")
            skipped_unknown_company += 1
            continue
        
        print(f"\nProcessing: {csv_file.name}")
        print(f"  CID: {cid}")
        print(f"  Industry: {industry}")
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                row_count = 0
                for row in reader:
                    try:
                        # Get complete flag
                        complete = row.get('complete', '').strip().upper()
                        
                        # Check complete field if filtering
                        if filter_complete:
                            if complete != 'TRUE':
                                skipped_incomplete += 1
                                continue
                        
                        # In Korean data: sid IS the metric text
                        metric = normalize_space(row.get('sid', ''))
                        topic = normalize_space(row.get('topic', ''))
                        page = row.get('page', '')
                        
                        # Skip if metric or page is empty
                        if not metric or not page:
                            continue
                        
                        # Convert page to int
                        page_num = int(page)
                        
                        # Add to data structure
                        data[cid][metric]['pages'].add(page_num)
                        
                        # Store topic (should be same for all rows of this metric)
                        if not data[cid][metric]['topic']:
                            data[cid][metric]['topic'] = topic
                        
                        # Store complete flag (should be same for all rows of this metric)
                        if not data[cid][metric]['complete_flag']:
                            data[cid][metric]['complete_flag'] = complete
                        
                        # Store industry
                        data[cid][metric]['industry'] = industry
                        
                        row_count += 1
                        
                    except (ValueError, KeyError) as e:
                        continue
                
                print(f"  ✓ Loaded {row_count} annotations")
                print(f"  ✓ Unique metrics: {len(data[cid])}")
        
        except Exception as e:
            print(f"  ✗ Error reading {csv_file}: {e}")
            continue
    
    if skipped_unknown_company > 0:
        print(f"\n⚠️  Skipped {skipped_unknown_company} files from unknown companies")
    
    if filter_complete:
        print(f"\n⚠️  Skipped {skipped_incomplete} rows with complete≠TRUE")
    
    # Convert sets to sorted lists
    for cid in data:
        for metric in data[cid]:
            data[cid][metric]['pages'] = sorted(data[cid][metric]['pages'])
    
    return data


def build_korean_queries(annotation_dir, output_dir, filter_complete=False):
    """
    Build queries for Korean dataset, organized by industry
    
    Args:
        annotation_dir: Directory containing CSV annotation files
        output_dir: Base output directory
        filter_complete: If True, only include complete=TRUE annotations
    """
    
    mode = "complete=TRUE only" if filter_complete else "all data (mixed)"
    suffix = "complete_yes" if filter_complete else "mixed"
    
    print("=" * 70)
    print(f"Building Korean queries ({mode})")
    print("=" * 70)
    print(f"Input directory: {annotation_dir}")
    print(f"Output directory: {output_dir}")
    print("=" * 70)
    
    # Load all annotations
    data = load_korean_annotations(annotation_dir, filter_complete)
    
    # Global metric to code mapping (same metric = same code across all companies)
    metric_to_code = {}
    
    # Group queries by industry
    industry_queries = {ind: [] for ind in TARGET_INDUSTRIES}
    
    print("\n" + "=" * 70)
    print("Building queries")
    print("=" * 70)
    
    for cid in sorted(data.keys()):
        industry = get_industry_from_cid(cid)
        
        if industry is None:
            continue
        
        print(f"\nProcessing CID: {cid} ({industry})")
        
        query_count = 0
        
        for metric, metric_data in sorted(data[cid].items()):
            pages = metric_data['pages']
            topic = metric_data['topic']
            complete_flag = metric_data['complete_flag']
            
            # Generate or get code for this metric
            code = generate_code_from_metric(metric, metric_to_code)
            
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
                "relevant_docs": relevant_docs,
                "complete_flag": complete_flag
            }
            
            industry_queries[industry].append(query_obj)
            query_count += 1
        
        print(f"  ✓ Created {query_count} queries")
    
    # Save queries by industry
    print("\n" + "=" * 70)
    print("Saving queries by industry")
    print("=" * 70)
    
    all_queries_count = 0
    
    for industry in TARGET_INDUSTRIES:
        queries = industry_queries[industry]
        
        if not queries:
            print(f"\n⚠️  {industry}: No queries found, skipping")
            continue
        
        # Create industry subdirectory
        industry_slug = industry.lower().replace(' ', '_')
        industry_dir = output_dir / industry_slug
        industry_dir.mkdir(parents=True, exist_ok=True)
        
        # Save industry-specific file
        output_file = industry_dir / f"queries_korean_{industry_slug}_{suffix}.json"
        
        output_data = {"queries": queries}
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        all_queries_count += len(queries)
        
        # Print statistics for this industry
        companies = set(q["CID"] for q in queries)
        codes = set(q["code"] for q in queries)
        topics = set(q["topic"] for q in queries if q["topic"])
        
        print(f"\n✓ {industry}:")
        print(f"    File: {output_file.name}")
        print(f"    Companies: {len(companies)}")
        print(f"    Unique codes: {len(codes)}")
        print(f"    Unique topics: {len(topics)}")
        print(f"    Queries: {len(queries)}")
        print(f"    Avg pages per query: {sum(len(q['relevant_docs']) for q in queries) / len(queries):.1f}")
        
        # Show complete status distribution for this industry (if mixed mode)
        if not filter_complete:
            complete_counts = defaultdict(int)
            for q in queries:
                complete_counts[q['complete_flag']] += 1
            
            print(f"    Complete status:")
            for status, count in sorted(complete_counts.items()):
                print(f"      {status}: {count}")
    
    # Print overall statistics
    print("\n" + "=" * 70)
    print("Overall Statistics:")
    print(f"  Mode: {mode}")
    print(f"  Total queries: {all_queries_count}")
    print(f"  Total unique codes (metrics): {len(metric_to_code)}")
    print(f"  Total industries: {len([i for i in TARGET_INDUSTRIES if industry_queries[i]])}")
    
    # Show industry breakdown
    print("\n  Queries by industry:")
    for industry in sorted(TARGET_INDUSTRIES):
        count = len(industry_queries[industry])
        if count > 0:
            companies = set(q["CID"] for q in industry_queries[industry])
            print(f"    {industry}: {count} queries, {len(companies)} companies")
    
    # Show top metrics across all industries
    print("\n  Top 10 most common metrics (by company count):")
    code_company_count = defaultdict(set)
    all_queries_list = []
    for queries in industry_queries.values():
        all_queries_list.extend(queries)
    
    for q in all_queries_list:
        code_company_count[q["code"]].add(q["CID"])
    
    sorted_codes = sorted(code_company_count.items(), 
                         key=lambda x: len(x[1]), reverse=True)
    
    for code, companies_set in sorted_codes[:10]:
        # Find metric for this code
        metric = next(q["metric"] for q in all_queries_list if q["code"] == code)
        print(f"    {code}: {len(companies_set)} companies - {metric[:60]}...")
    
    # Print sample queries from first industry with data
    for industry in TARGET_INDUSTRIES:
        queries = industry_queries[industry]
        if queries:
            print(f"\n  Sample queries from {industry}:")
            for i, query in enumerate(queries[:2]):
                print(f"\n  Query {i+1}:")
                print(f"    CID: {query['CID']}")
                print(f"    Industry: {query['industry']}")
                print(f"    Code: {query['code']}")
                print(f"    Topic: {query['topic'][:60]}..." if query['topic'] else "    Topic: N/A")
                print(f"    Metric: {query['metric'][:80]}...")
                print(f"    Complete: {query['complete_flag']}")
                print(f"    Relevant docs: {len(query['relevant_docs'])} pages")
            break
    
    print("\n" + "=" * 70)
    
    return all_queries_list


if __name__ == "__main__":
    # Set paths (relative to current directory)
    annotation_dir = Path("annotation_csv")
    output_base_dir = Path("queries_korean_by_industry")
    
    # Create base output directory
    output_base_dir.mkdir(exist_ok=True)
    
    print("\n" + "=" * 80)
    print("KOREAN QUERY BUILDING - DUAL MODE WITH INDUSTRY ORGANIZATION")
    print("=" * 80)
    print(f"Input annotation directory: {annotation_dir}")
    print(f"Output base directory: {output_base_dir}")
    print("\nCompany-Industry Mapping:")
    for industry in sorted(set(COMPANY_INDUSTRY_MAPPING.values())):
        companies = [cid for cid, ind in COMPANY_INDUSTRY_MAPPING.items() if ind == industry]
        print(f"\n  {industry}:")
        for company in sorted(companies):
            print(f"    - {company}")
    print("=" * 80)
    
    # Build queries for all data (mixed: complete=TRUE + FALSE)
    print("\n\n" + "🔵 " * 20)
    print("MODE 1: Building queries with ALL data (complete=TRUE + FALSE)")
    print("🔵 " * 20)
    
    queries_mixed = build_korean_queries(annotation_dir, output_base_dir, filter_complete=False)
    
    # Build queries for complete=TRUE only
    print("\n\n" + "🟢 " * 20)
    print("MODE 2: Building queries with complete=TRUE only")
    print("🟢 " * 20)
    
    queries_complete = build_korean_queries(annotation_dir, output_base_dir, filter_complete=True)
    
    # Final summary
    print("\n\n" + "=" * 80)
    print("✅ ALL DONE!")
    print("=" * 80)
    print(f"\n📁 Output structure:")
    print(f"   {output_base_dir}/")
    for industry in sorted(set(COMPANY_INDUSTRY_MAPPING.values())):
        industry_slug = industry.lower().replace(' ', '_')
        print(f"   ├── {industry_slug}/")
        print(f"   │   ├── queries_korean_{industry_slug}_mixed.json")
        print(f"   │   └── queries_korean_{industry_slug}_complete_yes.json")
    
    print(f"\n📊 Summary:")
    print(f"   Mixed mode (all data):")
    print(f"     Total queries: {len(queries_mixed)}")
    print(f"     Industries: {len(set(q['industry'] for q in queries_mixed))}")
    
    print(f"\n   Complete=TRUE mode:")
    print(f"     Total queries: {len(queries_complete)}")
    print(f"     Industries: {len(set(q['industry'] for q in queries_complete))}")
    
    print(f"\n   Difference:")
    print(f"     Filtered out: {len(queries_mixed) - len(queries_complete)} queries (complete≠TRUE)")
    
    print("\n" + "=" * 80 + "\n")