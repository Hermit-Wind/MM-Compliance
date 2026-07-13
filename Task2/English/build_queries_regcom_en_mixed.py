# build_queries_regcom_en_mixed.py
"""
Build query files from RegCom_Trainset_EN.json (mixed complete: true + false)

Rules:
  - One query = (CID, Code, Metric)
  - Merge all pages of the same metric in the same PDF into relevant_docs
  - query_text == metric
  - Keep industry
  - Include both complete == true and complete == false
  - Do NOT use query_id (use code as implicit identifier)
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IN_JSON = BASE_DIR / "RegCom_Trainset_EN.json"
OUT_DIR = BASE_DIR / "queries_regcom_mixed"  # <<< changed output folder

TARGET_INDUSTRIES = ["Luxury", "Finance", "Energy"]


def normalize_space(s: str) -> str:
    """Normalize spaces and handle None safely"""
    if s is None:
        return ""
    return " ".join(str(s).split())


def page_to_image(cid: str, page: str):
    """Convert page number to standardized image name"""
    try:
        p = int(page)
    except Exception:
        return None
    stem = Path(cid).stem
    return f"{stem}_p{p:03d}.png"


def main():
    if not IN_JSON.exists():
        raise FileNotFoundError(IN_JSON)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    data = json.loads(IN_JSON.read_text(encoding="utf-8"))

    # industry -> {(cid, code, metric): item}
    groups = {ind: {} for ind in TARGET_INDUSTRIES}

    for row in data:
        # --- 1. 行业过滤 ---
        industry = row.get("Industry")
        if industry not in TARGET_INDUSTRIES:
            continue

        # --- 2. 不剔除 incomplete 样本（complete: true/false 混合） ---
        # 以前这里是：
        # if not row.get("Complete", True):
        #     continue
        # 现在保留所有样本（complete == True / False 均包含）
        # （若要以后恢复过滤，只需取消上方注释即可）

        # --- 3. 提取字段 ---
        cid = row.get("CID")
        code = normalize_space(row.get("Code"))
        topic = normalize_space(row.get("Topic"))
        metric = normalize_space(row.get("Metric"))
        page = row.get("Page")

        # --- 4. 基本字段检查 ---
        if not cid or not code or not metric or not page:
            continue

        img = page_to_image(cid, page)
        if img is None:
            continue

        # --- 5. 按 (CID, Code, Metric) 聚合 ---
        key = (cid, code, metric)

        if key not in groups[industry]:
            groups[industry][key] = {
                "CID": cid,
                "industry": industry,
                "code": code,
                "topic": topic,
                "metric": metric,
                "query_text": metric,
                "relevant_docs": [],
                # 可选保留 Complete 信息（用于后续统计或分析）
                "complete_flag": row.get("Complete", None)
            }

        if img not in groups[industry][key]["relevant_docs"]:
            groups[industry][key]["relevant_docs"].append(img)

    # --- 6. 输出到 JSON ---
    for industry in TARGET_INDUSTRIES:
        queries = list(groups[industry].values())

        out_file = OUT_DIR / f"queries_{industry.lower()}.json"
        out_file.write_text(
            json.dumps({"queries": queries}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        print(f"[DONE] {industry}: {len(queries)} queries")

    print("Saved to:", OUT_DIR)


if __name__ == "__main__":
    main()
