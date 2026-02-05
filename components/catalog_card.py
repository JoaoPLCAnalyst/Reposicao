import streamlit as st
import os
import urllib.parse

def render_catalog_card(slug: str, cliente_name: str, qtd_pecas: int,
                        preview_img: str = None, preview_title: str = "",
                        key_suffix: str = "") -> bool:
    """
    Renderiza um card de catálogo usando componentes nativos do Streamlit.
    - A imagem é exibida com st.image (funciona para URLs externas e caminhos locais).
    - O botão funcional que abre o catálogo é um st.button branco (comportamento preservado).
    - Retorna True se o botão for clicado.
    """

    # Injeta CSS leve apenas para aparência do card (não estiliza o st.button)
    css_key = "_catalog_card_css_injected"
    if css_key not in st.session_state:
        st.markdown(
            """
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            .wce-card-wrap {
                background: linear-gradient(180deg,#ffffff 0%,#f7fbff 100%);
                border-radius: 12px;
                padding: 10px;
                box-shadow: 0 8px 24px rgba(8,54,92,0.06);
                transition: transform .18s ease, box-shadow .18s ease;
                overflow: hidden;
            }
            .wce-card-wrap:hover { transform: translateY(-4px); box-shadow: 0 14px 40px rgba(8,54,92,0.08); }
            .wce-title { font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; font-size:18px; font-weight:700; color:#08365c; margin:0 0 6px 0; }
            .wce-sub { font-family: 'Inter'; color:#6b7280; font-size:13px; margin:0 0 8px 0; }
            .wce-meta { font-family: 'Inter'; color:#475569; font-size:13px; margin:0; }
            .wce-thumb-fallback {
                width:160px;height:100px;border-radius:10px;background:#f1f5f9;border:1px solid #e6eef8;display:flex;align-items:center;justify-content:center;color:#6b7280;font-weight:700;
            }
            @media (max-width:900px){
                .wce-thumb-fallback { width:120px;height:80px; }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.session_state[css_key] = True

    # Container do card
    with st.container():
        st.markdown('<div class="wce-card-wrap">', unsafe_allow_html=True)
        cols = st.columns([1, 2], gap="small")
        # Coluna da imagem (usa st.image para garantir compatibilidade)
        with cols[0]:
            shown_image = False
            if preview_img and isinstance(preview_img, str):
                src = preview_img.strip()
                # URL externa
                if src.startswith("http://") or src.startswith("https://"):
                    try:
                        st.image(src, width=160, use_column_width=False)
                        shown_image = True
                    except Exception:
                        shown_image = False
                else:
                    # caminho local relativo
                    if os.path.exists(src):
                        try:
                            st.image(src, width=160, use_column_width=False)
                            shown_image = True
                        except Exception:
                            shown_image = False
                    else:
                        # tenta sem leading slash
                        alt = src.lstrip("/")
                        if os.path.exists(alt):
                            try:
                                st.image(alt, width=160, use_column_width=False)
                                shown_image = True
                            except Exception:
                                shown_image = False

            if not shown_image:
                # fallback visual com iniciais
                initials = (cliente_name[:2] or "CL").upper()
                st.markdown(f'<div class="wce-thumb-fallback">{initials}</div>', unsafe_allow_html=True)

        # Coluna do texto e ações (mantemos st.button branco funcional)
        with cols[1]:
            st.markdown(f'<div class="wce-title">{cliente_name}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="wce-meta">Itens no catálogo: <strong>{qtd_pecas}</strong></div>', unsafe_allow_html=True)
            if preview_title:
                st.markdown(f'<div class="wce-sub">{preview_title}</div>', unsafe_allow_html=True)

            # Espaço para ações: usamos st.button (branco padrão do Streamlit) para manter comportamento
            btn_key = f"open_{slug}_{key_suffix}"
            # Pequeno espaçamento visual antes do botão
            st.write("")  # quebra de linha leve
            clicked = st.button("Abrir Catálogo", key=btn_key)
        st.markdown("</div>", unsafe_allow_html=True)

    return clicked
