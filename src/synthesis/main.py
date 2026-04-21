import argparse
from .config import SynthesisConfig
from .pipeline import SynthesisPipeline


def main():
    parser = argparse.ArgumentParser(description="Layer 4: Synthesis & Memory")
    parser.add_argument("--session-id", type=str, default="default", help="Session ID")
    args = parser.parse_args()

    config = SynthesisConfig()
    pipeline = SynthesisPipeline(config)
    print(f"Synthesis pipeline initialized for session: {args.session_id}")


if __name__ == "__main__":
    main()
