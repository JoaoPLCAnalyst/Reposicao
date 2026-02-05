import streamlit as st
import urllib.parse
import os
import base64
from typing import Optional

DEBUG_SHOW_PATH = False  # Ative para debug de caminhos (True/False)

def _local_image_to_data_uri(path: str) -> Optional[str]:
    """Retorna data URI (base64) para a imagem local ou None se não existir/erro."""
    try:
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
    Renderiza o card mantendo a estrutura original.
    A imagem ocupa toda a lateral direita e tem corte diagonal.
    Retorna False (a ação de abrir catálogo é tratada via query param no app).
    """
    css_key = "_card_html_css"
    if css_key not in st.session_state:
        st.markdown("""
        <style>
        /* wrapper estica para que a thumb ocupe toda a lateral direita */
        .card-html {
            display:flex;
            align-items:stretch;
            justify-content:space-between;
            gap:16px;
            background:#ffffff;
            border-radius:12px;
            padding:0;
            box-shadow:0 8px 24px rgba(8,54,92,0.06);
            border:1px solid rgba(230,238,248,1);
            box-sizing:border-box;
            width:100%;
            margin-bottom:12px;
            overflow:hidden;
            min-height:110px;
        }
        .card-left {
            flex:1 1 auto;
            min-width:0;
            padding:14px;
            display:flex;
            flex-direction:column;
            justify-content:center;
            gap:6px;
        }
        .card-title { font-weight:700; color:#08365c; margin:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-family:Inter,system-ui,sans-serif; font-size:18px; }
        .card-meta { color:#475569; font-size:13px; margin:0; font-family:Inter,system-ui,sans-serif; }
        .card-sub { color:#6b7280; font-size:13px; margin:6px 0 0 0; font-family:Inter,system-ui,sans-serif; }
        .card-btn { display:inline-block; margin-top:10px; padding:8px 14px; background:#ffffff; color:#08365c; border-radius:8px; border:1px solid rgba(8,54,92,0.06); text-decoration:none; font-weight:700; font-family:Inter,system-ui,sans-serif; }

        /* miniatura ocupa toda a lateral direita; clip-path cria o corte diagonal */
        .card-thumb {
            flex: 0 0 40%;               /* largura da miniatura — ajuste aqui se quiser */
            height:100%;
            border-radius:0;
            overflow:hidden;
            background:#f1f5f9 center/cover no-repeat;
            border-left:1px solid rgba(230,238,248,1);
            display:block;
            background-size:cover;
            background-position:center;
            /* diagonal: corta a borda esquerda da miniatura em diagonal */
            clip-path: polygon(12% 0, 100% 0, 100% 100%, 0% 100%);
            -webkit-clip-path: polygon(12% 0, 100% 0, 100% 100%, 0% 100%);
        }

        @media (max-width:900px){
            .card-thumb { flex: 0 0 35%; }
            .card-title{ font-size:16px; }
            .card-html { min-height:90px; }
        }
        </style>
        """, unsafe_allow_html=True)
        st.session_state[css_key] = True

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

    # Se não houver thumb_attr válido, mostra fallback visual
    if not thumb_attr:
        thumb_div = '<div class="card-thumb" style="background:#e6eef8; display:flex; align-items:center; justify-content:center; color:#6b7280; font-weight:700;">SEM IMAGEM</div>'
    else:
        thumb_div = f'<div class="card-thumb" {thumb_attr}></div>'

    html = f"""
    <div class="card-html">
      <div class="card-left">
        <div class="card-title">{cliente_name}</div>
        <div class="card-meta">Itens no catálogo: <strong>{qtd_pecas}</strong></div>
        {"<div class='card-sub'>" + preview_title + "</div>" if preview_title else ""}
        <div><a class="card-btn" href="{href}">Abrir Catálogo</a></div>
      </div>
      {thumb_div}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    if DEBUG_SHOW_PATH and preview_img:
        exists = os.path.exists(preview_img) if os.path.isabs(preview_img) else os.path.exists(os.path.join(os.getcwd(), preview_img))
        st.write(f"DEBUG preview_img: {preview_img} | exists: {exists}")

    return False
