# build_queries_japanese_new.py
"""
Build query files from Japanese RegCom dataset (NEW FORMAT)

First creates a combined file with all queries, then splits by industry.

Rules:
  - One query = (CID, Code, Metric)
  - Merge all pages of the same metric in the same PDF into relevant_docs
  - query_text == metric
  - Keep industry (corrected from dataset)
  - Use PDF_Page (actual PDF page number) instead of Page
  - Exclude entries with label == "no"
  - Include all data with valid PDF_Page numbers (PDF_Page != N/A)
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IN_JSON = BASE_DIR / "new_mixed.json"
OUT_DIR_COMBINED = BASE_DIR / "queries_japanese_new"
OUT_DIR_BY_INDUSTRY = BASE_DIR / "queries_japanese_new_by_industry"

# Company to Industry mapping (CORRECTED - actual company names from dataset)
COMPANY_INDUSTRY_MAPPING = {
    # Automotive
    "Honda Motor": "Automotive",
    "Nissan Motor": "Automotive",
    "Mazda Motor": "Automotive",
    
    # Energy
    "Tokyo Gas": "Energy",
    "Toho Gas": "Energy",
    "Hokkaido Gas": "Energy",
    
    # Trading Companies
    "ITOCHU Corp": "Trading_Companies",
    "Marubeni Corp": "Trading_Companies",
    "Sumitomo Corp": "Trading_Companies"
}

# Get list of target industries
TARGET_INDUSTRIES = sorted(set(COMPANY_INDUSTRY_MAPPING.values()))


def normalize_space(s: str) -> str:
    """Normalize spaces and handle None safely"""
    if s is None:
        return ""
    return " ".join(str(s).split())


def get_industry_from_cid(cid: str) -> str:
    """
    Get corrected industry from CID (company name)
    
    Args:
        cid: Company name (e.g., "Honda Motor", "Marubeni Corp")
    
    Returns:
        Industry name or None if not found
    """
    if not cid:
        return None
    
    # Try exact match first
    if cid in COMPANY_INDUSTRY_MAPPING:
        return COMPANY_INDUSTRY_MAPPING[cid]
    
    # Try partial match (e.g., "Marubeni Corp" contains "Marubeni")
    for company, industry in COMPANY_INDUSTRY_MAPPING.items():
        if company.lower() in cid.lower() or cid.lower() in company.lower():
            return industry
    
    return None


def page_to_image(cid: str, page: str):
    """Convert page number to standardized image name"""
    if not page or page == "N/A":
        return None
    
    try:
        p = int(page)
    except Exception:
        return None
    
    return f"{cid}_p{p:03d}.png"


def main():
    if not IN_JSON.exists():
        raise FileNotFoundError(f"Input file not found: {IN_JSON}")

    OUT_DIR_COMBINED.mkdir(parents=True, exist_ok=True)
    OUT_DIR_BY_INDUSTRY.mkdir(parents=True, exist_ok=True)

    with open(IN_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"\n{'='*80}")
    print("Building Japanese queries (NEW FORMAT)")
    print(f"{'='*80}")
    print(f"Input file: {IN_JSON}")
    print(f"Combined output: {OUT_DIR_COMBINED}")
    print(f"Split output: {OUT_DIR_BY_INDUSTRY}")
    print(f"\nKey changes from old format:")
    print(f"  - Using 'PDF_Page' instead of 'Page' for actual page numbers")
    print(f"  - Excluding entries with label == 'no'")
    print(f"\nCompany-Industry Mapping:")
    for industry in ["Automotive", "Energy", "Trading_Companies"]:
        companies = [c for c, i in COMPANY_INDUSTRY_MAPPING.items() if i == industry]
        print(f"\n  {industry}:")
        for company in companies:
            print(f"    - {company}")
    print(f"{'='*80}\n")

    # Store all queries by industry
    groups = {ind: {} for ind in TARGET_INDUSTRIES}
    
    skipped_no_page = 0
    skipped_unknown_company = 0
    skipped_label_no = 0
    unknown_companies = set()
    
    for row in data:
        # Extract fields
        cid = row.get("CID")
        code = normalize_space(row.get("Code"))
        topic = normalize_space(row.get("Topic"))
        metric = normalize_space(row.get("Metric"))
        
        # NEW: Use PDF_Page instead of Page
        pdf_page = row.get("PDF_Page")
        
        # NEW: Get label field
        label = row.get("label", "")

        # Basic checks
        if not cid or not code or not metric:
            continue

        # NEW: Skip entries with label == "no"
        if label == "no":
            skipped_label_no += 1
            continue

        # Get corrected industry from CID
        industry = get_industry_from_cid(cid)
        
        # Track unknown companies
        if industry is None:
            skipped_unknown_company += 1
            unknown_companies.add(cid)
            continue

        # Skip N/A pages (only include data with valid page numbers)
        if not pdf_page or pdf_page == "N/A":
            skipped_no_page += 1
            continue

        img = page_to_image(cid, pdf_page)
        if img is None:
            skipped_no_page += 1
            continue

        # Group by (CID, Code, Metric)
        key = (cid, code, metric)

        if key not in groups[industry]:
            groups[industry][key] = {
                "CID": cid,
                "industry": industry,
                "code": code,
                "topic": topic,
                "metric": metric,
                "query_text": metric,
                "relevant_docs": []
            }

        if img not in groups[industry][key]["relevant_docs"]:
            groups[industry][key]["relevant_docs"].append(img)

    print(f"Skipped entries:")
    print(f"  - label == 'no': {skipped_label_no}")
    print(f"  - N/A PDF_Page: {skipped_no_page}")
    print(f"  - Unknown companies: {skipped_unknown_company}")
    if unknown_companies:
        print(f"\n  Unknown company names found:")
        for company in sorted(unknown_companies):
            print(f"    - {company}")
    print()

    # ====================================================================
    # Step 1: Create combined file with ALL queries
    # ====================================================================
    print(f"{'='*80}")
    print("STEP 1: Creating combined query file")
    print(f"{'='*80}\n")
    
    all_queries = []
    industry_counts = {}
    
    for industry in TARGET_INDUSTRIES:
        queries = list(groups[industry].values())
        all_queries.extend(queries)
        industry_counts[industry] = len(queries)
        print(f"  {industry}: {len(queries)} queries")
    
    # Save combined file
    combined_file = OUT_DIR_COMBINED / "queries_japanese_all.json"
    combined_file.write_text(
        json.dumps({"queries": all_queries}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    print(f"\n✓ Combined file saved: {combined_file.name}")
    print(f"  Total queries: {len(all_queries)}")

    # ====================================================================
    # Step 2: Split by industry
    # ====================================================================
    print(f"\n{'='*80}")
    print("STEP 2: Splitting queries by industry")
    print(f"{'='*80}\n")
    
    for industry in TARGET_INDUSTRIES:
        queries = list(groups[industry].values())
        
        if not queries:
            print(f"⚠️  {industry}: No queries found, skipping")
            continue

        # Create industry subdirectory
        industry_slug = industry.lower().replace(' ', '_').replace('&', 'and')
        industry_dir = OUT_DIR_BY_INDUSTRY / industry_slug
        industry_dir.mkdir(parents=True, exist_ok=True)
        
        # Save industry-specific file
        out_file = industry_dir / f"queries_{industry_slug}.json"
        out_file.write_text(
            json.dumps({"queries": queries}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # Show companies in this industry
        companies = sorted(set(q["CID"] for q in queries))
        print(f"✓ {industry}:")
        print(f"    Queries: {len(queries)}")
        print(f"    Companies: {', '.join(companies)}")
        print(f"    Directory: {industry_dir}")
        print(f"    File: {out_file.name}\n")

    # ====================================================================
    # Summary
    # ====================================================================
    print(f"{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"\nCombined file:")
    print(f"  {combined_file}")
    print(f"  Total queries: {len(all_queries)}")
    
    print(f"\nSplit by industry:")
    for industry in sorted(industry_counts.keys()):
        count = industry_counts[industry]
        industry_slug = industry.lower().replace(' ', '_').replace('&', 'and')
        companies = [c for c, i in COMPANY_INDUSTRY_MAPPING.items() if i == industry]
        print(f"  {industry}: {count} queries")
        print(f"    Companies: {', '.join(companies)}")
        print(f"    → {OUT_DIR_BY_INDUSTRY / industry_slug}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()