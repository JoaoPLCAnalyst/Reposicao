import streamlit as st
import urllib.parse
import os
import base64
from typing import Optional

def _local_image_to_data_uri(path: str) -> Optional[str]:
    try:
        if not path: return None
        # Se for um caminho relativo, completa com o diretório atual
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        if not os.path.exists(path): return None
        
        ext = os.path.splitext(path)[1].lower()
        mime = "image/png" if ext == ".png" else "image/jpeg"
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    except: return None

def render_catalog_card(slug: str,
                        cliente_name: str,
                        preview_title: str,
                        qtd_pecas: int,
                        preview_img: Optional[str] = None,
                        is_new: bool = False):
    
    # CSS para o Card com Corte Diagonal
    st.markdown("""
        <style>
        .card-container {
            display: flex;
            background: white;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            overflow: hidden;
            border: 1px solid #eee;
            min-height: 160px;
            font-family: 'Inter', sans-serif;
        }
        .card-content {
            flex: 1;
            padding: 20px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .card-title { color: #002d4b; font-size: 1.2rem; font-weight: 700; margin: 0; }
        .card-sub { color: #666; font-size: 0.85rem; margin-top: 4px; }
        .card-qty { color: #333; font-size: 0.9rem; margin: 12px 0; font-weight: 600; }
        
        .card-btn {
            background: #2e6d5a; /* Verde da imagem */
            color: white !important;
            text-decoration: none;
            padding: 8px 18px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.85rem;
            width: fit-content;
            transition: 0.3s;
        }

        .card-image-side {
            flex: 0 0 42%;
            position: relative;
            background-color: #f8f9fa;
        }
        .img-cut {
            width: 100%;
            height: 100%;
            object-fit: cover;
            /* O CORTE DIAGONAL */
            clip-path: polygon(18% 0, 100% 0, 100% 100%, 0% 100%);
        }
        .badge-new {
            position: absolute;
            top: 12px;
            right: 12px;
            background: #f4d36f;
            color: #333;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 800;
            z-index: 10;
        }
        </style>
    """, unsafe_allow_html=True)

    # Processa a imagem (URL ou Local)
    img_display = ""
    if preview_img:
        if preview_img.startswith(("http", "https")):
            img_display = preview_img
        else:
            img_display = _local_image_to_data_uri(preview_img) or ""

    badge_html = '<div class="badge-new">NOVO</div>' if is_new else ''
    href = f"?cliente={urllib.parse.quote(slug)}"

    html = f"""
    <div class="card-container">
        <div class="card-content">
            <h3 class="card-title">{cliente_name}</h3>
            <p class="card-sub">{preview_title}</p>
            <p class="card-qty"><strong>{qtd_pecas}</strong> produtos</p>
            <a href="{href}" target="_self" class="card-btn">Ver catálogo</a>
        </div>
        <div class="card-image-side">
            {badge_html}
            <img src="{img_display}" class="img-cut">
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)