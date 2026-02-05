# components/catalog_card.py
import streamlit as st
import urllib.parse
import os
import base64
from typing import Optional

DEBUG_SHOW_PATH = False  # Ative para debug de caminhos (True/False)

def _local_image_to_data_uri(path: str) -> Optional[str]:
    """Retorna data URI (base64) para a imagem local ou None se não existir/erro."""
    try:
        if not path:
            return None
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        if not os.path.exists(path):
            return None
        ext = os.path.splitext(path)[1].lower()
        mime = "image/png"
        if ext in [".jpg", ".jpeg"]:
            mime = "image/jpeg"
        elif ext == ".gif":
            mime = "image/gif"
        elif ext == ".webp":
            mime = "image/webp"
        with open(path, "rb") as f:
            b = f.read()
        b64 = base64.b64encode(b).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None

def render_catalog_card(slug: str,
                        cliente_name: str,
                        qtd_pecas: int,
                        preview_img: Optional[str] = None,
                        preview_title: str = "",
                        key_suffix: Optional[str] = None) -> bool:
    """
    Renderiza o card dentro de um elemento pai explicitamente definido (.page-container).
    Não altera o header; define o pai apenas para o card aqui.
    """
    css_key = "_card_html_css_explicit_parent"
    if css_key not in st.session_state:
        st.markdown("""
        <style>
        /* ELEMENTO PAI EXPLÍCITO: controla largura e padding do pai do card */
        .page-container {
            max-width: 3000px;    /* <-- largura explícita do elemento pai */
            margin: 0 auto;       /* centraliza o container na viewport */
            padding: 0 15px;      /* <-- padding lateral explícito (alinha com header) */
            box-sizing: border-box;
        }

        /* Card ocupa 100% da área interna do .page-container */
        .card-html {
            display:flex;
            align-items:stretch;
            justify-content:space-between;
            gap:16px;
            background:#ffffff;
            border-radius:12px;
            padding:0;                 /* sem padding no wrapper do card */
            box-shadow:0 8px 24px rgba(8,54,92,0.06);
            border:1px solid rgba(230,238,248,1);
            box-sizing:border-box;
            width:100%;                /* ocupa 100% da área interna do .page-container */
            margin-bottom:12px;
            overflow:hidden;
            min-height:110px;
        }

        /* conteúdo interno: padding vertical; horizontal já vem do .page-container */
        .card-left {
            flex:1 1 auto;
            min-width:0;
            padding:15px 0;            /* padding vertical; horizontal já aplicado no pai */
            display:flex;
            flex-direction:column;
            justify-content:center;
            gap:6px;
        }

        .card-title { font-weight:700; color:#08365c; margin:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-family:Inter,system-ui,sans-serif; font-size:18px; }
        .card-meta { color:#475569; font-size:13px; margin:0; font-family:Inter,system-ui,sans-serif; }
        .card-sub { color:#6b7280; font-size:13px; margin:6px 0 0 0; font-family:Inter,system-ui,sans-serif; }
        .card-btn { display:inline-block; margin-top:10px; padding:8px 14px; background:#ffffff; color:#08365c; border-radius:8px; border:1px solid rgba(8,54,92,0.06); text-decoration:none; font-weight:700; font-family:Inter,system-ui,sans-serif; }

        .card-thumb {
            flex: 0 0 36%;
            height:100%;
            border-radius:0;
            overflow:hidden;
            background:#f1f5f9 center/cover no-repeat;
            background-size:cover;
            background-position:center;
            clip-path: polygon(12% 0, 100% 0, 100% 100%, 0% 100%);
            -webkit-clip-path: polygon(12% 0, 100% 0, 100% 100%, 0% 100%);
        }

        /* Responsividade */
        @media (max-width:1200px){
            .card-thumb { flex: 0 0 40%; }
            .card-title{ font-size:16px; }
            .card-html { min-height:90px; }
        }
        @media (max-width:700px){
            .page-container { padding: 0 12px; } /* reduz padding em telas pequenas */
            .card-html { flex-direction:column; border-radius:12px; }
            .card-left { padding:12px 0; }
            .card-thumb { width:100%; height:160px; clip-path:none; -webkit-clip-path:none; border-radius:0 0 12px 12px; flex:0 0 auto; }
        }
        </style>
        """, unsafe_allow_html=True)
        st.session_state[css_key] = True

    # prepara atributo de estilo da thumb
    thumb_attr = ""
    if preview_img:
        preview_img = preview_img.strip()
        if preview_img.startswith("http://") or preview_img.startswith("https://"):
            safe = urllib.parse.quote(preview_img, safe=":/?&=#%")
            thumb_attr = f"style=\"background-image:url('{safe}'); background-size:cover; background-position:center;\""
        else:
            data_uri = _local_image_to_data_uri(preview_img)
            if data_uri:
                thumb_attr = f"style=\"background-image:url('{data_uri}'); background-size:cover; background-position:center;\""
            else:
                safe = urllib.parse.quote(preview_img, safe=":/?&=#%")
                thumb_attr = f"style=\"background-image:url('{safe}'); background-size:cover; background-position:center;\""

    href = f"?open={urllib.parse.quote(slug)}"

    if not thumb_attr:
        thumb_div = '<div class="card-thumb" style="background:#e6eef8; display:flex; align-items:center; justify-content:center; color:#6b7280; font-weight:700;">SEM IMAGEM</div>'
    else:
        thumb_div = f'<div class="card-thumb" {thumb_attr}></div>'

    # Renderiza o card DENTRO do elemento pai explícito .page-container
    html = f"""
    <div class="page-container">
      <div class="card-html">
        <div class="card-left">
          <div class="card-title">{cliente_name}</div>
          <div class="card-meta">Itens no catálogo: <strong>{qtd_pecas}</strong></div>
          {"<div class='card-sub'>" + preview_title + "</div>" if preview_title else ""}
          <div><a class="card-btn" href="{href}">Abrir Catálogo</a></div>
        </div>
        {thumb_div}
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    if DEBUG_SHOW_PATH and preview_img:
        abs_path = preview_img if os.path.isabs(preview_img) else os.path.join(os.getcwd(), preview_img)
        exists = os.path.exists(abs_path)
        st.write(f"DEBUG preview_img: {preview_img} | abs_path: {abs_path} | exists: {exists}")

    return False
