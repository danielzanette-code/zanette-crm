import streamlit as st
from crm_app.auth import render_login
from crm_app.security import checar_seguranca
from crm_app.ui import run_app

st.set_page_config(page_title="360 Inteligência de Mercado", page_icon="📊", layout="wide")

# login obrigatório antes de qualquer coisa
if not render_login():
    st.stop()

checar_seguranca()
run_app()
