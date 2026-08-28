import json
import re
import random
import time
from typing import List, Dict, Tuple
from pathlib import Path
from dataclasses import asdict
from tqdm import tqdm

from .case_formater import Case, generate_case
from .retriever import RetrievalPool
from src.config.config import get_config
from src.statistics.reporter import report, ReportContext
from src.utils.query_assembler import get_prompt
from src.models.visrag import predict

CFG = get_config()


def collect_cases(language: str, use_retrieval: bool) -> Tuple[List[Dict], List[Dict]]:
    annotation_path = Path(CFG.data.root) / 'target' / language / 'annotations'
    test_cases = []
    retrieval_cases = []

    with open(annotation_path / 'test.json', 'r') as f:
        test_cases.extend(json.load(f))
    with open(annotation_path / 'retrieval.json', 'r') as f:
        retrieval_cases.extend(json.load(f))

    if use_retrieval:
        return test_cases, retrieval_cases
    else:
        return test_cases, []


def extract_answer(text: str, tag: str) -> str | None:
    pattern = fr"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def write_back(labels, predictions):
    json_list = [
        {'label': label, 'prediction': p}
        for label, p in zip(labels, predictions)
    ]

    result_path = Path(CFG.statistics.root)
    file_name = time.strftime("%Y-%m-%d_%H%M", time.localtime())
    file_name = f'{file_name}.json'

    with open(result_path / file_name, 'w+', encoding='utf-8') as f:
        json.dump(
            json_list,
            f,
            ensure_ascii=False,
            indent=4
        )


def run(language: str) -> None:
    retriever_type: str = CFG.running.retriever_type
    emb_cache_path: Path = Path(CFG.data.root) / f'target/{language}/{retriever_type}_emb_cache.pt'

    test_cases, retrieval_cases = collect_cases(language, CFG.running.use_retrieval)

    formated_test: List[Case] = [generate_case(language, case) for case in test_cases]
    formated_retrieval: List[Case] = [generate_case(language, case) for case in retrieval_cases]

    retrieval_pool = RetrievalPool(
        base_cases=formated_retrieval,
        cache_path=emb_cache_path,
        ratio=CFG.data.retrieval_ratio,
        type=retriever_type,
    )

    labels = []
    preds = []
    mis_preds = []

    random.shuffle(formated_test)

    if CFG.running.mode == 'debug':
        truncated_len = int(len(formated_test) * 0.05)
        formated_test = formated_test[:truncated_len]

    for case in tqdm(formated_test):
        retrieved: List[Case] = []
        imgs: List[str] = []
        if CFG.running.use_retrieval:
            retrieved = retrieval_pool.retrieve_cases(case)
            imgs = [item.image_path for item in retrieved]

        use_text_input: bool = False
        if CFG.data.input_type == 'text':
            use_text_input = True
        prompt = get_prompt(case, use_text_input, retrieved)

        imgs.append(case.image_path)

        if use_text_input:
            imgs = []

        try:
            output = predict(imgs, prompt)
        except Exception as e:
            print(f'Err: perform prediction failed, {e}')
            continue

        pred_opt: str | None = extract_answer(output, 'answer')
        if pred_opt is None:
            raise RuntimeError(f'Did not extract any answer from output: {output}')

        pred: str = pred_opt

        print(f"prediction finished, label: {case.label} pred: {pred}")
        labels.append(case.label)
        preds.append(pred)

        if pred != case.label:
            mis_case = asdict(case)
            mis_case['pred'] = pred
            mis_preds.append({'case': mis_case, 'output': output})

    write_back(labels, preds)

    report_context = ReportContext(
        language=language,
        config=CFG,
        test_cases=formated_test,
        retrieval_cases=[] if not retrieval_pool else retrieval_pool.get_all_cases(),
        ground_truth=labels,
        preds=preds,
        mis_preds=mis_preds,
    )

    report(report_context)


def main() -> None:
    test_languages = CFG.running.test_languages
    for lang in test_languages:
        run(lang)


if __name__ == '__main__':
    main()
