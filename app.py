
import streamlit as st
from google import genai

st.title("Meu App de IA")

# Verifica se a chave está realmente chegando ao aplicativo
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("A chave GOOGLE_API_KEY não está disponível nos Secrets do Streamlit.")
    st.stop()

client = genai.Client(
    api_key=st.secrets["GOOGLE_API_KEY"]
)

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

pergunta = st.chat_input("Digite sua mensagem...")

if pergunta:
    st.session_state.mensagens.append({
        "role": "user",
        "content": pergunta
    })

    with st.chat_message("user"):
        st.write(pergunta)

    resposta = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=pergunta
    )

    texto_resposta = resposta.text

    st.session_state.mensagens.append({
        "role": "assistant",
        "content": texto_resposta
    })

    with st.chat_message("assistant"):
        st.write(texto_resposta)
