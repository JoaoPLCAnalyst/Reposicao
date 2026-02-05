import streamlit as st
import os
import urllib.parse

def _is_url(s):
    return isinstance(s, str) and (s.startswith("http://") or s.startswith("https://"))

def render_catalog_card(slug: str, cliente_name: str, qtd_pecas: int, preview_img: str = None, preview_title: str = "", key_suffix: str = ""):
    """
    Renderiza um card de catálogo com imagem à esquerda, título, meta e botão.
    - slug: identificador do cliente (usado para keys)
    - cliente_name: nome exibido do catálogo
    - qtd_pecas: número de itens no catálogo
    - preview_img: URL ou caminho local da imagem do primeiro item
    - preview_title: texto pequeno abaixo do meta
    - key_suffix: sufixo para keys de botões (evita colisão)
    """
    # monta HTML do card
    if preview_img:
        img_src = preview_img
        card_html = f"""
        <div class="card">
          <div class="card-thumb">
            <img src="{img_src}" alt="thumb" />
          </div>
          <div class="card-body">
            <div class="card-title">{cliente_name}</div>
            <div class="card-meta">Itens no catálogo: <strong>{qtd_pecas}</strong></div>
            <div class="card-sub">{preview_title}</div>
            <div class="card-actions">
              <a class="open-btn" href="javascript:void(0)" id="open_{slug}_{key_suffix}">Abrir Catálogo</a>
            </div>
          </div>
        </div>
        """
    else:
        initials = (cliente_name[:2] or "CL").upper()
        card_html = f"""
        <div class="card">
          <div class="card-thumb">
            <div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#6b7280;font-weight:700">{initials}</div>
          </div>
          <div class="card-body">
            <div class="card-title">{cliente_name}</div>
            <div class="card-meta">Itens no catálogo: <strong>{qtd_pecas}</strong></div>
          </div>
        </div>
        """

    st.markdown(card_html, unsafe_allow_html=True)

    # botão funcional do Streamlit (ação real)
    btn_key = f"open_{slug}_{key_suffix}"
    if st.button("Abrir Catálogo", key=btn_key):
        # devolve True para o chamador saber que foi clicado
        return True
    return False
