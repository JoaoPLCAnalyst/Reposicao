import streamlit as st
import urllib.parse

def render_wpp_button(numero: str, mensagem: str):
    mensagem_url = urllib.parse.quote(mensagem)
    link_whatsapp = f"https://wa.me/{numero}?text={mensagem_url}"

    st.markdown("""
        <style>
        .wpp-btn {
            background-color: #25D366;
            color: white !important;
            padding: 12px 20px;
            border-radius: 15px;
            text-decoration: none !important;
            font-weight: bold;
            font-size: 20px;
            display: inline-block;
            margin-top: 15px;
        }
        .wpp-btn:hover {
            background-color: #1ebe5d;
            text-decoration: none !important; 
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <a href="{link_whatsapp}" target="_blank" class="wpp-btn">
            📲 Enviar Pedido via WhatsApp
        </a>
    """, unsafe_allow_html=True)
