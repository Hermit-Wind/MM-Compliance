# run_colqwen_retrieval_eval_mixed.py

import json
import time
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Set

import torch
import numpy as np
from PIL import Image
from tqdm import tqdm
from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor


# ================================
# PATH SETTINGS
# ================================
BASE_DIR = Path(__file__).resolve().parent
PAGES_DIR = BASE_DIR / "pages"
QUERY_DIR = BASE_DIR / "queries_regcom_mixed"   # <<< changed
OUT_DIR = BASE_DIR / "results_colqwen_eval_mixed"  # <<< changed
CACHE_DIR = BASE_DIR / "cache"

MODEL_NAME = "vidore/colqwen2.5-v0.2"
DEVICE = "cuda:0"
BATCH_SIZE = 1  # Process one at a time for dynamic resolution


# =====================================================
# EVALUATION METRICS
# =====================================================
def calculate_ndcg_at_k(ranked_pages, relevant_pages, k=10):
    """Calculate nDCG@K"""
    if not relevant_pages:
        return 0.0
    dcg = 0.0
    for i, p in enumerate(ranked_pages[:k]):
        if p in relevant_pages:
            dcg += 1.0 / np.log2(i + 2)
    idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(relevant_pages), k)))
    return dcg / idcg if idcg > 0 else 0.0


def calculate_recall_at_k(ranked_pages, relevant_pages, k=10):
    """Calculate Recall@K"""
    if not relevant_pages:
        return 0.0
    return len(set(ranked_pages[:k]) & relevant_pages) / len(relevant_pages)


def calculate_precision_at_k(ranked_pages, relevant_pages, k=10):
    """Calculate Precision@K"""
    if not relevant_pages:
        return 0.0
    return len(set(ranked_pages[:k]) & relevant_pages) / k


def calculate_hit_rate_at_k(ranked_pages, relevant_pages, k=10):
    """Calculate Hit@K"""
    if not relevant_pages:
        return 0.0
    return 1.0 if len(set(ranked_pages[:k]) & relevant_pages) > 0 else 0.0


def evaluate_retrieval(scores, gt_indices, k_values=[1, 5, 10, 20]):
    """Complete evaluation function - K=1,5,10,20"""
    metrics = defaultdict(list)
    per_query = []

    for qi in range(scores.shape[0]):
        ranked = torch.argsort(scores[qi], descending=True).tolist()
        gt = set(gt_indices[qi])

        qm = {}
        for k in k_values:
            qm[f"Recall@{k}"] = calculate_recall_at_k(ranked, gt, k)
            qm[f"nDCG@{k}"] = calculate_ndcg_at_k(ranked, gt, k)
            qm[f"Precision@{k}"] = calculate_precision_at_k(ranked, gt, k)
            qm[f"Hit@{k}"] = calculate_hit_rate_at_k(ranked, gt, k)
            
        for name, val in qm.items():
            metrics[name].append(val)

        per_query.append({
            "num_relevant": len(gt),
            "ranked_indices": ranked,
            "metrics": qm
        })

    summary = {k: float(np.mean(v)) for k, v in metrics.items()}
    summary["num_queries"] = scores.shape[0]
    summary["avg_relevant_pages"] = float(np.mean([len(x) for x in gt_indices]))

    return {"summary": summary, "per_query": per_query}


# =====================================================
# Print Functions
# =====================================================
def print_evaluation_results(results):
    """Format and print evaluation results"""
    summary = results['summary']
    
    print("\n" + "=" * 90)
    print(" " * 30 + "RETRIEVAL EVALUATION RESULTS")
    print("=" * 90)
    
    print(f"\n📊 Dataset Statistics:")
    print(f"   Total queries: {summary['num_queries']}")
    print(f"   Avg relevant pages per query: {summary['avg_relevant_pages']:.2f}")
    
    print(f"\n{'Metric':<20} {'K=1':<12} {'K=5':<12} {'K=10':<12} {'K=20':<12}")
    print("-" * 90)
    
    for metric_type in ['Recall', 'nDCG', 'Precision', 'Hit']:
        row = f"{metric_type}@K"
        for k in [1, 5, 10, 20]:
            key = f'{metric_type}@{k}'
            if key in summary:
                score = summary[key]
                row += f"  {score*100:>6.2f}%    "
        print(row)
    
    print("\n" + "=" * 90)


def print_per_query_analysis(results, queries, doc_names, top_n=3):
    """Print detailed per-query analysis"""
    per_query = results['per_query']
    
    print("\n" + "=" * 90)
    print(f" " * 25 + f"PER-QUERY ANALYSIS (First {top_n} Queries)")
    print("=" * 90)
    
    for i in range(min(top_n, len(per_query))):
        qr = per_query[i]
        q = queries[i]
        
        print(f"\n📝 [Query {i}]")
        print(f"   CID: {q['CID']}")
        print(f"   Code: {q.get('code', 'N/A')}")
        print(f"   Metric: {q['metric'][:60]}...")
        print(f"   Relevant pages: {qr['num_relevant']}")
        
        print(f"\n   {'K':<5} {'Recall':<10} {'nDCG':<10} {'Precision':<10} {'Hit':<10}")
        print("   " + "-" * 50)
        
        m = qr['metrics']
        for k in [1, 5, 10, 20]:
            print(f"   {k:<5} "
                  f"{m[f'Recall@{k}']*100:>6.2f}%   "
                  f"{m[f'nDCG@{k}']*100:>6.2f}%   "
                  f"{m[f'Precision@{k}']*100:>6.2f}%   "
                  f"{m[f'Hit@{k}']*100:>6.2f}%")
        
        print(f"\n   🎯 Top-10 Retrieved Pages:")
        ranked = qr['ranked_indices']
        for rank, page_idx in enumerate(ranked[:10], 1):
            print(f"      {rank:2d}. {doc_names[page_idx]}")
        
        print("\n" + "-" * 90)


def validate_filtering(scores, queries, doc_names, num_samples=3):
    """Validate document boundary filtering"""
    print(f"\n{'='*90}")
    print(f" " * 25 + f"FILTERING VALIDATION (First {num_samples} Queries)")
    print(f"{'='*90}")

    doc_to_pages = defaultdict(list)
    for i, n in enumerate(doc_names):
        doc_to_pages[get_doc_prefix_from_image(n)].append(i)

    for qi in range(min(num_samples, len(queries))):
        q = queries[qi]
        cid = q["CID"]
        prefix = get_doc_prefix_from_cid(cid)
        valid = set(doc_to_pages[prefix])

        top5_idx = torch.topk(scores[qi], 5).indices.tolist()
        top5_val = torch.topk(scores[qi], 5).values.tolist()

        print(f"\n📄 [Query {qi}]")
        print(f"   Metric: {q['metric'][:60]}...")
        print(f"   CID: {cid}")
        print(f"   Valid pages: {len(valid)}")
        print(f"\n   {'Rank':<6} {'Page':<45} {'Score':<10} {'Status'}")
        print("   " + "-" * 75)

        for rank, (idx, val) in enumerate(zip(top5_idx, top5_val), 1):
            status = "✓ Valid" if idx in valid else "✗ CROSS-DOC"
            print(f"   {rank:<6} {doc_names[idx]:<45} {val:>8.4f}   {status}")

    print("\n" + "=" * 90)


# =====================================================
# Utility
# =====================================================
def get_doc_prefix_from_cid(cid: str):
    return Path(cid).stem.lower()


def get_doc_prefix_from_image(img: str):
    return img.rsplit("_p", 1)[0].lower()


# =====================================================
# Load data
# =====================================================
def load_pages_and_queries(industry: str):
    print(f"\n[INFO] Loading industry = {industry}")
    
    img_paths = sorted(PAGES_DIR.glob("*.png"))
    img_names = [p.name for p in img_paths]
    print(f"[INFO] Found {len(img_paths)} page images")
    
    images = [Image.open(p).convert("RGB") for p in tqdm(img_paths, desc="Loading images")]

    qfile = QUERY_DIR / f"queries_{industry}.json"
    queries = json.loads(qfile.read_text(encoding="utf-8"))["queries"]
    print(f"[INFO] Loaded {len(queries)} queries")

    name2idx = {n: i for i, n in enumerate(img_names)}
    gt_indices = []

    for q in queries:
        gt = [name2idx[p] for p in q["relevant_docs"] if p in name2idx]
        gt_indices.append(gt)

    print("[INFO] Ground truth loaded")
    return images, img_names, queries, gt_indices


# =====================================================
# Encode images with cache (ColQwen2.5 - dynamic resolution)
# =====================================================
def encode_images_with_cache(images, processor, model):
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / "cache_colqwen_image_emb_all.pt"

    if cache_file.exists():
        print(f"[INFO] Loading cached image embeddings")
        return torch.load(cache_file)

    print("[INFO] Encoding images with ColQwen2.5 (dynamic resolution)...")
    all_emb = []
    
    # Process images one at a time due to dynamic resolution
    for img in tqdm(images, desc="Encoding images"):
        batch_images = processor.process_images([img]).to(model.device)
        
        with torch.no_grad():
            emb = model(**batch_images)
        
        all_emb.append(emb.cpu())

    # Store as list since embeddings have different shapes
    print("[INFO] Image embeddings cached (list format)")
    torch.save(all_emb, cache_file)
    return all_emb


def encode_queries(qtexts, processor, model):
    """
    Encode queries one at a time (dynamic length)
    """
    print("[INFO] Encoding queries with ColQwen2.5 (dynamic length)...")
    all_emb = []
    
    # Process queries one at a time
    for qtext in tqdm(qtexts, desc="Encoding queries"):
        batch_queries = processor.process_queries([qtext]).to(model.device)
        
        with torch.no_grad():
            emb = model(**batch_queries)
        
        all_emb.append(emb.cpu())

    # Store as list since queries also have variable lengths
    print("[INFO] Query embeddings encoded (list format)")
    return all_emb


# =====================================================
# Compute scores with dynamic resolution embeddings
# =====================================================
def compute_scores_dynamic(query_embeddings_list, doc_embeddings_list, processor):
    """
    Compute scores when both queries and documents have variable lengths
    
    Args:
        query_embeddings_list: List of tensors, each [1, num_query_tokens, dim]
        doc_embeddings_list: List of tensors, each [1, num_doc_tokens, dim]
        processor: ColQwen2_5_Processor
    
    Returns:
        scores: Tensor [num_queries, num_docs]
    """
    num_queries = len(query_embeddings_list)
    num_docs = len(doc_embeddings_list)
    
    scores = torch.zeros(num_queries, num_docs)
    
    print(f"\n[INFO] Computing scores for {num_queries} queries x {num_docs} documents...")
    
    for qi in tqdm(range(num_queries), desc="Computing query scores"):
        query_emb = query_embeddings_list[qi]  # [1, num_query_tokens, dim]
        
        doc_scores = []
        for doc_emb in doc_embeddings_list:
            # Compute score for this query-document pair
            score = processor.score_multi_vector(query_emb, doc_emb)
            doc_scores.append(score.item())
        
        scores[qi] = torch.tensor(doc_scores)
    
    return scores


# =====================================================
# Document boundary filtering
# =====================================================
def apply_filtering(scores, queries, doc_names):
    print("\n[INFO] Applying document boundary filtering...")
    
    doc_to_pages = defaultdict(list)
    for i, n in enumerate(doc_names):
        doc_to_pages[get_doc_prefix_from_image(n)].append(i)

    filtered = scores.clone()
    for qi, q in enumerate(queries):
        prefix = get_doc_prefix_from_cid(q["CID"])
        valid = doc_to_pages[prefix]
        mask = torch.full((scores.shape[1],), float("-inf"))
        mask[valid] = 0.0
        filtered[qi] += mask

    print("[INFO] Filtering complete")
    return filtered


# =====================================================
# Main
# =====================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="ColQwen2.5 Retrieval Evaluation (MIXED)")
    parser.add_argument("--industry", required=True, 
                       choices=["finance", "energy", "luxury"],
                       help="Industry to evaluate")
    args = parser.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    
    print("\n" + "=" * 90)
    print(" " * 23 + "ColQwen2.5 Retrieval Evaluation System (MIXED)")
    print("=" * 90)

    # Step 1: Load data
    images, doc_names, queries, gt_indices = load_pages_and_queries(args.industry)
    qtexts = [q["query_text"] for q in queries]

    # Step 2: Load ColQwen2.5 model
    print(f"\n[INFO] Loading model: {MODEL_NAME}")
    
    try:
        from transformers.utils.import_utils import is_flash_attn_2_available
        use_flash_attn = is_flash_attn_2_available()
    except:
        use_flash_attn = False
    
    model = ColQwen2_5.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.bfloat16,
        device_map=DEVICE,
        attn_implementation="flash_attention_2" if use_flash_attn else None,
    ).eval()
    
    processor = ColQwen2_5_Processor.from_pretrained(MODEL_NAME)
    print(f"[INFO] Model loaded (Flash Attention 2: {use_flash_attn})")

    # Step 3: Encode
    emb_docs = encode_images_with_cache(images, processor, model)
    emb_queries = encode_queries(qtexts, processor, model)

    # Step 4: Compute scores (with efficiency timing)
    start = time.time()
    
    # Use custom scoring function for dynamic resolution
    scores = compute_scores_dynamic(emb_queries, emb_docs, processor)
    
    efficiency_time = time.time() - start
    avg_time = efficiency_time / len(queries)

    print(f"\n⏱️  EFFICIENCY METRICS:")
    print(f"   Total retrieval time: {efficiency_time:.2f} seconds")
    print(f"   Average time per query: {avg_time:.4f} seconds")
    print(f"   Queries per second: {1/avg_time:.2f}")

    # Step 5: Apply filtering
    scores = apply_filtering(scores, queries, doc_names)

    # Step 6: Validate filtering
    validate_filtering(scores, queries, doc_names, num_samples=3)

    # Step 7: Evaluate (K=1,5,10,20)
    print("\n[INFO] Calculating retrieval metrics (K=1,5,10,20)...")
    eval_results = evaluate_retrieval(scores, gt_indices, k_values=[1, 5, 10, 20])

    # Step 8: Print results
    print_evaluation_results(eval_results)
    print_per_query_analysis(eval_results, queries, doc_names, top_n=3)

    # Step 9: Prepare detailed results
    print("\n[INFO] Preparing detailed results...")
    detailed = []
    for qi, q in enumerate(queries):
        ranked = torch.argsort(scores[qi], descending=True).tolist()
        detailed.append({
            "CID": q["CID"],
            "code": q.get("code", ""),
            "topic": q.get("topic", ""),
            "metric": q["metric"],
            "query_text": q["query_text"],
            "num_relevant_pages": len(gt_indices[qi]),
            "ground_truth_pages": [doc_names[i] for i in gt_indices[qi]],
            "top10_predictions": [doc_names[i] for i in ranked[:10]],
            "top10_scores": [float(scores[qi][i]) for i in ranked[:10]],
            "top20_predictions": [doc_names[i] for i in ranked[:20]],
            "top20_scores": [float(scores[qi][i]) for i in ranked[:20]],
            "metrics": eval_results["per_query"][qi]["metrics"]
        })

    # Step 10: Save results
    out = {
        "industry": args.industry,
        "model": MODEL_NAME,
        "evaluation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": eval_results["summary"],
        "efficiency": {
            "total_time_seconds": round(efficiency_time, 4),
            "avg_time_per_query_seconds": round(avg_time, 6),
            "queries_per_second": round(1/avg_time, 2)
        },
        "results": detailed
    }

    out_file = OUT_DIR / f"results_{args.industry}.json"
    out_file.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"\n✅ DONE! Results saved to: {out_file}")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    main()
