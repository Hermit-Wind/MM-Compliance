import torch
from functools import lru_cache
from typing import List, Dict
from pathlib import Path
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, Qwen2_5_VLModel
from tqdm import tqdm
from qwen_vl_utils import process_vision_info  # pip install qwen-vl-utils
from src.config.config import get_config

ENCODER_IMAGE = 'image'
ENCODER_TEXT = 'text'

@lru_cache
def get_text_model():
    model_name = "Qwen/Qwen2.5-VL-3B-Instruct"

    model = Qwen2_5_VLModel.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    model.eval()

    processor = AutoProcessor.from_pretrained(model_name)

    return model, processor

@lru_cache
def get_image_model():
    model_name = "Qwen/Qwen2.5-VL-3B-Instruct"

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    model.eval()

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

def encode_image(image_path: str) -> torch.Tensor:
    model, processor = get_image_model()
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


def encode_text(text_path: str) -> torch.Tensor:
    model, processor = get_text_model()

    lines = []
    with open(text_path, 'r', encoding = 'utf-8') as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                lines.append(stripped)

    text = '\n'.join(lines) if lines else ""

    if not text.strip():
        return torch.zeros(model.config.hidden_size, device = model.device)

    text_input = processor(
        text = [text],
        return_tensors = 'pt',
        padding = True,
        truncation = True,
        videos = None,
    )

    text_input = {k: v.to(model.device) for k, v in text_input.items()}

    with torch.no_grad():
        outputs = model(**text_input)
        last_hidden_state = outputs.last_hidden_state

    attention_mask = text_input['attention_mask']
    mask = attention_mask.unsqueeze(-1)

    masked_embs = last_hidden_state * mask
    sum_embs = masked_embs.sum(dim = 1)

    lengths = mask.sum(dim = 1)
    lengths = torch.clamp(lengths, min = 1)
    sentence_embs = sum_embs / lengths

    sentence_embs = torch.nn.functional.normalize(
        sentence_embs, p = 2, dim = 1
    )

    return sentence_embs[0]


def get_embedding_with_cache(
    file_path: str,
    cache_file: Path,
    encoder_type: str
):
    cache = load_cache(cache_file)
    cache_key = Path(file_path).stem

    if cache_key in cache and 'kbank' not in cache_key:
        return cache[cache_key]
    else:
        if encoder_type == ENCODER_IMAGE:
            emb = encode_image(file_path)
        elif encoder_type == ENCODER_TEXT:
            emb = encode_text(file_path)
            ...
        else:
            raise ValueError(f'Unsupported encoder type: {encoder_type}')
        cache[cache_key] = emb
        save_cache(cache, cache_file)
        return emb

def main():
    languages = [
        "english",
        "french",
        "japanese",
        "chinese",
        "korean",
        "thai",
    ]

    for language in languages:
        image_root = Path(f'Your_Image_Path/{language}/reports/images/')

        images = [image for image in image_root.rglob('*.png')]

        for image in tqdm(images):
            get_embedding_with_cache(
                str(image.resolve()),
                Path(f'Your_Output_Path/{language}/image_emb_cache.pt'),
                ENCODER_IMAGE,
            )

if __name__ == '__main__':
    main()
