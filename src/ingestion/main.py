import argparse
from .config import IngestionConfig
from .pipeline import DocumentIngestionPipeline


def main():
    parser = argparse.ArgumentParser(description="Layer 1: Document Ingestion")
    parser.add_argument("--source", type=str, required=True, help="Source directory or URL")
    parser.add_argument("--db", type=str, default="./data/lancedb", help="LanceDB path")
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--overlap", type=int, default=50)
    args = parser.parse_args()

    config = IngestionConfig(
        chunk_size=args.chunk_size,
        chunk_overlap=args.overlap,
        lancedb_uri=args.db,
    )
    pipeline = DocumentIngestionPipeline(config)
    result = pipeline.ingest(args.source)
    print(f"Ingested {result.total_chunks} chunks from {result.total_docs} documents")


if __name__ == "__main__":
    main()
