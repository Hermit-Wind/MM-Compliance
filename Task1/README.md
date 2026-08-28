# Task1: ESG Compliance Analysis

## Prerequisites

- Python 3.10+
- GPU with CUDA support (recommended)
- 20GB+ disk space

## Quick Start

### 1. Install Dependencies

```bash
pip install torch transformers vllm scikit-learn matplotlib tqdm pillow qwen-vl-utils tomli
```

### 2. Configure Project

Edit `configs/config.toml`:

```toml
[statistics]
root = '/path/to/your/output/directory'

[running]
test_languages = ['english']  # Select languages to process

[data]
root = '/path/to/your/data/directory'
input_type = 'image'
```

### 3. Prepare Data Directory

Create this directory structure:

```
your_data_directory/
└── target/
    └── english/
        ├── annotations/
        │   ├── test.json
        │   └── retrieval.json       # optional
        └── reports/
            ├── images/
            │   ├── document_page_1.png
            │   ├── document_page_2.png
            │   └── ...
            └── text/
                ├── document_page_1.txt
                ├── document_page_2.txt
                └── ...
```

### 4. Prepare JSON Data

Format for `test.json` and `retrieval.json`:

```json
[
    {
        "cid": "company_id",
        "metric": "ESG metric description",
        "topic": "ESG topic",
        "sid": "SASB_ID",
        "file_stem": "document_page_1",
        "label": "yes"
    }
]
```

**Required fields:**
- `cid`: Company ID
- `metric`: Metric description
- `topic`: Topic name
- `sid`: SASB standard ID
- `file_stem`: Filename stem (without extension)
- `label`: `"yes"`, `"no"`, or `"yes but not complete"`

**File requirements:**
- Images: `.png` format, filename must match `file_stem`
- Text: `.txt` format, filename must match `file_stem`

### 5. Run Pipeline

```bash
# Test with 5% data first (set mode = 'debug' in config.toml)
python -m src.run

# Run full pipeline (set mode = 'production' in config.toml)
python -m src.run
```

### 6. View Results

Results saved in `output_directory/{language}_{input_type}_{timestamp}/`:
- `summary.output` - Classification metrics
- `confusion_matrix.png` - Performance visualization
- `err.json` - Misclassified cases
- `err.output` - Detailed error analysis

## Configuration Reference

| Parameter | Options | Default | Description |
|-----------|---------|---------|-------------|
| `root` (statistics) | path | - | Output directory for results |
| `root` (data) | path | - | Data directory path |
| `use_retrieval` | true/false | true | Enable retrieval system |
| `retriever_type` | 'image'/'text' | 'image' | Embedding type for retrieval |
| `test_languages` | list | ['english'] | Languages to process |
| `mode` | 'production'/'debug' | 'production' | Use 100% or 5% of data |
| `input_type` | 'image'/'text' | 'image' | Process images or text |
| `retrieval_ratio` | 0.0-1.0 | 1.0 | Retrieval set size ratio |

## Data Directory Example

```
my_data/
└── target/
    └── english/
        ├── annotations/
        │   ├── test.json
        │   └── retrieval.json
        └── reports/
            ├── images/
            │   ├── esg-report-2022_008.png
            │   ├── esg-report-2022_009.png
            │   └── esg-report-2022_012.png
            └── text/
                ├── esg-report-2022_008.txt
                ├── esg-report-2022_009.txt
                └── esg-report-2022_012.txt
```

## Code Structure

| Module | Purpose |
|--------|---------|
| `src/run.py` | Main pipeline orchestrator |
| `src/case_formater.py` | Convert JSON to Case objects |
| `src/encoder.py` | Image/text embedding generation |
| `src/retriever.py` | Case retrieval using similarity |
| `src/models/visrag.py` | Model inference (EVisRAG-7B) |
| `src/statistics/reporter.py` | Report generation |

## Advanced Configuration

### Without Retrieval

```toml
[running]
use_retrieval = false
```

### Text-based Analysis

```toml
[running]
retriever_type = 'text'

[data]
input_type = 'text'
```

### Multi-language Processing

```toml
[running]
test_languages = ['english', 'french', 'japanese', 'chinese']
```

## Configuration Template

See `configs/config.example.toml` for annotated configuration with all options.

