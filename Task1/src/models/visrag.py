from transformers import AutoProcessor
from vllm import LLM, SamplingParams
from qwen_vl_utils import process_vision_info

def get_model():
    if hasattr(get_model, '_model'):
        return get_model._model

    model_path = "Boggy666/EVisRAG-7B"
    processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True, padding_side='left')
    llm = LLM(
        model=model_path,
        tensor_parallel_size=1,
        gpu_memory_utilization = 0.7,
        dtype="bfloat16",
        limit_mm_per_prompt={"image":5, "video":0},
    )

    get_model._model = (llm, processor)

    return (llm, processor)

def predict(imgs, prompt):
    sampling_params = SamplingParams(
        temperature=0.1,
        repetition_penalty=1.05,
        max_tokens=4096,
    )

    content = [{"type": "text", "text": prompt}]
    for img in imgs:
        content.append({
            "type": "image",
            "image": img
        })

    msg = [{
        "role": "user",
        "content": content,
    }]

    llm, processor = get_model()

    prompt = processor.apply_chat_template(
        msg,
        tokenize=False,
        add_generation_prompt=True,
    )

    if imgs:
        image_inputs, _ = process_vision_info(msg)

        msg_input = [{
            "prompt": prompt,
            "multi_modal_data": {"image": image_inputs},
        }]

        output_texts = llm.generate(msg_input,
            sampling_params=sampling_params,
        )

        return output_texts[0].outputs[0].text
    else:
        msg_input = [{
            "prompt": prompt,
        }]

        output_texts = llm.generate(msg_input,
            sampling_params=sampling_params,
        )

        return output_texts[0].outputs[0].text



