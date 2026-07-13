import json
import time
from typing import List, Dict
from pathlib import Path
from dataclasses import dataclass
import matplotlib.pyplot as plt
from sklearn.metrics import (
    confusion_matrix,
    ConfusionMatrixDisplay,
    classification_report,
)

from src.config.config import Config
from src.case_formater import Case

@dataclass
class ReportContext():
    language: str
    config: Config
    test_cases: List[Case]
    retrieval_cases: List[Case]
    ground_truth: List[str]
    preds: List[str]
    mis_preds: List[Dict]

def generate_report_name(context: ReportContext) -> str:
    current = time.localtime()
    time_str: str = time.strftime('%Y-%m-%d_%H%M', current)

    use_retrieval: bool = context.config.running.use_retrieval
    retrieval_type: str = context.config.running.retriever_type
    input_type: str = context.config.data.input_type

    file_name: str = f'{context.language}_{input_type}'
    if use_retrieval:
        file_name += f'_retrieval_{retrieval_type}'
    file_name += f'_{time_str}'
    return file_name

def generate_summary(config: Config) -> str:
    languages = ",".join(config.running.test_languages)
    use_retrieval = config.running.use_retrieval
    retrieval_ratio: float | str = config.data.retrieval_ratio if use_retrieval else '-'

    retrieval_strategy: str = 'mix' if use_retrieval else '-'

    summary = f"""
Test languages: {languages}
Use retrieval: {use_retrieval}
Retrieval strategy: {retrieval_strategy}
Retrieval ratio: {retrieval_ratio}
"""

    return summary

def report_data_distribution(cases: List[Case]) -> str:
    label_counts: Dict[str, int] = {}

    for item in cases:
        label_counts.setdefault(item.label, 0)
        label_counts[item.label] += 1

    total: int = len(cases)

    keys = label_counts.keys()
    cols = []

    for key in keys:
        value_str = f"{label_counts[key]}({float(label_counts[key]) / total:2.2%})"
        width = max(len(str(key)), len(value_str))
        cols.append((str(key), value_str, width))

    label_line: str = "\t".join(f"{k:<{w}}" for k, _, w in cols)
    data_line: str = "\t".join(f"{v:<{w}}" for _, v, w in cols)

    distribution = f"""
{label_line}
{data_line}
"""
    return distribution

def draw_confusion(report_path: Path, trues: List[str], preds: List[str]) -> None:
    labels = list(set(trues + preds)).sort()

    cm = confusion_matrix(trues, preds, labels = labels)
    fig, ax = plt.subplots(figsize = (15, 15))

    disp = ConfusionMatrixDisplay(
        confusion_matrix = cm,
        display_labels = labels
    )

    disp.plot(
        ax = ax,
        cmap = 'Blues',
        colorbar = True,
        values_format = "d"
    )

    ax.set_xlabel('prediction', fontsize = 18)
    ax.set_ylabel('ground truth', fontsize = 18)
    ax.tick_params(axis="x", labelsize=18)
    ax.tick_params(axis="y", labelsize=18)

    for t in disp.text_.ravel():
        t.set_fontsize(20)

    plt.tight_layout()
    plt.savefig(report_path / 'confusion_matrix.png')

def write_summary(
    config: Config,
    report_path: Path,
    tests: List[Case],
    retrieval: List[Case],
    trues: List[str],
    preds: List[str],
) -> None:
    test_distribution: str = report_data_distribution(tests)
    retrieval_distribution: str = report_data_distribution(retrieval)
    summary = generate_summary(config)
    metrics: str = classification_report(trues, preds)

    report: str = f"""
Summary:
{summary}

Test Data Distribution:
{test_distribution}

Retrieval Data Distribution:
{retrieval_distribution}

Results:
{metrics}
"""

    with open(report_path / 'summary.output', 'w+', encoding = 'utf-8') as f:
        f.write(report)

def report_error(report_path: Path, mis_preds: List[Dict]) -> None:
    mis_cases = [item['case'] for item in mis_preds]
    output = [item['output'] for item in mis_preds]
    with open(report_path / 'err.json', 'w') as f:
        json.dump(mis_cases, f, indent = 4, ensure_ascii = False)

    with open(report_path / 'err.output', 'w') as f:
        for item in output:
            f.write('-------------------------------------\n')
            f.write(item)
            f.write('\n')

# Report Contents
# Test language
# Use retrieval
# Retrieval Strategy
# Test data distribution
# Knowlege base data distribution
def report(
    context: ReportContext,
) -> None:
    config = context.config
    report_path: Path = Path(context.config.statistics.root)
    report_name: str = generate_report_name(context)
    report_path = report_path / report_name
    report_path.mkdir(parents = True, exist_ok = True)

    write_summary(
        config,
        report_path,
        context.test_cases,
        context.retrieval_cases,
        context.ground_truth,
        context.preds,
    )

    draw_confusion(report_path, context.ground_truth, context.preds)
    report_error(report_path, context.mis_preds)

def main() -> None:
    ...

if __name__ == '__main__':
    main()
