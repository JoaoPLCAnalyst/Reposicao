import streamlit as st
import urllib.parse
import os
from typing import List, Dict

# -------------------------
# Render do card (HTML puro)
# -------------------------
def render_catalog_card_html(slug: str, cliente_name: str, qtd_pecas: int,
                             preview_img: str | None = None, preview_title: str = "") -> None:
    """
    Renderiza um card 100% em HTML (um único retângulo) com:
    - nome, quantidade e botão (link) à esquerda
    - imagem à direita
    O link seta ?open=<slug> na URL para o app principal tratar.
    """
    if "_card_html_css" not in st.session_state:
        st.markdown(
            """
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

            .card-html {
                display:flex;
                align-items:center;
                justify-content:space-between;
                gap:16px;
                background:#ffffff;
                border-radius:12px;
                padding:14px;
                box-shadow:0 8px 24px rgba(8,54,92,0.06);
                border:1px solid rgba(230,238,248,1);
                box-sizing:border-box;
                width:100%;
                margin-bottom:12px;
            }
            .card-left { flex:1; min-width:0; }
            .card-title {
                font-weight:700;
                color:#08365c;
                margin:0 0 6px 0;
                white-space:nowrap;
                overflow:hidden;
                text-overflow:ellipsis;
                font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,"Helvetica Neue",Arial;
                font-size:18px;
            }
            .card-meta {
                color:#475569;
                font-size:13px;
                margin:0;
                font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,"Helvetica Neue",Arial;
            }
            .card-sub {
                color:#6b7280;
                font-size:13px;
                margin:6px 0 0 0;
                font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,"Helvetica Neue",Arial;
            }
            .card-btn {
                display:inline-block;
                margin-top:10px;
                padding:8px 14px;
                background:#ffffff;
                color:#08365c;
                border-radius:8px;
                border:1px solid rgba(8,54,92,0.06);
                text-decoration:none;
                font-weight:700;
                font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,"Helvetica Neue",Arial;
            }
            .card-thumb {
                width:180px;
                height:110px;
                border-radius:10px;
                overflow:hidden;
                background:#f1f5f9 center/cover no-repeat;
                border:1px solid rgba(230,238,248,1);
                flex-shrink:0;
            }
            @media (max-width:900px){
                .card-thumb{ width:120px; height:80px; }
                .card-title{ font-size:16px; }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.session_state["_card_html_css"] = True

    thumb_attr = ""
    if preview_img:
        # Escapa a URL para uso em background-image
        safe = urllib.parse.quote(preview_img, safe=":/?&=#%")
        thumb_attr = f"style=\"background-image:url('{safe}');\""

    href = f"?open={urllib.parse.quote(slug)}"

    html = f"""
    <div class="card-html">
      <div class="card-left">
        <div class="card-title">{cliente_name}</div>
        <div class="card-meta">Itens no catálogo: <strong>{qtd_pecas}</strong></div>
        {"<div class='card-sub'>" + preview_title + "</div>" if preview_title else ""}
        <div><a class="card-btn" href="{href}">Abrir Catálogo</a></div>
      </div>
      <div class="card-thumb" {thumb_attr}></div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# --------------------------------
# Função que abre o catálogo (stub)
# --------------------------------
def abrir_catalogo_por_slug(slug: str) -> None:
    """
    Substitua esta função pela lógica real de abertura de catálogo.
    Aqui apenas definimos um estado e exibimos uma mensagem.
    """
    st.session_state["catalogo_aberto"] = slug
    # Exemplo de ação: carregar dados do catálogo, navegar para outra página, etc.
    st.write(f"Abrindo catálogo: {slug}")


# -------------------------
# Exemplo de dados de teste
# -------------------------
def get_catalogos_demo() -> List[Dict]:
    """
    Retorna uma lista de catálogos de exemplo.
    Substitua por sua fonte real (API, DB, arquivo).
    """
    return [
        {"slug": "wce", "cliente": "WCE", "qtd_pecas": 1, "preview_img": "", "preview_title": "soft"},
        {"slug": "alpha", "cliente": "Alpha Co", "qtd_pecas": 12, "preview_img": "https://picsum.photos/320/200?random=1", "preview_title": "Coleção A"},
        {"slug": "bravo", "cliente": "Bravo Ltda", "qtd_pecas": 5, "preview_img": "https://picsum.photos/320/200?random=2", "preview_title": "Novidades"},
    ]


# -------------
# App principal
# -------------
def main():
    st.set_page_config(page_title="Catálogos", layout="wide")
    st.title("Escolha um catálogo para visualizar os itens e fazer pedidos.")

    catalogos = get_catalogos_demo()

    # Renderiza lista de catálogos (cada um como um retângulo HTML)
    for c in catalogos:
        render_catalog_card_html(
            slug=c["slug"],
            cliente_name=c["cliente"],
            qtd_pecas=c["qtd_pecas"],
            preview_img=c.get("preview_img", ""),
            preview_title=c.get("preview_title", ""),
        )

    # Após renderizar, checa query params para abrir catálogo quando link for clicado
    params = st.experimental_get_query_params()
    if "open" in params:
        slug_to_open = params["open"][0]
        # evita re-executar indefinidamente: limpa os params antes de executar ação
        st.experimental_set_query_params()
        # chama a função que abre o catálogo
        abrir_catalogo_por_slug(slug_to_open)

    # Exibe estado atual (opcional, útil para debug)
    if "catalogo_aberto" in st.session_state:
        st.info(f"Catálogo aberto: {st.session_state['catalogo_aberto']}")

    # Botão para limpar estado (útil durante desenvolvimento)
    if st.button("Limpar seleção"):
        if "catalogo_aberto" in st.session_state:
            del st.session_state["catalogo_aberto"]
        st.experimental_rerun()


if __name__ == "__main__":
    main()
