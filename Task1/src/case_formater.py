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

    ############################## 
    #new_old_cid_mapping = {
    #    "06-21_gb-_lvmh_rse2022": "lvmh",
    #    "2022-baytex-esg-report-final": "baytex",
    #    "burberry_2020-21_esg": "burberry",
    #    "cannickel-esg-report2023-print": "canadanickel",
    #    "kering_sustainability_progress_report_2020_2023_7d06687606": "kering",
    #    "esg-2022": "greenergy",
    #    "esg-report-2022": "arabbank",
    #    "esg-report-2022-final_ada": "usbank",
    #    "esgreport2022": "standardbank",
    #}

    #file_stem = raw_dict['file_stem']
    #page = file_stem.rsplit("_", 1)[1]
    #cid = raw_dict['cid']
    #raw_dict['file_stem'] = f'{new_old_cid_mapping[cid]}_{page}'
    ############################## 


    image_root: Path = Path(CFG.data.root) / 'target' / language / 'reports' / 'images'
    image_path: Path = image_root / f'{raw_dict["file_stem"]}.png'

    text_root: Path = Path(CFG.data.root) / 'target' / language / 'reports' / 'text'
    text_path: Path = text_root / f'{raw_dict["file_stem"]}.txt'

    sid = raw_dict.get('sid', None)
    if sid != None:
        sid = str(sid)
    else:
        print(f'No SASB info in {language} data, for case {raw_dict}')
        raise ValueError('No SASB specialized.')

    case = Case(
        company = raw_dict['cid'],
        metric = raw_dict['metric'],
        topic = raw_dict['topic'],
        label = raw_dict['label'],
        image_path = str(image_path.resolve()),
        text_path = str(text_path.resolve()),
        sid = sid,
    )

    return case

