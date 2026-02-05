import streamlit as st
import urllib.parse

def render_catalog_card(slug: str, cliente_name: str, qtd_pecas: int,
                        preview_img: str = None, preview_title: str = "") -> None:
    """
    Renderiza um card 100% em HTML (um único retângulo) com:
    - nome, quantidade e botão (link) à esquerda
    - imagem à direita
    O link seta ?open=<slug> na URL para o app principal tratar.
    """
    # injeta CSS uma vez
    if "_card_html_css" not in st.session_state:
        st.markdown("""
        <style>
        .card-html { display:flex; align-items:center; justify-content:space-between; gap:16px;
                     background:#ffffff; border-radius:12px; padding:14px; box-shadow:0 8px 24px rgba(8,54,92,0.06);
                     border:1px solid rgba(230,238,248,1); box-sizing:border-box; width:100%; margin-bottom:12px; }
        .card-left { flex:1; min-width:0; }
        .card-title { font-weight:700; color:#08365c; margin:0 0 6px 0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-family:Inter,system-ui,sans-serif; font-size:18px; }
        .card-meta { color:#475569; font-size:13px; margin:0; font-family:Inter,system-ui,sans-serif; }
        .card-sub { color:#6b7280; font-size:13px; margin:6px 0 0 0; font-family:Inter,system-ui,sans-serif; }
        .card-btn { display:inline-block; margin-top:10px; padding:8px 14px; background:#ffffff; color:#08365c; border-radius:8px; border:1px solid rgba(8,54,92,0.06); text-decoration:none; font-weight:700; font-family:Inter,system-ui,sans-serif; }
        .card-thumb { width:180px; height:110px; border-radius:10px; overflow:hidden; background:#f1f5f9 center/cover no-repeat; border:1px solid rgba(230,238,248,1); flex-shrink:0; }
        @media (max-width:900px){ .card-thumb{ width:120px; height:80px; } .card-title{ font-size:16px; } }
        </style>
        """, unsafe_allow_html=True)
        st.session_state["_card_html_css"] = True

    # prepara thumb style (escapa URL)
    thumb_attr = ""
    if preview_img:
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
