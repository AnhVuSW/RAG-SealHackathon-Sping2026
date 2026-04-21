import streamlit as st


def render_sources(sources: list[dict]):
    if not sources:
        return
    with st.expander("Sources", expanded=False):
        for i, src in enumerate(sources, 1):
            score = src.get("score", 0)
            text = src.get("text", "")[:200]
            st.markdown(f"**{i}.** [{score:.2f}] {text}...")
