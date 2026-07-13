# Task 2: Metric-to-Page Evidence Retrieval

Code for Task 2 of MM-Compliance.

Given a SASB metric description as a query and a target ESG report, the
system ranks the pages within that report to identify the page(s) containing
relevant disclosure evidence. Retrieval is restricted to pages from the same
report (document-boundary retrieval).

The code supports six languages: English, French, Chinese, Japanese,
Korean, and Thai.

**Model:** ColQwen2.5 (`vidore/colqwen2.5-v0.2`)

ColPali (`vidore/colpali-v1.2-hf`) is included only for the English
baseline comparison.

## Workflow

The language-specific scripts cover the following workflow:

1. `pdf_to_images_*.py`  
   Render report PDFs into page images.

2. `build_queries_*.py`  
   Construct SASB metric queries from the annotation files.

3. `split_queries_by_company_*.py`  
   Organize queries by company/report.

4. `run_colqwen_retrieval_eval_*.py`  
   Run ColQwen2.5 retrieval within each report and evaluate retrieval
   performance.

5. `split_results_by_company_*.py` and `aggregate_by_metric_*.py`  
   Organize retrieval outputs and aggregate evaluation scores by metric.

The evaluation scripts compute F1@K and Hit@K for
K = 1, 5, 10, and 20. Some scripts additionally output nDCG@K,
Recall@K, and Precision@K.

## Data

This repository contains code only.

The annotations, query files, source PDFs, and rendered page images are
not included. Page images can be generated from the source reports using
the corresponding `pdf_to_images_*.py` scripts.


## Requirements

- torch
- transformers
- colpali-engine
- pdf2image
- Pillow
- numpy
- tqdm

The `pdf2image` package requires Poppler to be installed separately.
