import argparse
from .config import QueryOrchestrationConfig
from .pipeline import QueryPipeline


def main():
    parser = argparse.ArgumentParser(description="Layer 2: Query Orchestration")
    parser.add_argument("--query", type=str, required=True, help="Query string")
    parser.add_argument("--test-mode", action="store_true", help="Test with mock data")
    args = parser.parse_args()

    config = QueryOrchestrationConfig()
    pipeline = QueryPipeline(config)
    results = pipeline.process(args.query)
    print(f"Retrieved {len(results)} documents")


if __name__ == "__main__":
    main()
