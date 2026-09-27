import streamlit as st
import google.generativeai as genai

st.title("Meu App de IA")

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

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

    resposta = model.generate_content(pergunta)
    texto_resposta = resposta.text

    st.session_state.mensagens.append({"role": "assistant", "content": texto_resposta})
    with st.chat_message("assistant"):
        st.write(texto_resposta)
