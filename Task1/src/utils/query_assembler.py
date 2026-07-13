from src.case_formater import Case
from typing import List

def assemble_prompt(query: str, few_shot: str, use_text_input: bool):
    image_step1_instruction: str = """Step 1: Observe the Images
First, analyze the question and consider what types of images may contain relevant information.
Then, examine each image one by one, paying special attention to aspects related to the question.
Identify whether each image contains any potentially relevant information.
Wrap your observations within <observe></observe> tags."""

    image_step2_instruction: str = """Step 2: Record Evidences from Images
After reviewing all images, record the evidence you find for each image within <evidence></evidence> tags.
If you are certain that an image contains no relevant information, record it as: [i]: no relevant information(where i denotes the index of the image).
If an image contains relevant evidence, record it as: [j]: [the evidence you find for the question](where j is the index of the image)."""

    image_step3_instruction: str = """Step 3: Reason Based on the Question and Evidences
Based on the recorded evidences, reason about the answer to the question.
Include your step-by-step reasoning within <think></think> tags."""

    image_step4_instruction: str = """Step 4: Answer the Question
Provide your final answer based only on the evidences you found in the images.
Wrap your answer within <answer></answer> tags.
Avoid adding unnecessary contents in your final answer, like if the question is a yes/no question, simply answer "yes" or "no".
Additionally, if the task is a multi-class classification task, you must make sure your answer uses one of all possible options.For example, for a 3-class problem with options yes / yes but not complete / no, you should answer exactly one of: "yes", "yes but not complete", or "no"."""

    text_step1_instruction: str = """Step 1: Observe the OCR text
First, analyze the question and consider what types of text may contain relevant information.
Then, examine text, paying special attention to aspects related to the question.
Identify whether each text contains any potentially relevant information.
Wrap your observations within <observe></observe> tags."""

    text_step2_instruction: str = """Step 2: Record Evidences from OCR text
After reviewing OCR text, record the evidence you find for text within <evidence></evidence> tags.
If you are certain that an text contains no relevant information, record it as: no relevant information.
If text contains relevant evidence, record it as: [the evidence you find for the question]."""

    text_step3_instruction: str = """Step 3: Reason Based on the Question and Evidences
Based on the recorded evidences, reason about the answer to the question.
Include your step-by-step reasoning within <think></think> tags."""

    text_step4_instruction: str = """Step 4: Answer the Question
Provide your final answer based only on the evidences you found in the OCR text.
Wrap your answer within <answer></answer> tags.
Avoid adding unnecessary contents in your final answer, like if the question is a yes/no question, simply answer "yes" or "no".
Additionally, if the task is a multi-class classification task, you must make sure your answer uses one of all possible options.For example, for a 3-class problem with options yes / yes but not complete / no, you should answer exactly one of: "yes", "yes but not complete", or "no"."""

    image_prompt: str = f"""You are an AI Visual QA assistant. I will provide you with a question and several images. Please follow the four steps below:
{image_step1_instruction}

{image_step2_instruction}

{image_step3_instruction}

{image_step4_instruction}

Formatting Requirements:
Use the exact tags <observe>, <evidence>, <think>, and <answer> for structured output.
It is possible that none, one, or several images contain relevant evidence."""

    text_prompt: str = f"""You are an AI Visual QA assistant. I will provide you with a question and several images. Please follow the four steps below:
{text_step1_instruction}

{text_step2_instruction}

{text_step3_instruction}

{text_step4_instruction}

Formatting Requirements:
Use the exact tags <observe>, <evidence>, <think>, and <answer> for structured output."""

    fewshots = f"""First, there will be some examples for you to understand the task, you can answer the question based on given examples
Examples:
{few_shot}"""

    question = f"""Question and images are provided below. Please follow the steps as instructed.
Question:
{query}"""

    prompt: str = image_prompt
    if use_text_input:
        prompt = text_prompt

    if few_shot:
        prompt = f"""{prompt}

{fewshots}"""

    prompt = f"""{prompt}

{question}"""

    return prompt


def assemble_query(case: Case, use_text_input: bool) -> str:
    topic = case.topic
    metric = case.metric

    lines: List[str] = []
    with open(case.text_path, 'r', encoding = 'utf-8') as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                lines.append(stripped)

    ocr_text = '\n'.join(lines)

    ocr_text_prompt: str = f"""Here is the text contents extracted from specific document page.

[OCR text]
{ocr_text}
<EOF>"""

    text_query_body: str = f"""Below, after the 'Topic' and 'Metric' is the topic of information, also, metric that may occured in document.
You should judge whether the mentioned topic, metric and corresponding value occured in the document provided or not.
There is no image information, you should answer the question based only on the ocr text provided above.
The answer should be "yes", "yes but not complete" or "no".

[Topic]
{topic}

[Metric]
{metric}
"""

    image_query_body: str = f"""Below, after the 'Topic' and 'Metric' is the topic of information, also, metric that may occured in document.
You should judge whether the mentioned topic, metric and corresponding value occured in the document provided or not.
The answer should be "yes", "yes but not complete" or "no".

[Topic]
{topic}

[Metric]
{metric}
"""

    if use_text_input:
        return f"""{ocr_text_prompt}

{text_query_body}"""
    else:
        return image_query_body

def genereate_few_shots(cases: List[Case], use_text_input: bool) -> str:
    result = ""

    for i, case in enumerate(cases, start = 1):
        query = assemble_query(case, use_text_input)
        result += f"""[Example {i}]
{query}
<answer>{case.label}</answer>
"""

    result += """===== End of Examples =====

Now solve the following question.
Question and images are provided below...
"""

    return result

def get_prompt(case: Case, use_text_input: bool, examples: List[Case] = []) -> str:
    query = assemble_query(case, use_text_input)
    few_shots = genereate_few_shots(examples, use_text_input) if examples else ""
    prompt = assemble_prompt(query, few_shots, use_text_input)

    return prompt

