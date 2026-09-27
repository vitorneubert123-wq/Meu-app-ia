
import streamlit as st
from google import genai

# Configuração da página
st.set_page_config(
    page_title="Serjão Pururucas",
    page_icon="🍊",
    layout="centered"
)

# Estilo laranja
st.markdown("""
<style>
    .stApp {
        background-color: #111111;
    }

    h1 {
        color: #ff7900 !important;
    }

    .stChatMessage {
        border-radius: 15px;
    }

    [data-testid="stChatInput"] {
        border: 2px solid #ff7900;
        border-radius: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Título
st.title("🍊 Serjão Pururucas")
st.caption("Sua IA meio doida, mas que tenta ajudar.")

# API
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("A chave GOOGLE_API_KEY não está configurada.")
    st.stop()

client = genai.Client(
    api_key=st.secrets["GOOGLE_API_KEY"]
)

# Personalidade do Serjão
INSTRUCAO = """
Você é o Serjão Pururucas, uma inteligência artificial engraçada,
amigável e inteligente.

Sua personalidade:
- Fale em português do Brasil.
- Seja engraçado quando fizer sentido.
- Faça algumas brincadeiras leves.
- Não exagere nas piadas.
- Ajude o usuário de verdade.
- Explique as coisas de forma simples.
- Nunca diga que você é o Gemini.
- Se perguntarem seu nome, responda que você é o Serjão Pururucas.
- Você pode usar emojis ocasionalmente.
- Não invente informações quando não souber algo.
"""

# Histórico
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat
pergunta = st.chat_input("Fala aí, manda sua pergunta...")

if pergunta:
    st.session_state.mensagens.append({
        "role": "user",
        "content": pergunta
    })

    with st.chat_message("user"):
        st.write(pergunta)

    prompt = INSTRUCAO + "\n\nMensagem do usuário:\n" + pergunta

    resposta = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )

    texto_resposta = resposta.text

    st.session_state.mensagens.append({
        "role": "assistant",
        "content": texto_resposta
    })

    with st.chat_message("assistant"):
        st.write(texto_resposta)
