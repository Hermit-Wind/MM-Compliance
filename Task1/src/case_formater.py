from dataclasses import dataclass
from pathlib import Path
from src.config.config import get_config

CFG = get_config()


@dataclass
class Case():
    company: str
    metric: str
    topic: str
    image_path: str
    text_path: str
    label: str
    sid: str


def generate_case(language: str, raw_dict: dict) -> Case:
    if not raw_dict:
        raise ValueError('raw_dict is null')

    image_root: Path = Path(CFG.data.root) / 'target' / language / 'reports' / 'images'
    image_path: Path = image_root / f'{raw_dict["file_stem"]}.png'

    text_root: Path = Path(CFG.data.root) / 'target' / language / 'reports' / 'text'
    text_path: Path = text_root / f'{raw_dict["file_stem"]}.txt'

    sid = raw_dict.get('sid', None)
    if sid is not None:
        sid = str(sid)
    else:
        print(f'No SASB info in {language} data, for case {raw_dict}')
        raise ValueError('No SASB specialized.')

    case = Case(
        company=raw_dict['cid'],
        metric=raw_dict['metric'],
        topic=raw_dict['topic'],
        label=raw_dict['label'],
        image_path=str(image_path.resolve()),
        text_path=str(text_path.resolve()),
        sid=sid,
    )

    return case
