import argparse
from .config import RankingConfig
from .pipeline import RankingPipeline


def main():
    parser = argparse.ArgumentParser(description="Layer 3: Ranking & Processing")
    parser.add_argument("--input", type=str, required=True, help="Input results file")
    parser.add_argument("--reranker", type=str, default="cohere", help="Reranker: cohere or bge")
    args = parser.parse_args()

    config = RankingConfig()
    pipeline = RankingPipeline(config)
    print(f"Ranking with {args.reranker} reranker")


if __name__ == "__main__":
    main()
