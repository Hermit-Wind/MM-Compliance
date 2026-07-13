import tomli
from dataclasses import dataclass
from typing import List
from functools import lru_cache
from pathlib import Path

CONFIG_PATH = Path(__file__).parents[2] / 'configs' / 'config.toml'

@dataclass
class Statistics:
    root: str

@dataclass
class Running:
    use_retrieval: bool
    test_languages: List[str]
    mode: str
    retriever_type: str

@dataclass
class Data:
    root: str
    retrieval_ratio: float
    input_type: str

@dataclass
class Model:
    inference_model: str
    image_encoder: str

@dataclass
class Config:
    statistics: Statistics
    running: Running
    data: Data
    model: Model

@lru_cache(maxsize = 1)
def get_config():
    with open(CONFIG_PATH, 'rb') as f:
        config = tomli.load(f)

    statistics = Statistics(
        config['statistics']['root'],
    )

    running = Running(
        use_retrieval = config['running']['use_retrieval'],
        test_languages = config['running']['test_languages'],
        mode = config['running']['mode'],
        retriever_type = config['running']['retriever_type'],
    )

    data = Data(
        root = config['data']['root'],
        retrieval_ratio = config['data']['retrieval_ratio'],
        input_type = config['data']['input_type']
    )

    model = Model(
        inference_model = config['model']['inference_model'],
        image_encoder = config['model']['image_encoder'],
    )

    cfg = Config(
        statistics = statistics,
        running = running,
        data = data,
        model = model,
    )

    return cfg
