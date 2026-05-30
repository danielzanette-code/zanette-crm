import streamlit as st
from crm_app.auth import render_login
from crm_app.ui import run_app

# login obrigatório antes de qualquer coisa
if not render_login():
    st.stop()

run_app()
