def render_user_message(message: str):
    import streamlit as st
    st.chat_message("user").write(message)


def render_assistant_message(message: str):
    import streamlit as st
    st.chat_message("assistant").write(message)
