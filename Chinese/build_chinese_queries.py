"""
Build query files for Chinese RegCom dataset

Uses CSV annotations to get precise page numbers for each metric (sid).

Format matches English/French structure:
- CID = PDF filename (e.g., "Alchip.pdf")
- Group metrics by code (same code → one query with multiple metrics)
- relevant_docs = actual annotated pages from CSV (not full range)
- query_text = ONLY metric text (no units)
- Include industry field
- No complete field (not in data)
"""

import json
import csv
from pathlib import Path
from collections import defaultdict


# PDF filename mapping (JSON stem -> actual PDF name)
PDF_NAME_MAPPING = {
    "alchip": "Alchip.pdf",
    "esun": "E.SUN.pdf",
    "fpcc": "FPCC.pdf",
    "gtg": "GTG.pdf",
    "inx": "INX.pdf",
    "kye": "KYE.pdf",
    "largan": "LARGAN.pdf",
    "mfhc": "MFHC.pdf",
    "npc": "NPC.pdf",
    "pegavision": "pegavision.pdf",
    "psi": "PSI.pdf",
    "spt": "SPT.pdf",
    "standard": "Standard.pdf",
    "tcfh": "TCFH.pdf",
    "tsmc": "TSMC.pdf"
}

# Industry mapping
INDUSTRY_MAPPING = {
    "TSMC.pdf": "Semiconductor",
    "Alchip.pdf": "Semiconductor",
    "PSI.pdf": "Semiconductor",
    "FPCC.pdf": "Energy",
    "NPC.pdf": "Energy",
    "GTG.pdf": "Energy",
    "pegavision.pdf": "Biomedical",
    "Standard.pdf": "Biomedical",
    "SPT.pdf": "Biomedical",
    "MFHC.pdf": "Finance",
    "E.SUN.pdf": "Finance",
    "TCFH.pdf": "Finance",
    "LARGAN.pdf": "Technology",
    "INX.pdf": "Technology",
    "KYE.pdf": "Technology"
}


def normalize_space(s: str) -> str:
    """Normalize spaces and handle None safely"""
    if s is None:
        return ""
    return " ".join(str(s).split())


def json_to_pdf_name(json_filename: str) -> str:
    """
    Convert JSON filename to PDF filename using mapping
    e.g., "alchip.json" -> "Alchip.pdf"
          "esun.json" -> "E.SUN.pdf"
    """
    stem = Path(json_filename).stem.lower()
    return PDF_NAME_MAPPING.get(stem, f"{stem.capitalize()}.pdf")


def page_to_image(cid: str, page: int) -> str:
    """
    Convert page number to standardized image name
    e.g., "Alchip.pdf", page 53 -> "Alchip_p053.png"
    """
    stem = Path(cid).stem
    return f"{stem}_p{page:03d}.png"


def load_annotations(annotation_dir, company_stem):
    """
    Load CSV annotations for a company to get precise page numbers for each sid.
    
    Args:
        annotation_dir: Path to Annotations directory
        company_stem: Company name stem (e.g., "alchip")
    
    Returns:
        dict: {sid: set(page_numbers)}
    """
    annotation_dir = Path(annotation_dir)
    
    # Find CSV files for this company (e.g., alchip_3.csv)
    csv_files = list(annotation_dir.glob(f"{company_stem}_*.csv"))
    
    if not csv_files:
        print(f"    ⚠ No annotation CSV found for {company_stem}")
        return {}
    
    # sid -> set of pages
    sid_pages = defaultdict(set)
    
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        sid = int(row['sid'])
                        page = int(row['page'])
                        sid_pages[sid].add(page)
                    except (ValueError, KeyError) as e:
                        continue
        except Exception as e:
            print(f"    ⚠ Error reading {csv_file}: {e}")
            continue
    
    # Convert sets to sorted lists
    sid_pages = {sid: sorted(pages) for sid, pages in sid_pages.items()}
    
    return sid_pages


def build_chinese_queries(json_dir, annotation_dir, output_dir):
    """
    Build queries for Chinese dataset following English/French format.
    Uses CSV annotations to get precise page numbers.
    Uses ONLY metric text for query (no units).
    Splits queries by industry into separate files.
    
    IMPORTANT: Only creates queries for metrics that have CSV annotations.
    Metrics without annotations are skipped.
    
    Args:
        json_dir: Directory containing Chinese metric JSON files
        annotation_dir: Directory containing CSV annotation files
        output_dir: Output directory for industry-specific query files
    """

    json_dir = Path(json_dir)
    annotation_dir = Path(annotation_dir)
    output_dir = Path(output_dir)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    if not json_dir.exists():
        raise FileNotFoundError(f"Directory not found: {json_dir}")
    
    if not annotation_dir.exists():
        raise FileNotFoundError(f"Annotation directory not found: {annotation_dir}")

    json_files = sorted(json_dir.glob("*.json"))

    print(f"Found {len(json_files)} JSON files in {json_dir}")
    print("=" * 70)

    # Group queries by industry
    industry_queries = defaultdict(list)

    # Process each company JSON file
    for json_file in json_files:
        print(f"\nProcessing: {json_file.name}")

        company_stem = json_file.stem.lower()
        cid = json_to_pdf_name(json_file.name)
        industry = INDUSTRY_MAPPING.get(cid, "Unknown")
        
        print(f"  CID: {cid}")
        print(f"  Industry: {industry}")

        # Load annotations for this company
        sid_pages = {}
        if annotation_dir:
            sid_pages = load_annotations(annotation_dir, company_stem)
            if sid_pages:
                print(f"  ✓ Loaded annotations for {len(sid_pages)} sids")
            else:
                print(f"  ⚠ No annotations found, skipping this company")
                continue

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"  ✗ Error reading file: {e}")
            continue

        # Group by code, track sids for each code
        code_groups = defaultdict(lambda: {
            "metrics": [],
            "topic": "",
            "page_range": [],
            "sids": []
        })
        
        skipped_sids = []

        # Iterate structure
        for topic_item in data:
            topic_name = normalize_space(topic_item.get("name", ""))
            page_range = topic_item.get("page", [])

            for code_item in topic_item.get("codes", []):
                code = normalize_space(code_item.get("code", ""))

                if not code:
                    continue

                # first time assign topic/page
                if not code_groups[code]["topic"]:
                    code_groups[code]["topic"] = topic_name
                if not code_groups[code]["page_range"]:
                    code_groups[code]["page_range"] = page_range

                for metric_item in code_item.get("metrics", []):
                    sid = metric_item.get("sid")
                    
                    # Skip metrics without CSV annotations
                    if sid not in sid_pages:
                        skipped_sids.append(sid)
                        continue
                    
                    metric_text = normalize_space(metric_item.get("metric", ""))
                    category = normalize_space(metric_item.get("category", ""))
                    unit = normalize_space(metric_item.get("unit", ""))

                    if not metric_text:
                        continue

                    code_groups[code]["metrics"].append({
                        "sid": sid,
                        "metric": metric_text,
                        "category": category,
                        "unit": unit
                    })
                    
                    code_groups[code]["sids"].append(sid)

        # Build queries
        query_count = 0
        for code, group_data in code_groups.items():
            metrics_list = group_data["metrics"]
            topic = group_data["topic"]
            page_range = group_data["page_range"]
            sids = group_data["sids"]

            if not metrics_list:
                continue

            # Query text uses ONLY metric text (no units or categories)
            metric_texts = [m["metric"] for m in metrics_list]
            query_text = " | ".join(metric_texts)

            # Build relevant_docs from CSV annotations ONLY
            relevant_docs = []
            pages_set = set()
            
            # Collect all pages for all sids in this code
            for sid in sids:
                if sid in sid_pages:
                    pages_set.update(sid_pages[sid])
            
            # Convert to sorted list of image names
            if pages_set:
                for page in sorted(pages_set):
                    relevant_docs.append(page_to_image(cid, page))
            else:
                print(f"    ⚠ Warning: No pages found for code {code}, skipping")
                continue

            query_obj = {
                "CID": cid,
                "industry": industry,
                "code": code,
                "topic": topic,
                "metric": " | ".join(metric_texts),
                "query_text": query_text,
                "relevant_docs": relevant_docs
            }

            industry_queries[industry].append(query_obj)
            query_count += 1

        print(f"  ✓ Created {query_count} queries")
        if skipped_sids:
            print(f"  ⓘ Skipped {len(skipped_sids)} metrics without annotations: {sorted(set(skipped_sids))}")

    # Save queries by industry
    print("\n" + "=" * 70)
    print("Saving queries by industry...")
    
    all_queries_count = 0
    for industry, queries in industry_queries.items():
        output_file = output_dir / f"queries_chinese_{industry.lower()}.json"
        output_data = {"queries": queries}
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        all_queries_count += len(queries)
        print(f"  ✓ {industry}: {len(queries)} queries -> {output_file}")

    print("\n" + "=" * 70)
    print("Statistics:")
    print(f"  Total industries: {len(industry_queries)}")
    print(f"  Total queries: {all_queries_count}")
    
    for industry, queries in sorted(industry_queries.items()):
        companies = set(q["CID"] for q in queries)
        codes = set(q["code"] for q in queries)
        total_pages = sum(len(q["relevant_docs"]) for q in queries)
        avg_pages = total_pages / len(queries) if queries else 0
        
        print(f"\n  {industry}:")
        print(f"    Companies: {len(companies)}")
        print(f"    Unique codes: {len(codes)}")
        print(f"    Queries: {len(queries)}")
        print(f"    Avg pages per query: {avg_pages:.1f}")
    
    # Print sample queries
    print("\n" + "=" * 70)
    print("Sample queries (first query from each industry):")
    for industry in sorted(industry_queries.keys()):
        queries = industry_queries[industry]
        if queries:
            query = queries[0]
            print(f"\n{industry} - Query 1:")
            print(f"  CID: {query['CID']}")
            print(f"  Code: {query['code']}")
            print(f"  Topic: {query['topic']}")
            print(f"  Query text: {query['query_text'][:150]}...")
            print(f"  Relevant docs: {len(query['relevant_docs'])} pages")

    return industry_queries


if __name__ == "__main__":

    json_dir = Path("Metric (sid)")
    annotation_dir = Path("Annotations")
    output_dir = Path("queries_chinese_by_industry")

    print("Building Chinese queries (English/French format)")
    print(f"Input JSON directory: {json_dir}")
    print(f"Input Annotation directory: {annotation_dir}")
    print(f"Output directory: {output_dir}")
    print("=" * 70)

    build_chinese_queries(json_dir, annotation_dir, output_dir)

    print("\n✓ Done!")