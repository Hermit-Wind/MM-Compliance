from typing import List, Tuple
from .case_formater import Case
from functools import wraps
import random

def devide_by_label(cases: List[Case]) -> List[List[Case]]:
    results = []
    labels = set([item.label for item in cases])
    for label in labels:
        results.append([item for item in cases if item.label == label])

    return results

def split_validator(bias: float):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            while(True):
                test_pool, pools = func(*args, **kwargs)
                # Different cases may share same image, in order to avoid data leakage
                # We have to devide the dataset based on image_path instead of cases
                # If the difference between the actual data split ratio and the expected ratio
                # exceeds `bias`, reject the current split result and rerun the splitting process.
                test_length = len(test_pool)
                retrieval_length = sum([len(item) for item in pools])

                actual_ratio = retrieval_length / (retrieval_length + test_length)

                expected_ratio = args[1]
                if abs(actual_ratio - expected_ratio) / expected_ratio <= bias:
                    return test_pool, pools
                else:
                    print(f'err: bias exceeds {bias}, actual ratio: {actual_ratio}')
        return inner
    return wrapper

@split_validator(0.1)
def split(
    cases: List[Case],
    ratio: float,
) -> Tuple[List[Case], List[List[Case]]]:

    distinct_image_paths: List[str] = list(set([item.image_path for item in cases]))
    split_point: int = int(len(distinct_image_paths) * ratio)

    random.shuffle(distinct_image_paths)

    retrieval_images: List[str] = distinct_image_paths[:split_point]
    test_images: List[str] = distinct_image_paths[split_point:]

    test_pool: List[Case] = [
        item
        for item in cases
        if item.image_path in test_images
    ]

    retrieval_pool: List[Case] = [
        item
        for item in cases
        if item.image_path in retrieval_images
    ]

    pools = devide_by_label(retrieval_pool)

    return test_pool, pools
