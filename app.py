import streamlit as st
from anthropic import Anthropic

st.title("Meu App de IA")

client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

pergunta = st.chat_input("Digite sua mensagem...")

if pergunta:
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.write(pergunta)

    resposta = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=st.session_state.mensagens
    )
    texto_resposta = resposta.content[0].text

    st.session_state.mensagens.append({"role": "assistant", "content": texto_resposta})
    with st.chat_message("assistant"):
        st.write(texto_resposta)
