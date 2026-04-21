from dataclasses import dataclass


@dataclass
class StreamlitConfig:
    page_title: str = "RAG System"
    page_icon: str = "🔍"
    layout: str = "wide"
    initial_sidebar_state: str = "expanded"
