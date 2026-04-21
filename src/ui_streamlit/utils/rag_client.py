from src.ingestion import DocumentIngestionPipeline
from src.query_orchestration import QueryPipeline
from src.ranking import RankingPipeline
from src.synthesis import SynthesisPipeline


class RAGClient:
    """Wraps UnifiedPipeline for Streamlit session state."""

    def __init__(self):
        self._initialized = False
        self._query_pipeline = None
        self._ranking_pipeline = None
        self._synthesis_pipeline = None

    def _ensure_init(self):
        if self._initialized:
            return
        self._query_pipeline = QueryPipeline()
        self._ranking_pipeline = RankingPipeline()
        self._synthesis_pipeline = SynthesisPipeline()
        self._initialized = True

    def ingest(self, data_path: str):
        pipeline = DocumentIngestionPipeline()
        return pipeline.ingest(data_path)

    def query(self, question: str) -> dict:
        self._ensure_init()
        docs = self._query_pipeline.process(question)
        ranked = self._ranking_pipeline.process(question, docs)
        response, metadata = self._synthesis_pipeline.synthesize(question, ranked)
        return {
            "response": response,
            "sources": ranked[:5],
            "metadata": metadata,
        }
