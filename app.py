import streamlit as st
from google import genai
from google.genai import types
import time
import json
import re
from datetime import datetime

# ============================================================
# SERJÃO PURURUCAS
# Aplicativo de chat com IA usando Streamlit + Google GenAI
# ============================================================

st.set_page_config(
    page_title="Serjão Pururucas",
    page_icon="🍊",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ============================================================
# CONFIGURAÇÕES
# ============================================================

APP_NAME = "Serjão Pururucas"
APP_ICON = "🍊"
MODEL_NAME = "gemini-3.8-flash"

SYSTEM_INSTRUCTION = """
Você é o Serjão Pururucas, uma inteligência artificial brasileira,
engraçada, amigável e inteligente.

REGRAS:
- Fale sempre em português do Brasil, salvo se o usuário pedir outro idioma.
- Seja útil, claro e amigável.
- Faça brincadeiras leves quando fizer sentido.
- Não exagere nas piadas.
- Explique assuntos difíceis de maneira simples.
- Não invente informações.
- Se não souber algo, diga claramente que não sabe.
- Nunca diga que seu nome é Gemini.
- Se perguntarem seu nome, diga que você é o Serjão Pururucas.
- Use emojis ocasionalmente, sem exagerar.
- Para programação, coloque código em blocos Markdown com a linguagem correta.
- Não coloque código Python solto no meio de uma frase.
- Organize respostas longas com títulos, listas e parágrafos.
"""

# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>
    .stApp {
        background-color: #111111;
    }

    [data-testid="stHeader"] {
        background-color: #111111;
    }

    h1 {
        color: #ff7900 !important;
        font-weight: 800 !important;
    }

    h2, h3 {
        color: #ff9d4d !important;
    }

    .stCaption {
        color: #aaaaaa !important;
    }

    [data-testid="stChatInput"] {
        border: 2px solid #ff7900;
        border-radius: 15px;
    }

    [data-testid="stChatInput"] textarea {
        color: white !important;
    }

    .stChatMessage {
        border-radius: 15px;
    }

    [data-testid="stSidebar"] {
        background-color: #151515;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ff7900 !important;
    }

    .serjao-card {
        background: #1b1b1b;
        border: 1px solid #333333;
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 14px;
    }

    .serjao-title {
        color: #ff7900;
        font-size: 22px;
        font-weight: 800;
    }

    .serjao-small {
        color: #aaaaaa;
        font-size: 13px;
    }

    .serjao-status {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        background: #173d24;
        color: #72e69a;
        font-size: 12px;
        font-weight: 700;
    }

    code {
        border-radius: 8px;
    }

    pre {
        border-radius: 10px !important;
    }

    .stButton > button {
        border-radius: 10px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def inicializar_estado():
    """Cria todas as variáveis necessárias na sessão."""
    if "mensagens" not in st.session_state:
        st.session_state.mensagens = []

    if "chat_id" not in st.session_state:
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    if "contador_mensagens" not in st.session_state:
        st.session_state.contador_mensagens = 0

    if "ultima_resposta" not in st.session_state:
        st.session_state.ultima_resposta = ""

    if "erro_api" not in st.session_state:
        st.session_state.erro_api = None

    if "modo_rapido" not in st.session_state:
        st.session_state.modo_rapido = True

    if "mostrar_dicas" not in st.session_state:
        st.session_state.mostrar_dicas = True

    if "temperatura" not in st.session_state:
        st.session_state.temperatura = 0.7


def obter_cliente():
    """Cria o cliente da API usando o segredo configurado no Streamlit."""
    if "GOOGLE_API_KEY" not in st.secrets:
        return None

    chave = st.secrets["GOOGLE_API_KEY"]

    if not chave:
        return None

    return genai.Client(api_key=chave)


def limpar_texto(texto):
    """Limpa espaços desnecessários sem destruir a formatação Markdown."""
    if texto is None:
        return ""

    texto = str(texto)
    texto = texto.replace("\r\n", "\n")
    texto = texto.replace("\r", "\n")

    linhas = texto.split("\n")
    resultado = []

    for linha in linhas:
        resultado.append(linha.rstrip())

    return "\n".join(resultado).strip()


def contar_caracteres(texto):
    """Retorna o número de caracteres."""
    if not texto:
        return 0
    return len(texto)


def contar_palavras(texto):
    """Conta palavras de maneira simples."""
    if not texto:
        return 0
    return len(texto.split())


def formatar_hora():
    """Retorna a hora local do servidor."""
    return datetime.now().strftime("%H:%M")


def criar_prompt(pergunta, historico):
    """Monta o prompt enviado ao modelo."""
    partes = [SYSTEM_INSTRUCTION]

    if historico:
        partes.append("\nHISTÓRICO RECENTE DA CONVERSA:")

        historico_recente = historico[-12:]

        for mensagem in historico_recente:
            papel = mensagem.get("role", "")
            conteudo = mensagem.get("content", "")

            if papel == "user":
                partes.append(f"Usuário: {conteudo}")

            elif papel == "assistant":
                partes.append(f"Serjão Pururucas: {conteudo}")

    partes.append("\nNOVA MENSAGEM DO USUÁRIO:")
    partes.append(pergunta)

    partes.append(
        """
Responda diretamente à nova mensagem.
Não repita o histórico inteiro.
Se houver código, use blocos Markdown com a linguagem apropriada.
"""
    )

    return "\n".join(partes)


def gerar_resposta(cliente, pergunta, historico):
    """Gera a resposta do modelo."""
    prompt = criar_prompt(pergunta, historico)

    resposta = cliente.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=st.session_state.temperatura,
        ),
    )

    texto = getattr(resposta, "text", None)

    if not texto:
        return "Não consegui gerar uma resposta agora. Tenta novamente."

    return limpar_texto(texto)


def mostrar_mensagem(role, content):
    """Mostra uma mensagem no formato de chat."""
    with st.chat_message(role):
        st.markdown(content)


def adicionar_mensagem(role, content):
    """Adiciona uma mensagem ao histórico."""
    st.session_state.mensagens.append(
        {
            "role": role,
            "content": content,
            "hora": formatar_hora(),
        }
    )


def limpar_conversa():
    """Apaga o histórico atual."""
    st.session_state.mensagens = []
    st.session_state.ultima_resposta = ""
    st.session_state.erro_api = None
    st.session_state.contador_mensagens = 0


def exportar_conversa():
    """Cria uma versão de texto da conversa."""
    linhas = []
    linhas.append("SERJÃO PURURUCAS")
    linhas.append("=" * 40)
    linhas.append("")

    for mensagem in st.session_state.mensagens:
        papel = mensagem.get("role", "unknown")
        content = mensagem.get("content", "")
        hora = mensagem.get("hora", "")

        if papel == "user":
            nome = "Usuário"
        else:
            nome = "Serjão Pururucas"

        linhas.append(f"[{hora}] {nome}:")
        linhas.append(content)
        linhas.append("")
        linhas.append("-" * 40)
        linhas.append("")

    return "\n".join(linhas)


def detectar_codigo(texto):
    """Detecta se a resposta possui blocos de código Markdown."""
    if not texto:
        return False

    return "```" in texto


def resumo_sessao():
    """Retorna informações básicas da sessão."""
    total = len(st.session_state.mensagens)
    usuarios = sum(
        1
        for m in st.session_state.mensagens
        if m.get("role") == "user"
    )
    respostas = sum(
        1
        for m in st.session_state.mensagens
        if m.get("role") == "assistant"
    )

    return total, usuarios, respostas


# ============================================================
# INICIALIZAÇÃO
# ============================================================

inicializar_estado()

# ============================================================
# CABEÇALHO
# ============================================================

st.title("🍊 Serjão Pururucas")
st.caption("Sua IA meio doida, mas que tenta ajudar.")

st.markdown(
    '<span class="serjao-status">● Online</span>',
    unsafe_allow_html=True,
)

st.write("")

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("🍊 Serjão")

    st.markdown(
        """
        <div class="serjao-card">
            <div class="serjao-title">Painel</div>
            <div class="serjao-small">
                Configure sua experiência de conversa.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🗑️ Nova conversa", use_container_width=True):
        limpar_conversa()
        st.rerun()

    st.divider()

    st.subheader("⚙️ Configurações")

    st.session_state.modo_rapido = st.toggle(
        "⚡ Modo rápido",
        value=st.session_state.modo_rapido,
    )

    st.session_state.mostrar_dicas = st.toggle(
        "💡 Mostrar dicas",
        value=st.session_state.mostrar_dicas,
    )

    st.session_state.temperatura = st.slider(
        "🎨 Criatividade",
        min_value=0.0,
        max_value=1.0,
        value=float(st.session_state.temperatura),
        step=0.1,
        help="Valores maiores deixam as respostas mais variadas.",
    )

    st.divider()

    st.subheader("📊 Sessão")

    total, usuarios, respostas = resumo_sessao()

    st.write(f"💬 Mensagens: **{total}**")
    st.write(f"👤 Suas mensagens: **{usuarios}**")
    st.write(f"🍊 Respostas: **{respostas}**")

    st.divider()

    st.subheader("💾 Conversa")

    texto_exportacao = exportar_conversa()

    st.download_button(
        label="📥 Baixar conversa",
        data=texto_exportacao,
        file_name=f"serjao_{st.session_state.chat_id}.txt",
        mime="text/plain",
        use_container_width=True,
    )

    st.divider()

    st.markdown(
        """
        <div class="serjao-card">
            <b>Serjão Pururucas</b><br>
            <span class="serjao-small">
                Feito com Streamlit + Google GenAI.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# VERIFICAÇÃO DA API
# ============================================================

cliente = obter_cliente()

if cliente is None:
    st.error(
        "A chave GOOGLE_API_KEY não está configurada. "
        "Adicione a chave nos Secrets do Streamlit."
    )
    st.stop()

# ============================================================
# DICAS INICIAIS
# ============================================================

if not st.session_state.mensagens and st.session_state.mostrar_dicas:
    st.markdown(
        """
        <div class="serjao-card">
            <div class="serjao-title">👋 Fala aí!</div>
            <p>
                Eu sou o <b>Serjão Pururucas</b>.
                Pode perguntar sobre estudos, programação,
                ideias, matemática, jogos e muito mais.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "📚 Me ajuda a estudar",
            use_container_width=True,
        ):
            st.session_state.sugestao = (
                "Me ajude a montar um resumo para estudar."
            )

    with col2:
        if st.button(
            "💻 Me ajuda com código",
            use_container_width=True,
        ):
            st.session_state.sugestao = (
                "Me ajude a criar um código Python simples."
            )

# ============================================================
# HISTÓRICO
# ============================================================

for mensagem in st.session_state.mensagens:
    role = mensagem.get("role", "assistant")
    content = mensagem.get("content", "")

    if role in ("user", "assistant"):
        mostrar_mensagem(role, content)

# ============================================================
# ENTRADA DE TEXTO
# ============================================================

sugestao = st.session_state.pop("sugestao", None)

pergunta = st.chat_input(
    "Fala aí, manda sua pergunta..."
)

if sugestao and not pergunta:
    pergunta = sugestao

# ============================================================
# PROCESSAMENTO
# ============================================================

if pergunta:
    pergunta = pergunta.strip()

    if not pergunta:
        st.warning("Digite alguma coisa primeiro 😅")
        st.stop()

    if len(pergunta) > 12000:
        st.error(
            "Essa mensagem ficou muito grande. "
            "Tente dividir em partes."
        )
        st.stop()

    adicionar_mensagem("user", pergunta)
    st.session_state.contador_mensagens += 1

    mostrar_mensagem("user", pergunta)

    with st.chat_message("assistant"):
        with st.spinner("O Serjão está pensando... 🍊"):
            try:
                historico = st.session_state.mensagens[:-1]

                texto_resposta = gerar_resposta(
                    cliente,
                    pergunta,
                    historico,
                )

                st.session_state.ultima_resposta = texto_resposta
                st.session_state.erro_api = None

            except Exception as erro:
                texto_resposta = (
                    "Deu um problema ao falar com a IA. 😅\n\n"
                    "Tente novamente em alguns segundos."
                )

                st.session_state.erro_api = str(erro)

        st.markdown(texto_resposta)

    adicionar_mensagem(
        "assistant",
        texto_resposta,
    )

# ============================================================
# INFORMAÇÕES DA ÚLTIMA RESPOSTA
# ============================================================

if st.session_state.ultima_resposta:
    resposta_atual = st.session_state.ultima_resposta

    with st.expander("ℹ️ Informações da resposta"):
        caracteres = contar_caracteres(resposta_atual)
        palavras = contar_palavras(resposta_atual)
        possui_codigo = detectar_codigo(resposta_atual)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Caracteres", caracteres)

        with col2:
            st.metric("Palavras", palavras)

        with col3:
            st.metric(
                "Código",
                "Sim" if possui_codigo else "Não",
            )

# ============================================================
# ERRO TÉCNICO OPCIONAL
# ============================================================

if st.session_state.erro_api:
    with st.expander("🔧 Detalhes técnicos"):
        st.caption(
            "Essas informações podem ajudar a identificar "
            "um problema de configuração."
        )
        st.code(
            st.session_state.erro_api,
            language="text",
        )

# ============================================================
# RODAPÉ
# ============================================================

st.divider()

st.caption(
    "🍊 Serjão Pururucas • Uma IA brasileira feita com carinho."
)

# ============================================================
# FIM DO APLICATIVO
# ============================================================


# ============================================================
# FUNÇÕES EXTRAS DE APOIO
# ============================================================

def normalizar_pergunta(texto):
    """Normaliza uma pergunta sem alterar seu conteúdo principal."""
    if texto is None:
        return ""
    return " ".join(str(texto).strip().split())


def pergunta_tem_conteudo(texto):
    """Verifica se uma pergunta contém conteúdo útil."""
    return bool(normalizar_pergunta(texto))


def tamanho_seguro(texto, limite=12000):
    """Verifica se um texto está dentro do limite escolhido."""
    return len(texto or "") <= limite


def preparar_nome_arquivo(nome):
    """Remove caracteres problemáticos de nomes de arquivos."""
    nome = str(nome or "arquivo")
    nome = re.sub(r"[^a-zA-Z0-9_-]+", "_", nome)
    return nome[:80]


def obter_data_formatada():
    """Data atual formatada para uso em registros locais."""
    return datetime.now().strftime("%d/%m/%Y")


def obter_data_hora_formatada():
    """Data e hora atual formatadas."""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def mensagem_e_usuario(mensagem):
    """Verifica se uma mensagem é do usuário."""
    return mensagem.get("role") == "user"


def mensagem_e_assistente(mensagem):
    """Verifica se uma mensagem é do assistente."""
    return mensagem.get("role") == "assistant"


def obter_ultima_mensagem():
    """Retorna a última mensagem da sessão."""
    if not st.session_state.mensagens:
        return None
    return st.session_state.mensagens[-1]


def obter_ultima_pergunta():
    """Retorna a última pergunta do usuário."""
    for mensagem in reversed(st.session_state.mensagens):
        if mensagem_e_usuario(mensagem):
            return mensagem.get("content", "")
    return ""


def obter_ultima_resposta():
    """Retorna a última resposta do assistente."""
    for mensagem in reversed(st.session_state.mensagens):
        if mensagem_e_assistente(mensagem):
            return mensagem.get("content", "")
    return ""


def quantidade_de_turnos():
    """Retorna a quantidade de turnos completos."""
    usuarios = sum(
        1
        for mensagem in st.session_state.mensagens
        if mensagem_e_usuario(mensagem)
    )
    return usuarios


def possui_conversa():
    """Retorna True se houver mensagens."""
    return len(st.session_state.mensagens) > 0


def conversa_vazia():
    """Retorna True quando não há mensagens."""
    return not possui_conversa()


def apagar_ultima_mensagem():
    """Remove a última mensagem da conversa."""
    if st.session_state.mensagens:
        st.session_state.mensagens.pop()


def apagar_ultimo_turno():
    """Remove o último par pergunta/resposta."""
    if not st.session_state.mensagens:
        return

    apagar_ultima_mensagem()

    if st.session_state.mensagens:
        apagar_ultima_mensagem()


def limitar_historico(maximo=30):
    """Limita o histórico armazenado na sessão."""
    if len(st.session_state.mensagens) > maximo:
        st.session_state.mensagens = (
            st.session_state.mensagens[-maximo:]
        )


def copiar_texto(texto):
    """Retorna texto pronto para download/cópia."""
    return str(texto or "")


def construir_titulo_conversa():
    """Cria um título simples para a conversa."""
    primeira = obter_ultima_pergunta()

    if not primeira:
        return "Nova conversa"

    primeira = normalizar_pergunta(primeira)

    if len(primeira) > 45:
        primeira = primeira[:45] + "..."

    return primeira


def validar_modelo(nome_modelo):
    """Verifica se o nome do modelo foi informado."""
    return bool(nome_modelo and isinstance(nome_modelo, str))


def chave_configurada():
    """Verifica se a chave existe nos Secrets."""
    return "GOOGLE_API_KEY" in st.secrets


def estado_api():
    """Retorna o estado simples da configuração da API."""
    if not chave_configurada():
        return "não configurada"

    chave = st.secrets["GOOGLE_API_KEY"]

    if not chave:
        return "vazia"

    return "configurada"


def criar_mensagem_erro():
    """Mensagem amigável para falhas genéricas."""
    return (
        "Não consegui concluir essa resposta agora. "
        "Tente novamente."
    )


def criar_mensagem_limite():
    """Mensagem para entradas muito grandes."""
    return (
        "Essa mensagem ficou grande demais. "
        "Divida o conteúdo em partes e tente novamente."
    )


def criar_mensagem_vazia():
    """Mensagem para entrada vazia."""
    return "Manda alguma coisa para o Serjão responder 😅"


def texto_para_download():
    """Gera o conteúdo completo da conversa."""
    return exportar_conversa()


def nome_download():
    """Gera nome seguro para o arquivo da conversa."""
    data = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"serjao_conversa_{data}.txt"


def possui_markdown(texto):
    """Detecta alguns sinais básicos de Markdown."""
    if not texto:
        return False

    sinais = [
        "**",
        "__",
        "```",
        "# ",
        "- ",
        "1. ",
    ]

    return any(sinal in texto for sinal in sinais)


def possui_lista(texto):
    """Detecta listas simples."""
    if not texto:
        return False

    for linha in texto.splitlines():
        linha_limpa = linha.strip()

        if linha_limpa.startswith("- "):
            return True

        if re.match(r"^\d+\.\s", linha_limpa):
            return True

    return False


def possui_titulo(texto):
    """Detecta títulos Markdown."""
    if not texto:
        return False

    for linha in texto.splitlines():
        if linha.strip().startswith("#"):
            return True

    return False


def extrair_blocos_codigo(texto):
    """Extrai blocos de código Markdown."""
    if not texto:
        return []

    padrao = r"```(?:([a-zA-Z0-9_+-]+))?\n(.*?)```"
    encontrados = re.findall(
        padrao,
        texto,
        flags=re.DOTALL,
    )

    blocos = []

    for linguagem, codigo in encontrados:
        blocos.append(
            {
                "linguagem": linguagem or "text",
                "codigo": codigo,
            }
        )

    return blocos


def quantidade_blocos_codigo(texto):
    """Conta blocos de código."""
    return len(extrair_blocos_codigo(texto))


def detectar_python(texto):
    """Detecta indicação explícita de Python."""
    if not texto:
        return False

    return bool(
        re.search(
            r"```python|```py",
            texto,
            flags=re.IGNORECASE,
        )
    )


def detectar_javascript(texto):
    """Detecta indicação explícita de JavaScript."""
    if not texto:
        return False

    return bool(
        re.search(
            r"```javascript|```js",
            texto,
            flags=re.IGNORECASE,
        )
    )


def detectar_html(texto):
    """Detecta indicação explícita de HTML."""
    if not texto:
        return False

    return bool(
        re.search(
            r"```html",
            texto,
            flags=re.IGNORECASE,
        )
    )


def detectar_css(texto):
    """Detecta indicação explícita de CSS."""
    if not texto:
        return False

    return bool(
        re.search(
            r"```css",
            texto,
            flags=re.IGNORECASE,
        )
    )


def detectar_json(texto):
    """Detecta indicação explícita de JSON."""
    if not texto:
        return False

    return bool(
        re.search(
            r"```json",
            texto,
            flags=re.IGNORECASE,
        )
    )


def limpar_codigo(codigo):
    """Limpa espaços extras em um bloco de código."""
    if codigo is None:
        return ""

    return codigo.strip("\n")


def estatisticas_resposta(texto):
    """Retorna estatísticas simples de uma resposta."""
    return {
        "caracteres": contar_caracteres(texto),
        "palavras": contar_palavras(texto),
        "blocos_codigo": quantidade_blocos_codigo(texto),
        "tem_markdown": possui_markdown(texto),
        "tem_lista": possui_lista(texto),
        "tem_titulo": possui_titulo(texto),
    }


def historico_para_texto(mensagens):
    """Converte histórico em texto."""
    partes = []

    for mensagem in mensagens or []:
        role = mensagem.get("role", "")
        content = mensagem.get("content", "")

        nome = (
            "Usuário"
            if role == "user"
            else "Serjão Pururucas"
        )

        partes.append(f"{nome}: {content}")

    return "\n\n".join(partes)


def historico_para_json(mensagens):
    """Converte histórico para JSON."""
    return json.dumps(
        mensagens or [],
        ensure_ascii=False,
        indent=2,
    )


def quantidade_caracteres_conversa():
    """Conta caracteres de toda a conversa."""
    return sum(
        contar_caracteres(mensagem.get("content", ""))
        for mensagem in st.session_state.mensagens
    )


def quantidade_palavras_conversa():
    """Conta palavras de toda a conversa."""
    return sum(
        contar_palavras(mensagem.get("content", ""))
        for mensagem in st.session_state.mensagens
    )


def conversa_json_download():
    """Retorna JSON pronto para download."""
    return historico_para_json(
        st.session_state.mensagens
    )


def conversa_txt_download():
    """Retorna TXT pronto para download."""
    return historico_para_texto(
        st.session_state.mensagens
    )


def mensagem_tem_hora(mensagem):
    """Verifica se uma mensagem possui horário."""
    return bool(mensagem.get("hora"))


def mensagens_do_usuario():
    """Retorna somente mensagens do usuário."""
    return [
        mensagem
        for mensagem in st.session_state.mensagens
        if mensagem_e_usuario(mensagem)
    ]


def mensagens_do_assistente():
    """Retorna somente mensagens do assistente."""
    return [
        mensagem
        for mensagem in st.session_state.mensagens
        if mensagem_e_assistente(mensagem)
    ]


def primeira_mensagem():
    """Retorna a primeira mensagem."""
    if not st.session_state.mensagens:
        return None
    return st.session_state.mensagens[0]


def ultima_mensagem():
    """Retorna a última mensagem."""
    if not st.session_state.mensagens:
        return None
    return st.session_state.mensagens[-1]


def conversa_tem_resposta():
    """Verifica se já existe resposta do assistente."""
    return any(
        mensagem_e_assistente(mensagem)
        for mensagem in st.session_state.mensagens
    )


def conversa_tem_pergunta():
    """Verifica se já existe pergunta do usuário."""
    return any(
        mensagem_e_usuario(mensagem)
        for mensagem in st.session_state.mensagens
    )


def criar_id_mensagem():
    """Cria um identificador simples baseado no horário."""
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


def registrar_mensagem(role, content):
    """Cria uma mensagem completa."""
    return {
        "id": criar_id_mensagem(),
        "role": role,
        "content": content,
        "hora": formatar_hora(),
        "data": obter_data_formatada(),
    }


def adicionar_mensagem_completa(role, content):
    """Adiciona mensagem com metadados."""
    st.session_state.mensagens.append(
        registrar_mensagem(role, content)
    )


def quantidade_mensagens_usuario():
    """Conta mensagens do usuário."""
    return len(mensagens_do_usuario())


def quantidade_mensagens_assistente():
    """Conta mensagens do assistente."""
    return len(mensagens_do_assistente())


def conversa_balanceada():
    """Verifica se há quantidade semelhante de perguntas e respostas."""
    usuarios = quantidade_mensagens_usuario()
    assistentes = quantidade_mensagens_assistente()

    return usuarios == assistentes


def ultimo_papel():
    """Retorna o papel da última mensagem."""
    mensagem = ultima_mensagem()

    if not mensagem:
        return None

    return mensagem.get("role")


def ultima_mensagem_e_usuario():
    """Verifica se a última mensagem é do usuário."""
    return ultimo_papel() == "user"


def ultima_mensagem_e_assistente():
    """Verifica se a última mensagem é do assistente."""
    return ultimo_papel() == "assistant"


def gerar_id_chat():
    """Gera identificador para a conversa."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def garantir_id_chat():
    """Garante que a sessão tenha um ID."""
    if not st.session_state.get("chat_id"):
        st.session_state.chat_id = gerar_id_chat()

    return st.session_state.chat_id


def texto_seguro_para_markdown(texto):
    """Mantém texto seguro para exibição em Markdown."""
    return str(texto or "")


def exibir_resposta_formatada(texto):
    """Exibe uma resposta preservando Markdown."""
    st.markdown(texto_seguro_para_markdown(texto))


def exibir_usuario(texto):
    """Exibe mensagem do usuário."""
    with st.chat_message("user"):
        st.markdown(texto_seguro_para_markdown(texto))


def exibir_assistente(texto):
    """Exibe mensagem do assistente."""
    with st.chat_message("assistant"):
        st.markdown(texto_seguro_para_markdown(texto))


def obter_modelo_atual():
    """Retorna o modelo utilizado."""
    return MODEL_NAME


def obter_nome_aplicativo():
    """Retorna o nome do aplicativo."""
    return APP_NAME


def obter_icone_aplicativo():
    """Retorna o ícone do aplicativo."""
    return APP_ICON


def sistema_pronto():
    """Verifica se os elementos básicos estão prontos."""
    return (
        cliente is not None
        and validar_modelo(MODEL_NAME)
    )


def status_texto():
    """Retorna texto amigável do estado da aplicação."""
    if sistema_pronto():
        return "Online"

    return "Configuração pendente"


def limpar_erro():
    """Limpa erro salvo na sessão."""
    st.session_state.erro_api = None


def salvar_erro(erro):
    """Salva representação textual de um erro."""
    st.session_state.erro_api = str(erro)


def possui_erro():
    """Verifica se existe erro salvo."""
    return bool(st.session_state.erro_api)


def reiniciar_estado_conversa():
    """Reinicia apenas dados relacionados à conversa."""
    st.session_state.mensagens = []
    st.session_state.ultima_resposta = ""
    st.session_state.erro_api = None
    st.session_state.contador_mensagens = 0


def configurar_padrao():
    """Mantém uma função central para padrões futuros."""
    return {
        "nome": APP_NAME,
        "modelo": MODEL_NAME,
        "icone": APP_ICON,
    }


def informacoes_app():
    """Retorna informações do aplicativo."""
    return {
        "nome": APP_NAME,
        "modelo": MODEL_NAME,
        "data": obter_data_formatada(),
        "status": status_texto(),
    }


def criar_relatorio_sessao():
    """Cria resumo textual da sessão."""
    total, usuarios, respostas = resumo_sessao()

    return (
        f"Aplicativo: {APP_NAME}\n"
        f"Modelo: {MODEL_NAME}\n"
        f"Mensagens: {total}\n"
        f"Usuário: {usuarios}\n"
        f"Assistente: {respostas}\n"
        f"Data: {obter_data_hora_formatada()}\n"
    )


def limpar_espacos_externos(texto):
    """Remove espaços externos."""
    return str(texto or "").strip()


def texto_normalizado(texto):
    """Normaliza texto básico."""
    return limpar_espacos_externos(texto)


def texto_tem_numero(texto):
    """Verifica se o texto contém algum número."""
    return bool(re.search(r"\d", texto or ""))


def texto_tem_link(texto):
    """Detecta links HTTP/HTTPS."""
    return bool(
        re.search(
            r"https?://",
            texto or "",
            flags=re.IGNORECASE,
        )
    )


def texto_tem_email(texto):
    """Detecta formato simples de e-mail."""
    return bool(
        re.search(
            r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b",
            texto or "",
        )
    )


def texto_tem_interrogacao(texto):
    """Verifica se há interrogação."""
    return "?" in (texto or "")


def texto_tem_exclamacao(texto):
    """Verifica se há exclamação."""
    return "!" in (texto or "")


def comprimento_pergunta(texto):
    """Retorna o comprimento da pergunta."""
    return len(texto or "")


def pergunta_curta(texto):
    """Classifica pergunta curta."""
    return comprimento_pergunta(texto) <= 80


def pergunta_longa(texto):
    """Classifica pergunta longa."""
    return comprimento_pergunta(texto) > 500


def criar_contexto_curto():
    """Cria contexto das últimas mensagens."""
    return criar_prompt(
        "",
        st.session_state.mensagens[-6:],
    )


def quantidade_contexto():
    """Retorna quantidade de mensagens no contexto atual."""
    return len(st.session_state.mensagens[-12:])


def limpar_contexto_antigo():
    """Aplica limite simples ao histórico."""
    limitar_historico(30)


def atualizar_contador():
    """Atualiza contador com base no histórico."""
    st.session_state.contador_mensagens = (
        quantidade_mensagens_usuario()
    )


def resumo_textual():
    """Retorna resumo simples da conversa."""
    if conversa_vazia():
        return "Nenhuma mensagem ainda."

    return (
        f"{quantidade_mensagens_usuario()} perguntas e "
        f"{quantidade_mensagens_assistente()} respostas."
    )


def dados_sessao():
    """Retorna dados básicos da sessão."""
    return {
        "chat_id": garantir_id_chat(),
        "mensagens": len(st.session_state.mensagens),
        "perguntas": quantidade_mensagens_usuario(),
        "respostas": quantidade_mensagens_assistente(),
    }


def validar_historico():
    """Verifica se o histórico possui estrutura esperada."""
    if not isinstance(st.session_state.mensagens, list):
        st.session_state.mensagens = []

    return True


def corrigir_historico():
    """Remove itens inválidos do histórico."""
    mensagens_validas = []

    for mensagem in st.session_state.mensagens:
        if not isinstance(mensagem, dict):
            continue

        if mensagem.get("role") not in (
            "user",
            "assistant",
        ):
            continue

        if "content" not in mensagem:
            continue

        mensagens_validas.append(mensagem)

    st.session_state.mensagens = mensagens_validas


def preparar_sessao():
    """Executa pequenas verificações de segurança da sessão."""
    validar_historico()
    corrigir_historico()
    limitar_historico(30)
    garantir_id_chat()
    atualizar_contador()


def resposta_pronta_para_exibicao(texto):
    """Verifica se a resposta pode ser exibida."""
    return bool(
        isinstance(texto, str)
        and texto.strip()
    )


def fallback_resposta():
    """Retorna resposta de fallback."""
    return (
        "Não consegui gerar uma resposta válida agora. "
        "Tente novamente."
    )


def resposta_segura(texto):
    """Garante que uma resposta não seja None."""
    if not resposta_pronta_para_exibicao(texto):
        return fallback_resposta()

    return texto


def montar_mensagem_usuario(pergunta):
    """Normaliza pergunta antes do processamento."""
    return normalizar_pergunta(pergunta)


def validar_pergunta(pergunta):
    """Valida pergunta para processamento."""
    pergunta = montar_mensagem_usuario(pergunta)

    if not pergunta:
        return False, criar_mensagem_vazia()

    if not tamanho_seguro(pergunta):
        return False, criar_mensagem_limite()

    return True, pergunta


def registrar_pergunta(pergunta):
    """Registra uma pergunta no histórico."""
    adicionar_mensagem("user", pergunta)


def registrar_resposta(resposta):
    """Registra uma resposta no histórico."""
    adicionar_mensagem("assistant", resposta)


def obter_contexto_antes_da_pergunta():
    """Retorna histórico sem a última pergunta."""
    if not st.session_state.mensagens:
        return []

    return st.session_state.mensagens[:-1]


def gerar_resposta_segura(cliente_api, pergunta):
    """Wrapper seguro para geração."""
    try:
        historico = obter_contexto_antes_da_pergunta()

        resposta = gerar_resposta(
            cliente_api,
            pergunta,
            historico,
        )

        return resposta_segura(resposta), None

    except Exception as erro:
        return fallback_resposta(), erro


def registrar_resultado(resposta, erro=None):
    """Registra resultado da geração."""
    st.session_state.ultima_resposta = resposta

    if erro is None:
        limpar_erro()
    else:
        salvar_erro(erro)


def mostrar_estatisticas():
    """Mostra estatísticas resumidas da conversa."""
    if not possui_conversa():
        return

    with st.expander("📊 Estatísticas da conversa"):
        st.write(
            f"Total de mensagens: "
            f"**{len(st.session_state.mensagens)}**"
        )

        st.write(
            f"Perguntas: "
            f"**{quantidade_mensagens_usuario()}**"
        )

        st.write(
            f"Respostas: "
            f"**{quantidade_mensagens_assistente()}**"
        )

        st.write(
            f"Caracteres: "
            f"**{quantidade_caracteres_conversa()}**"
        )

        st.write(
            f"Palavras: "
            f"**{quantidade_palavras_conversa()}**"
        )


def criar_backup_local():
    """Retorna backup textual do histórico."""
    return historico_para_json(
        st.session_state.mensagens
    )


def nome_backup():
    """Nome do backup."""
    return preparar_nome_arquivo(
        f"serjao_backup_{st.session_state.chat_id}.json"
    )


def mostrar_backup():
    """Exibe opção de backup."""
    if not possui_conversa():
        return

    with st.expander("🗂️ Backup"):
        st.download_button(
            "📥 Baixar backup JSON",
            data=criar_backup_local(),
            file_name=nome_backup(),
            mime="application/json",
        )


def mostrar_info_modelo():
    """Mostra informações do modelo."""
    with st.expander("🤖 Modelo"):
        st.write(f"Modelo configurado: `{MODEL_NAME}`")
        st.write(f"Aplicativo: **{APP_NAME}**")
        st.write(f"Status: **{status_texto()}**")


def pode_gerar():
    """Verifica condições básicas para geração."""
    return (
        cliente is not None
        and validar_modelo(MODEL_NAME)
    )


def aviso_se_indisponivel():
    """Mostra aviso se a API não estiver pronta."""
    if pode_gerar():
        return False

    st.warning(
        "A IA ainda não está pronta para responder. "
        "Verifique a configuração da API."
    )

    return True


def texto_status():
    """Texto curto de status."""
    return (
        "🟢 Online"
        if pode_gerar()
        else
        "🟠 Configuração pendente"
    )


def mostrar_status():
    """Mostra status da aplicação."""
    st.caption(texto_status())


def criar_sugestao(texto):
    """Cria uma sugestão padronizada."""
    return {
        "texto": texto,
        "criada_em": obter_data_hora_formatada(),
    }


def sugestoes_padrao():
    """Retorna sugestões padrão."""
    return [
        criar_sugestao("Explique matemática de um jeito fácil."),
        criar_sugestao("Me ajude a estudar para uma prova."),
        criar_sugestao("Crie um código Python simples."),
        criar_sugestao("Explique esse assunto como se eu tivesse 10 anos."),
    ]


def validar_sugestao(sugestao):
    """Verifica se uma sugestão é válida."""
    return (
        isinstance(sugestao, dict)
        and bool(sugestao.get("texto"))
    )


def textos_sugestoes():
    """Retorna somente textos das sugestões."""
    return [
        sugestao["texto"]
        for sugestao in sugestoes_padrao()
        if validar_sugestao(sugestao)
    ]


def quantidade_sugestoes():
    """Quantidade de sugestões disponíveis."""
    return len(textos_sugestoes())


def sugestao_por_indice(indice):
    """Retorna sugestão pelo índice."""
    sugestoes = textos_sugestoes()

    if indice < 0 or indice >= len(sugestoes):
        return None

    return sugestoes[indice]


def tem_sugestoes():
    """Verifica se há sugestões."""
    return quantidade_sugestoes() > 0


def construir_prompt_simples(pergunta):
    """Cria prompt sem histórico."""
    return (
        SYSTEM_INSTRUCTION
        + "\n\nMensagem do usuário:\n"
        + pergunta
    )


def construir_prompt_completo(pergunta):
    """Cria prompt com histórico atual."""
    return criar_prompt(
        pergunta,
        st.session_state.mensagens,
    )


def modelo_configurado():
    """Retorna nome do modelo se válido."""
    if validar_modelo(MODEL_NAME):
        return MODEL_NAME

    return "modelo não configurado"


def configuracao_resumida():
    """Resumo da configuração."""
    return {
        "modelo": modelo_configurado(),
        "api": estado_api(),
        "temperatura": st.session_state.temperatura,
    }


def temperatura_valida(valor):
    """Valida temperatura."""
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return False

    return 0.0 <= valor <= 1.0


def corrigir_temperatura():
    """Corrige temperatura inválida."""
    if not temperatura_valida(
        st.session_state.temperatura
    ):
        st.session_state.temperatura = 0.7


def preparar_configuracoes():
    """Prepara configurações da sessão."""
    corrigir_temperatura()


def executar_preparacao():
    """Executa preparações gerais."""
    preparar_sessao()
    preparar_configuracoes()


def app_esta_pronto():
    """Estado geral do aplicativo."""
    return (
        chave_configurada()
        and validar_modelo(MODEL_NAME)
    )


def nome_status():
    """Nome do estado."""
    return "Pronto" if app_esta_pronto() else "Pendente"


def relatorio_tecnico():
    """Relatório técnico curto."""
    configuracao = configuracao_resumida()

    return (
        f"Modelo: {configuracao['modelo']}\n"
        f"API: {configuracao['api']}\n"
        f"Temperatura: {configuracao['temperatura']}\n"
        f"Status: {nome_status()}"
    )


def exibir_relatorio_tecnico():
    """Exibe relatório técnico."""
    with st.expander("🛠️ Relatório técnico"):
        st.code(
            relatorio_tecnico(),
            language="text",
        )


def exportacao_disponivel():
    """Verifica se há algo para exportar."""
    return possui_conversa()


def texto_copiavel():
    """Retorna conversa em texto."""
    return conversa_txt_download()


def texto_json():
    """Retorna conversa em JSON."""
    return conversa_json_download()


def criar_nome_txt():
    """Nome do TXT."""
    return nome_download()


def criar_nome_json():
    """Nome do JSON."""
    return preparar_nome_arquivo(
        f"serjao_{st.session_state.chat_id}.json"
    )


def limitar_tamanho_exportacao(texto, limite=1000000):
    """Evita exportações absurdamente grandes."""
    texto = str(texto or "")

    if len(texto) <= limite:
        return texto

    return texto[:limite] + "\n[conteúdo cortado]"


def exportar_txt_seguro():
    """Exporta TXT limitado."""
    return limitar_tamanho_exportacao(
        texto_copiavel()
    )


def exportar_json_seguro():
    """Exporta JSON limitado."""
    return limitar_tamanho_exportacao(
        texto_json()
    )


def hora_atual():
    """Hora atual."""
    return datetime.now().strftime("%H:%M:%S")


def data_atual():
    """Data atual."""
    return datetime.now().strftime("%d/%m/%Y")


def timestamp_atual():
    """Timestamp atual."""
    return datetime.now().isoformat()


def criar_evento(tipo, dados=None):
    """Cria evento interno simples."""
    return {
        "tipo": tipo,
        "data": timestamp_atual(),
        "dados": dados or {},
    }


def registrar_evento(tipo, dados=None):
    """Registra evento em memória da sessão."""
    if "eventos" not in st.session_state:
        st.session_state.eventos = []

    st.session_state.eventos.append(
        criar_evento(tipo, dados)
    )

    if len(st.session_state.eventos) > 100:
        st.session_state.eventos = (
            st.session_state.eventos[-100:]
        )


def quantidade_eventos():
    """Conta eventos."""
    return len(
        st.session_state.get("eventos", [])
    )


def limpar_eventos():
    """Limpa eventos."""
    st.session_state.eventos = []


def ultimo_evento():
    """Último evento."""
    eventos = st.session_state.get("eventos", [])

    if not eventos:
        return None

    return eventos[-1]


def evento_de_pergunta(pergunta):
    """Registra pergunta como evento."""
    registrar_evento(
        "pergunta",
        {"tamanho": len(pergunta)},
    )


def evento_de_resposta(resposta):
    """Registra resposta como evento."""
    registrar_evento(
        "resposta",
        {
            "tamanho": len(resposta),
            "blocos_codigo": quantidade_blocos_codigo(
                resposta
            ),
        },
    )


def evento_de_erro(erro):
    """Registra erro sem expor dados sensíveis."""
    registrar_evento(
        "erro",
        {"tipo": type(erro).__name__},
    )


def obter_eventos():
    """Retorna eventos."""
    return st.session_state.get("eventos", [])


def eventos_json():
    """Retorna eventos em JSON."""
    return json.dumps(
        obter_eventos(),
        ensure_ascii=False,
        indent=2,
    )


def eventos_txt():
    """Retorna eventos em texto."""
    linhas = []

    for evento in obter_eventos():
        linhas.append(
            f"{evento.get('data')} - "
            f"{evento.get('tipo')}"
        )

    return "\n".join(linhas)


def id_valido(valor):
    """Valida identificador textual."""
    if not valor:
        return False

    return bool(
        re.match(
            r"^[A-Za-z0-9_-]+$",
            str(valor),
        )
    )


def chat_id_valido():
    """Verifica ID da conversa."""
    return id_valido(
        st.session_state.get("chat_id")
    )


def corrigir_chat_id():
    """Corrige ID caso necessário."""
    if not chat_id_valido():
        st.session_state.chat_id = gerar_id_chat()


def preparar_identidade():
    """Prepara identificação da conversa."""
    corrigir_chat_id()


def executar_preparacao_completa():
    """Executa preparação completa."""
    executar_preparacao()
    preparar_identidade()


def app_nome_curto():
    """Nome curto."""
    return "Serjão"


def app_descricao():
    """Descrição do app."""
    return "Sua IA meio doida, mas que tenta ajudar."


def app_creditos():
    """Créditos."""
    return "Streamlit + Google GenAI"


def mensagem_boas_vindas():
    """Mensagem de boas-vindas."""
    return (
        "👋 Fala aí! Eu sou o Serjão Pururucas. "
        "Manda sua pergunta."
    )


def mensagem_ajuda():
    """Mensagem de ajuda."""
    return (
        "Você pode perguntar sobre estudos, programação, "
        "ideias, matemática e muitos outros assuntos."
    )


def mensagem_sobre():
    """Mensagem sobre o aplicativo."""
    return (
        f"{APP_NAME} usa {MODEL_NAME} para gerar respostas."
    )


def comandos_disponiveis():
    """Lista recursos internos."""
    return [
        "nova conversa",
        "baixar conversa",
        "configurações",
        "estatísticas",
    ]


def recurso_disponivel(nome):
    """Verifica recurso."""
    return nome in comandos_disponiveis()


def quantidade_recursos():
    """Quantidade de recursos."""
    return len(comandos_disponiveis())


def status_recursos():
    """Status dos recursos."""
    return {
        nome: True
        for nome in comandos_disponiveis()
    }


def validar_texto(texto):
    """Validação genérica."""
    return isinstance(texto, str)


def validar_mensagem(mensagem):
    """Valida estrutura de mensagem."""
    return (
        isinstance(mensagem, dict)
        and mensagem.get("role") in (
            "user",
            "assistant",
        )
        and validar_texto(
            mensagem.get("content", "")
        )
    )


def validar_todas_mensagens():
    """Valida todo histórico."""
    return all(
        validar_mensagem(mensagem)
        for mensagem in st.session_state.mensagens
    )


def remover_mensagens_invalidas():
    """Remove mensagens inválidas."""
    st.session_state.mensagens = [
        mensagem
        for mensagem in st.session_state.mensagens
        if validar_mensagem(mensagem)
    ]


def preparar_historico_final():
    """Última etapa de limpeza do histórico."""
    remover_mensagens_invalidas()
    limitar_historico(30)


def sistema_interno():
    """Resumo do sistema interno."""
    return {
        "app": APP_NAME,
        "modelo": MODEL_NAME,
        "mensagens": len(st.session_state.mensagens),
        "api_configurada": chave_configurada(),
        "historico_valido": validar_todas_mensagens(),
    }


def sistema_interno_texto():
    """Sistema interno em texto."""
    dados = sistema_interno()

    linhas = []

    for chave, valor in dados.items():
        linhas.append(f"{chave}: {valor}")

    return "\n".join(linhas)


def mostrar_sistema_interno():
    """Mostra informações internas não sensíveis."""
    with st.expander("🔍 Diagnóstico"):
        st.code(
            sistema_interno_texto(),
            language="text",
        )


def validar_resposta_api(resposta):
    """Valida resposta bruta da API."""
    if resposta is None:
        return False

    return bool(
        getattr(resposta, "text", None)
    )


def texto_resposta_api(resposta):
    """Extrai texto de resposta da API."""
    if not validar_resposta_api(resposta):
        return ""

    return limpar_texto(resposta.text)


def mensagem_de_conexao():
    """Mensagem sobre conexão."""
    return "Conexão com o serviço de IA configurada."


def mensagem_sem_conexao():
    """Mensagem sem conexão."""
    return "O serviço de IA não está configurado."


def status_conexao():
    """Status da conexão."""
    return (
        mensagem_de_conexao()
        if cliente is not None
        else
        mensagem_sem_conexao()
    )


def mostrar_status_conexao():
    """Mostra status da conexão."""
    st.caption(status_conexao())


def numero_seguro(valor, padrao=0):
    """Converte valor para número."""
    try:
        return int(valor)
    except (TypeError, ValueError):
        return padrao


def float_seguro(valor, padrao=0.0):
    """Converte valor para float."""
    try:
        return float(valor)
    except (TypeError, ValueError):
        return padrao


def limitar_numero(valor, minimo, maximo):
    """Limita número a intervalo."""
    valor = float_seguro(valor, minimo)

    return max(
        minimo,
        min(maximo, valor),
    )


def criatividade_atual():
    """Retorna criatividade atual."""
    return limitar_numero(
        st.session_state.temperatura,
        0.0,
        1.0,
    )


def ajustar_criatividade(valor):
    """Ajusta criatividade."""
    st.session_state.temperatura = limitar_numero(
        valor,
        0.0,
        1.0,
    )


def modo_rapido_ativo():
    """Verifica modo rápido."""
    return bool(
        st.session_state.modo_rapido
    )


def dicas_ativas():
    """Verifica dicas."""
    return bool(
        st.session_state.mostrar_dicas
    )


def alternar_modo_rapido():
    """Alterna modo rápido."""
    st.session_state.modo_rapido = (
        not st.session_state.modo_rapido
    )


def alternar_dicas():
    """Alterna dicas."""
    st.session_state.mostrar_dicas = (
        not st.session_state.mostrar_dicas
    )


def conversa_resumida():
    """Retorna resumo curto."""
    if not possui_conversa():
        return "Conversa vazia"

    return (
        f"{quantidade_mensagens_usuario()} perguntas, "
        f"{quantidade_mensagens_assistente()} respostas"
    )


def titulo_sidebar():
    """Título da barra lateral."""
    return "🍊 Serjão Pururucas"


def descricao_sidebar():
    """Descrição da barra lateral."""
    return "Configurações e ferramentas."


def titulo_estatisticas():
    """Título de estatísticas."""
    return "📊 Estatísticas"


def titulo_configuracoes():
    """Título de configurações."""
    return "⚙️ Configurações"


def titulo_exportacao():
    """Título de exportação."""
    return "💾 Exportar"


def titulo_diagnostico():
    """Título de diagnóstico."""
    return "🔧 Diagnóstico"


def botao_nova_conversa():
    """Texto do botão."""
    return "🗑️ Nova conversa"


def botao_download():
    """Texto do download."""
    return "📥 Baixar conversa"


def placeholder_chat():
    """Placeholder do chat."""
    return "Fala aí, manda sua pergunta..."


def placeholder_pergunta():
    """Alias do placeholder."""
    return placeholder_chat()


def limite_pergunta():
    """Limite de pergunta."""
    return 12000


def limite_historico():
    """Limite de histórico."""
    return 30


def limite_resposta_exportacao():
    """Limite de exportação."""
    return 1000000


def constantes_app():
    """Retorna constantes principais."""
    return {
        "nome": APP_NAME,
        "icone": APP_ICON,
        "modelo": MODEL_NAME,
        "limite_pergunta": limite_pergunta(),
        "limite_historico": limite_historico(),
    }


def validar_constantes():
    """Verifica constantes principais."""
    dados = constantes_app()

    return all(
        valor is not None
        for valor in dados.values()
    )


def pronto_para_uso():
    """Verifica se o app pode operar."""
    return (
        validar_constantes()
        and cliente is not None
    )


def mensagem_pronto():
    """Mensagem de app pronto."""
    return "🍊 Serjão está pronto."


def mensagem_pendente():
    """Mensagem de app pendente."""
    return "⚠️ O Serjão precisa de configuração."


def mensagem_status():
    """Mensagem de status."""
    return (
        mensagem_pronto()
        if pronto_para_uso()
        else
        mensagem_pendente()
    )


def obter_nome_usuario():
    """Retorna nome genérico do usuário."""
    return "Usuário"


def nome_assistente():
    """Retorna nome do assistente."""
    return APP_NAME


def papel_usuario():
    """Papel do usuário."""
    return "user"


def papel_assistente():
    """Papel do assistente."""
    return "assistant"


def papéis_validos():
    """Papéis aceitos."""
    return [
        papel_usuario(),
        papel_assistente(),
    ]


def papel_valido(papel):
    """Verifica papel."""
    return papel in papéis_validos()


def mensagem_vazia(mensagem):
    """Verifica mensagem vazia."""
    return not mensagem.get("content", "").strip()


def filtrar_mensagens_vazias():
    """Remove mensagens sem conteúdo."""
    st.session_state.mensagens = [
        mensagem
        for mensagem in st.session_state.mensagens
        if not mensagem_vazia(mensagem)
    ]


def preparar_historico():
    """Prepara histórico antes de uso."""
    preparar_historico_final()
    filtrar_mensagens_vazias()


def pronto_para_pergunta(pergunta):
    """Valida pergunta final."""
    valido, _ = validar_pergunta(pergunta)
    return valido


def mensagem_validacao(pergunta):
    """Retorna mensagem de validação."""
    valido, resultado = validar_pergunta(pergunta)

    if valido:
        return resultado

    return resultado


def resumo_configuracao():
    """Resumo de configuração."""
    return (
        f"Modelo: {MODEL_NAME}\n"
        f"Criatividade: {criatividade_atual():.1f}\n"
        f"Modo rápido: {modo_rapido_ativo()}\n"
        f"Dicas: {dicas_ativas()}"
    )


def mostrar_resumo_configuracao():
    """Mostra resumo."""
    with st.expander("⚙️ Resumo da configuração"):
        st.code(
            resumo_configuracao(),
            language="text",
        )


def gerar_nome_sessao():
    """Nome da sessão."""
    return construir_titulo_conversa()


def info_sessao():
    """Informações da sessão."""
    return {
        "nome": gerar_nome_sessao(),
        "id": garantir_id_chat(),
        "criada": st.session_state.chat_id,
    }


def info_sessao_texto():
    """Informações da sessão em texto."""
    dados = info_sessao()

    return (
        f"Nome: {dados['nome']}\n"
        f"ID: {dados['id']}"
    )


def mostrar_info_sessao():
    """Mostra info da sessão."""
    with st.expander("🧾 Sessão"):
        st.code(
            info_sessao_texto(),
            language="text",
        )


def criar_resposta_status():
    """Resposta de status."""
    return {
        "status": status_texto(),
        "modelo": MODEL_NAME,
        "hora": hora_atual(),
    }


def resposta_status_texto():
    """Status em texto."""
    dados = criar_resposta_status()

    return (
        f"Status: {dados['status']}\n"
        f"Modelo: {dados['modelo']}\n"
        f"Hora: {dados['hora']}"
    )


def mostrar_resposta_status():
    """Mostra status detalhado."""
    with st.expander("📡 Status"):
        st.code(
            resposta_status_texto(),
            language="text",
        )


def criar_menu_recursos():
    """Menu interno de recursos."""
    return [
        {
            "nome": "Chat",
            "ativo": True,
        },
        {
            "nome": "Histórico",
            "ativo": True,
        },
        {
            "nome": "Exportação",
            "ativo": True,
        },
        {
            "nome": "Configurações",
            "ativo": True,
        },
    ]


def recursos_ativos():
    """Retorna recursos ativos."""
    return [
        recurso
        for recurso in criar_menu_recursos()
        if recurso["ativo"]
    ]


def quantidade_recursos_ativos():
    """Conta recursos ativos."""
    return len(recursos_ativos())


def recursos_texto():
    """Lista recursos."""
    return "\n".join(
        recurso["nome"]
        for recurso in recursos_ativos()
    )


def mostrar_recursos():
    """Mostra recursos."""
    with st.expander("🧩 Recursos"):
        st.code(
            recursos_texto(),
            language="text",
        )


def construir_mensagem_sistema():
    """Retorna instrução do sistema."""
    return SYSTEM_INSTRUCTION.strip()


def tamanho_instrucoes():
    """Tamanho da instrução."""
    return len(
        construir_mensagem_sistema()
    )


def modelo_tem_nome():
    """Verifica modelo."""
    return bool(MODEL_NAME.strip())


def configuracao_basica_valida():
    """Configuração básica."""
    return (
        modelo_tem_nome()
        and tamanho_instrucoes() > 0
    )


def diagnostico_basico():
    """Diagnóstico básico."""
    return {
        "modelo_valido": modelo_tem_nome(),
        "instrucoes_validas": (
            tamanho_instrucoes() > 0
        ),
        "api": estado_api(),
        "historico": validar_todas_mensagens(),
    }


def diagnostico_basico_texto():
    """Diagnóstico em texto."""
    dados = diagnostico_basico()

    return "\n".join(
        f"{chave}: {valor}"
        for chave, valor in dados.items()
    )


def mostrar_diagnostico_basico():
    """Mostra diagnóstico."""
    with st.expander("🩺 Diagnóstico básico"):
        st.code(
            diagnostico_basico_texto(),
            language="text",
        )


def obter_nome_modelo():
    """Nome do modelo."""
    return MODEL_NAME


def obter_nome_sistema():
    """Nome do sistema."""
    return APP_NAME


def obter_versao_interface():
    """Versão da interface."""
    return "1.0"


def informacoes_versao():
    """Informações de versão."""
    return (
        f"{APP_NAME} - interface "
        f"{obter_versao_interface()}"
    )


def mostrar_versao():
    """Mostra versão."""
    st.caption(informacoes_versao())


def criar_identificador_evento():
    """Identificador de evento."""
    return datetime.now().strftime(
        "%Y%m%d%H%M%S%f"
    )


def evento_generico(tipo):
    """Evento genérico."""
    return {
        "id": criar_identificador_evento(),
        "tipo": tipo,
        "hora": hora_atual(),
    }


def registrar_evento_generico(tipo):
    """Registra evento genérico."""
    registrar_evento(
        tipo,
        {"id": criar_identificador_evento()},
    )


def eventos_ativos():
    """Eventos ativos."""
    return obter_eventos()


def total_eventos():
    """Total de eventos."""
    return quantidade_eventos()


def limpar_estado_eventos():
    """Limpa estado de eventos."""
    limpar_eventos()


def garantir_estado_eventos():
    """Garante estado de eventos."""
    if "eventos" not in st.session_state:
        st.session_state.eventos = []


def preparar_eventos():
    """Prepara eventos."""
    garantir_estado_eventos()


def preparar_aplicativo():
    """Preparação geral."""
    executar_preparacao_completa()
    preparar_eventos()


def aplicativo_nome():
    """Nome público."""
    return APP_NAME


def aplicativo_icone():
    """Ícone público."""
    return APP_ICON


def aplicativo_modelo():
    """Modelo público."""
    return MODEL_NAME


def aplicativo_status():
    """Status público."""
    return status_texto()


def aplicativo_resumo():
    """Resumo público."""
    return (
        f"{aplicativo_icone()} "
        f"{aplicativo_nome()} — "
        f"{aplicativo_status()}"
    )


def exibir_resumo_publico():
    """Exibe resumo público."""
    st.caption(aplicativo_resumo())


def pode_mostrar_exportacao():
    """Pode mostrar exportação."""
    return exportacao_disponivel()


def pode_mostrar_estatisticas():
    """Pode mostrar estatísticas."""
    return possui_conversa()


def executar_rotina_final():
    """Rotina final de preparação."""
    preparar_aplicativo()
    preparar_historico()


# ============================================================
# FIM DAS FUNÇÕES AUXILIARES
# ============================================================


# ============================================================
# VERIFICAÇÃO FINAL DO ESTADO
# ============================================================

# Estas chamadas são seguras e apenas organizam o estado da sessão.
executar_rotina_final()

# O aplicativo principal já foi renderizado acima.
# As funções adicionais ficam disponíveis para futuras melhorias.

