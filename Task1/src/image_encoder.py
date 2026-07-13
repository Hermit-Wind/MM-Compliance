import torch
from functools import lru_cache
from typing import List, Dict
from pathlib import Path
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info  # pip install qwen-vl-utils
from src.config.config import get_config

CFG = get_config()
CACHE_FILE = Path(CFG.data.root) / 'target' / 'image_emb_cache.pt'

@lru_cache
def get_model():
    model_name = "Qwen/Qwen2.5-VL-3B-Instruct"

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )

    processor = AutoProcessor.from_pretrained(model_name)

    return model, processor

@lru_cache
def load_cache(cache_file: Path) -> Dict[str, torch.Tensor]:
    if cache_file.exists():
        data = torch.load(cache_file)
        return {str(k): v for k, v in data.items()}
    else:
        print(f'Warning: cache file not found in {str(cache_file)}')
        return {}

def save_cache(cache: Dict[str, torch.Tensor], cache_file: Path) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    torch.save(cache, cache_file)

def get_embeddings_with_cache(
        image_path: str,
        cache_file: Path = CACHE_FILE
) -> torch.Tensor:
    cache = load_cache(cache_file)

    image_name = Path(image_path).stem

    if image_name not in cache:
        print(f'Warning: embeddings not found in cache {image_path}')
        emb = encode(image_path).to('cpu')
        cache[image_name] = emb

        save_cache(cache, cache_file)

        return emb
    else:
        return cache[image_name]

def encode(image_path: str) -> torch.Tensor:
    model, processor = get_model()
    image_encoder = model.visual

    image = Image.open(image_path).convert("RGB")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
            ],
        }
    ]

    vision_inputs, _ = process_vision_info(messages)
    inputs = processor(
        text = [""],
        images=vision_inputs,
        videos=None,
        padding=True,
        return_tensors="pt",
    )

    pixel_values = inputs["pixel_values"].to(model.device, dtype=model.dtype)
    grid_thw = inputs["image_grid_thw"].to(model.device)

    with torch.no_grad():
        patch_feats = image_encoder(pixel_values, grid_thw=grid_thw)
        if patch_feats.dim() == 3:
            image_emb = patch_feats.mean(dim=1)      # (B, D)
        else:
            image_emb = patch_feats.mean(dim=0, keepdim=True)  # (1, D)

    return image_emb

