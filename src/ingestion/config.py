from dataclasses import dataclass
import torch


@dataclass
class IngestionConfig:
    chunk_size: int = 512
    chunk_overlap: int = 50
    embedding_model: str = "BAAI/bge-m3"           # multilingual, hỗ trợ tiếng Việt
    embedding_device: str = "cuda" if torch.cuda.is_available() else "cpu"
    lancedb_uri: str = "./data/lancedb"
    lancedb_table: str = "documents"
    batch_size: int = 100
    num_workers: int = 4
