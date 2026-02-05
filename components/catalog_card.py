import streamlit as st
import base64
import os
from typing import Optional

def _local_image_to_data_uri(path: str) -> Optional[str]:
    try:
        if not path: return ""
        if not os.path.exists(path): return ""
        ext = os.path.splitext(path)[1].lower()
        mime = "image/png" if ext == ".png" else "image/jpeg"
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    except: return ""

def render_catalog_card(slug: str, 
                        cliente_name: str, 
                        qtd_pecas: int, 
                        preview_img: Optional[str], 
                        preview_title: str, 
                        key_suffix: str,
                        is_new: bool = False):
    """
    Componente de Card com corte diagonal sincronizado com os dados do catalogos.py
    """
    # CSS Unificado
    st.markdown("""
        <style>
        .card-container {
            display: flex; background: white; border-radius: 12px;
            margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            overflow: hidden; border: 1px solid #eee; min-height: 155px;
            font-family: 'Inter', sans-serif; position: relative;
        }
        .card-left { flex: 1; padding: 20px; display: flex; flex-direction: column; justify-content: center; }
        .card-title { color: #002d4b; font-size: 1.25rem; font-weight: 700; margin: 0; }
        .card-sub { color: #555; font-size: 0.85rem; margin-top: 5px; line-height: 1.2; }
        .card-qty { color: #333; font-size: 0.9rem; margin: 12px 0; font-weight: 600; }
        .card-btn {
            background: #2e6d5a; color: white !important; padding: 8px 20px;
            border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 0.85rem; width: fit-content;
        }
        .card-right { flex: 0 0 42%; position: relative; background: #f9f9f9; }
        .img-cut {
            width: 100%; height: 100%; object-fit: cover;
            clip-path: polygon(18% 0, 100% 0, 100% 100%, 0% 100%);
        }
        .badge-novo {
            position: absolute; top: 10px; right: 10px; background: #f4d36f;
            color: #222; padding: 3px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 800; z-index: 5;
        }
        </style>
    """, unsafe_allow_html=True)

    # Lógica de Imagem
    display_img = ""
    if preview_img:
        if preview_img.startswith("http"):
            display_img = preview_img
        else:
            display_img = _local_image_to_data_uri(preview_img)
    
    # Se não houver imagem, uma cor neutra aparece
    badge_html = '<div class="badge-novo">NOVO</div>' if is_new else ''
    href = f"?cliente={slug}"

    st.markdown(f"""
        <div class="card-container">
            <div class="card-left">
                <div class="card-title">{cliente_name}</div>
                <div class="card-sub">{preview_title}</div>
                <div class="card-qty">{qtd_pecas} produtos</div>
                <a href="{href}" target="_self" class="card-btn">Ver catálogo</a>
            </div>
            <div class="card-right">
                {badge_html}
                <img src="{display_img}" class="img-cut">
            </div>
        </div>
    """, unsafe_allow_html=True)
    return False