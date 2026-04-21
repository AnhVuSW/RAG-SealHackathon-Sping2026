#!/usr/bin/env python3
"""
Marketing RAG Agent — Unified Runner
=====================================
Usage:
    python run.py --ingest                            # Ingest marketing data
    python run.py --ui                                # Streamlit web UI
    python run.py --query "ROI TikTok tháng trước?"  # Single query (terminal)
    python run.py                                     # Interactive chat mode
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Cố định encoding UTF-8 để in emoji không bị lỗi trên Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Khởi động Langfuse trước khi import llama-index
try:
    from src.cost_tracking import start_langfuse
    start_langfuse()
except Exception:
    pass


def run_ingest(data_path: str):
    from src.ingestion.pipeline import MarketingIngestionPipeline

    path = Path(data_path)
    if not path.exists():
        print(f"❌ Không tìm thấy thư mục: {data_path}")
        sys.exit(1)

    print(f"\n📂 Ingest data từ: {data_path}")
    pipeline = MarketingIngestionPipeline()
    result = pipeline.ingest(data_path)

    print(f"\n{'='*50}")
    print(f"✅ Ingest thành công!")
    print(f"   Total chunks : {result.total_chunks:,}")
    print(f"   Total docs   : {result.total_docs:,}")
    print(f"   Collections  :")
    for coll, count in result.collections.items():
        print(f"     - {coll}: {count:,}")
    print(f"{'='*50}")


def run_ui():
    import subprocess
    print("🚀 Khởi động Streamlit UI...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "src/ui_streamlit/main.py",
        "--server.headless=false",
        "--server.port=8501",
    ])


def run_query(question: str):
    from src.agent import MarketingAgent
    from src.cost_tracking import CostTracker
    import time

    print(f"\n🤔 Query: {question}")
    print("-" * 50)

    agent = MarketingAgent()
    tracker = CostTracker()

    result = agent.chat(question)
    response = result.get("response", "")
    latency = result.get("latency_ms", 0)

    input_tokens = len(question) // 4
    output_tokens = len(response) // 4
    metrics = tracker.record(question, response, input_tokens, output_tokens, latency)

    print(f"\n📝 Response:\n{response}")
    print(f"\n💰 Chi phí: ${metrics.cost_usd:.6f} | ⏱ {latency} ms | 🪙 ~{input_tokens+output_tokens} tokens")


def run_interactive():
    from src.agent import MarketingAgent
    from src.cost_tracking import CostTracker

    print("\n" + "=" * 55)
    print("  Marketing RAG Agent — Interactive Mode")
    print("  Gõ 'quit' để thoát | 'reset' để xóa memory")
    print("=" * 55)
    print("\nCâu hỏi mẫu:")
    print("  • Tóm tắt lý do KH đánh giá 1 sao tuần qua")
    print("  • ROI chiến dịch TikTok tháng trước bao nhiêu?")
    print("  • Có mã giảm giá nào cho hạng Gold?")
    print("  • Chính sách bồi thường hàng hỏng thế nào?\n")

    agent = MarketingAgent()
    tracker = CostTracker()

    while True:
        try:
            question = input("❯ ").strip()

            if not question:
                continue

            if question.lower() in ["quit", "exit", "q"]:
                print(f"\n📊 Session summary: {tracker.summary()}")
                print("Goodbye!")
                break

            if question.lower() == "reset":
                agent.reset_memory()
                print("✓ Memory đã được reset")
                continue

            result = agent.chat(question)
            response = result.get("response", "")
            latency = result.get("latency_ms", 0)

            input_tokens = len(question) // 4
            output_tokens = len(response) // 4
            metrics = tracker.record(question, response, input_tokens, output_tokens, latency)

            print(f"\n{response}")
            print(f"\n[💰 ${metrics.cost_usd:.6f} | ⏱ {latency}ms | Session total: ${tracker.total_cost_usd:.6f}]\n")

        except KeyboardInterrupt:
            print(f"\n\n📊 Session: {tracker.total_requests} requests, ${tracker.total_cost_usd:.4f}")
            print("Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    from src.config import MARKETING_DATA_PATH

    parser = argparse.ArgumentParser(
        description="Marketing RAG Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py --ingest
  python run.py --ingest --data "C:\\path\\to\\MARKETING_DataSwamp_VN"
  python run.py --ui
  python run.py --query "ROI chiến dịch TikTok?"
  python run.py                    # Interactive mode
        """
    )

    parser.add_argument("--query", "-q", type=str, help="Single query")
    parser.add_argument("--ingest", action="store_true", help="Ingest marketing data")
    parser.add_argument(
        "--data", type=str,
        default=str(MARKETING_DATA_PATH),
        help="Đường dẫn thư mục MARKETING_DataSwamp_VN"
    )
    parser.add_argument("--ui", action="store_true", help="Khởi động Streamlit UI")

    args = parser.parse_args()

    if args.ingest:
        run_ingest(args.data)
    elif args.ui:
        run_ui()
    elif args.query:
        run_query(args.query)
    else:
        run_interactive()


if __name__ == "__main__":
    main()
