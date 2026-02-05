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
    Renderiza um card full-bleed (vai da borda esquerda à direita da área de conteúdo).
    Mantém a lógica de conversão local->data URI e suporte a URLs externas.
    """
    css_key = "_card_html_css_full_bleed"
    if css_key not in st.session_state:
        st.markdown("""
        <style>
        /* Full-bleed card: compensa o padding do container do Streamlit para ocupar toda a largura */
        .card-html {
            display:flex;
            align-items:stretch;
            gap:16px;
            background:#ffffff;
            border-radius:12px;
            padding:14px;
            box-shadow:0 8px 24px rgba(8,54,92,0.06);
            border:1px solid rgba(230,238,248,1);
            box-sizing:border-box;
            width:calc(100% + 48px);    /* ajuste para compensar padding do container */
            max-width:none;
            margin-left:-24px;          /* desloca para a esquerda */
            margin-right:-24px;         /* desloca para a direita */
            margin-bottom:16px;
            overflow:hidden;
            min-height:120px;
        }

        /* Conteúdo interno com padding apenas na coluna esquerda */
        .card-left {
            flex:1 1 auto;
            min-width:0;
            padding:0 16px 0 16px;
            display:flex;
            flex-direction:column;
            justify-content:center;
            gap:6px;
        }

        .card-title { font-weight:700; color:#08365c; margin:0 0 6px 0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-family:Inter,system-ui,sans-serif; font-size:18px; }
        .card-meta { color:#475569; font-size:13px; margin:0; font-family:Inter,system-ui,sans-serif; }
        .card-sub { color:#6b7280; font-size:13px; margin:6px 0 0 0; font-family:Inter,system-ui,sans-serif; }
        .card-btn { display:inline-block; margin-top:10px; padding:8px 14px; background:#ffffff; color:#08365c; border-radius:8px; border:1px solid rgba(8,54,92,0.06); text-decoration:none; font-weight:700; font-family:Inter,system-ui,sans-serif; }

        /* Thumb ocupa lateral direita, sem radius, encostando nas bordas externas; corte diagonal */
        .card-thumb {
            flex: 0 0 40%;                 /* largura relativa da miniatura */
            height:100%;
            border-radius:0;               /* sem radius para encostar nas bordas externas */
            overflow:hidden;
            background:#f1f5f9 center/cover no-repeat;
            border-left:none;
            display:block;
            background-size:cover;
            background-position:center;
            /* corte diagonal na borda esquerda da thumb */
            clip-path: polygon(12% 0, 100% 0, 100% 100%, 0% 100%);
            -webkit-clip-path: polygon(12% 0, 100% 0, 100% 100%, 0% 100%);
        }

        /* Responsividade: reduz a largura da thumb em telas menores e ajusta compensação */
        @media (max-width:1200px){
            .card-thumb { flex: 0 0 35%; }
            .card-title{ font-size:16px; }
            .card-html { min-height:100px; width:calc(100% + 32px); margin-left:-16px; margin-right:-16px; }
        }
        @media (max-width:700px){
            .card-html { flex-direction:column; width:100%; margin-left:0; margin-right:0; border-radius:12px; }
            .card-left { padding:12px; }
            .card-thumb { flex: 0 0 auto; width:100%; height:160px; clip-path:none; -webkit-clip-path:none; border-radius:0 0 12px 12px; }
        }
        </style>
        """, unsafe_allow_html=True)
        st.session_state[css_key] = True

    # prepara atributo de estilo da thumb com background-size e position
    thumb_attr = ""
    if preview_img:
        preview_img = preview_img.strip()
        if preview_img.startswith("http://") or preview_img.startswith("https://"):
            safe = urllib.parse.quote(preview_img, safe=":/?&=#%")
            thumb_attr = f"style=\"background-image:url('{safe}'); background-size:cover; background-position:center;\""
        else:
            # tenta converter caminho local para data URI (resolve relativo ao cwd)
            data_uri = _local_image_to_data_uri(preview_img)
            if data_uri:
                thumb_attr = f"style=\"background-image:url('{data_uri}'); background-size:cover; background-position:center;\""
            else:
                # fallback: tenta usar o caminho tal qual (útil se a pasta for servida estaticamente)
                safe = urllib.parse.quote(preview_img, safe=":/?&=#%")
                thumb_attr = f"style=\"background-image:url('{safe}'); background-size:cover; background-position:center;\""

    href = f"?open={urllib.parse.quote(slug)}"

    # fallback visual quando não há imagem válida
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

    # debug opcional: mostra se o arquivo existe no caminho resolvido
    if DEBUG_SHOW_PATH and preview_img:
        abs_path = preview_img if os.path.isabs(preview_img) else os.path.join(os.getcwd(), preview_img)
        exists = os.path.exists(abs_path)
        st.write(f"DEBUG preview_img: {preview_img} | abs_path: {abs_path} | exists: {exists}")

    return False
