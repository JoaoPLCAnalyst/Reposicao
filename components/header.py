import streamlit as st

def render_header(logo_base64):
    st.markdown(f"""
    <style>
    .header {{
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 15px;
        border-bottom: 2px solid #ddd;
        background-color: #fafafa;
    }}
    .header img {{
        height: 70px;
        margin-right: 15px;
    }}
    .header h1 {{
        font-size: 32px;
        font-weight: 700;
        margin: 0;
    }}
    </style>

    <div class="header">
        <img src="data:image/png;base64,{logo_base64}">
        <h1>ALCAM — Reposição de Peças</h1>
    </div>
    """, unsafe_allow_html=True)
