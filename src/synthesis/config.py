from dataclasses import dataclass


@dataclass
class SynthesisConfig:
    compact_max_tokens: int = 4096
    dream_interval_minutes: int = 30
    llm_model: str = "gpt-4o"
