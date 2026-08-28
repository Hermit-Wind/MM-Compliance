import torch
import torch.nn.functional as F
from pathlib import Path
from torch import Tensor
from typing import List
from .case_formater import Case
import src.encoder as encoder

device: torch.device = torch.device('cuda')


class RetrievalPool():

    @classmethod
    def divide_by_label(cls, cases: List[Case]):
        groups = {}
        for case in cases:
            groups.setdefault(case.label, []).append(case)

        return groups

    @classmethod
    def divide_by_company(cls, cases: List[Case]):
        groups = {}
        for case in cases:
            groups.setdefault(case.company, []).append(case)

        return groups

    @classmethod
    def extract_by_ratio(cls, cases: List[Case], ratio: float) -> List[Case]:
        results: List[Case] = []

        company_groups = RetrievalPool.divide_by_company(cases)

        for sublist in company_groups.values():
            label_groups = RetrievalPool.divide_by_label(sublist)
            for item in label_groups.values():
                split_point: int = int(len(item) * ratio)
                if not split_point and len(item):
                    split_point = 1
                results.extend(item[:split_point])

        return results

    def __init__(self, base_cases: List[Case], cache_path: Path, ratio: float | None, type: str = 'image') -> None:
        self.base = base_cases
        self.retriever_type = type
        if ratio:
            truncated_base: List[Case] = RetrievalPool.extract_by_ratio(base_cases, ratio)
            self.case_shards = list(RetrievalPool.divide_by_label(truncated_base).values())
        else:
            self.case_shards = list(RetrievalPool.divide_by_label(self.base).values())
        self.cache_path = cache_path

        for shard in self.case_shards:
            print(f'label: {shard[0].label}, length: {len(shard)}')

    def retrieve_first(self, candidates: List[Case], emb: Tensor) -> Case:
        expanded_emb = emb.expand(len(candidates), -1)

        if self.retriever_type == 'image':
            candidate_embs = [
                encoder.get_embedding_with_cache(
                    case.image_path,
                    self.cache_path,
                    encoder.ENCODER_IMAGE).to(device) for case in candidates]
        elif self.retriever_type == 'text':
            candidate_embs = [
                encoder.get_embedding_with_cache(
                    case.text_path,
                    self.cache_path,
                    encoder.ENCODER_TEXT).to(device) for case in candidates]
        else:
            raise ValueError(f'Unsupported retriever type: {self.retriever_type}')

        candidate_embs = torch.stack(candidate_embs, dim=0)
        candidate_embs = candidate_embs.squeeze(1)

        sim = F.cosine_similarity(candidate_embs, expanded_emb, dim=1)
        index = int(torch.argmax(sim))

        return candidates[index]

    def retrieve_cases(self, query: Case) -> List[Case]:
        if self.retriever_type == 'image':
            emb = encoder.get_embedding_with_cache(query.image_path, self.cache_path, encoder.ENCODER_IMAGE).to(device)
        elif self.retriever_type == 'text':
            emb = encoder.get_embedding_with_cache(query.text_path, self.cache_path, encoder.ENCODER_TEXT).to(device)
        else:
            raise ValueError(f'Unsupported retriever type: {self.retriever_type}')

        results = [self.retrieve_first(item, emb) for item in self.case_shards]

        return results

    def get_all_cases(self) -> List[Case]:
        all_cases = [item for shard in self.case_shards for item in shard]
        return all_cases
