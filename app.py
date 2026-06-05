import streamlit as pd_st
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import io
import hashlib
from st_supabase_connection import SupabaseConnection

# 1. CONFIGURATION DE LA PAGE
pd_st.set_page_config(page_title="Salle Victoria - Management", layout="wide", page_icon="🏢")

# --- CONNEXION SUPABASE ---
conn = pd_st.connection("supabase", type=SupabaseConnection)

# --- FONCTION DE REQUÊTE UNIFIÉE (POSTGRESQL) ---
def query_db(query, params=(), is_select=True):
    if is_select:
        try:
            response = conn.query(query, params=params)
            if response and hasattr(response, 'data') and response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        except Exception as e:
            pd_st.error(f"Erreur de lecture : {e}")
            return pd.DataFrame()
    else:
        try:
            conn.execute(query, params=params)
            return True
        except Exception as e:
            pd_st.error(f"Erreur d'écriture : {e}")
            return False

# --- CHARTE GRAPHIQUE COMPLÈTE ---
COLOR_PRIMARY = "#1E293B"  
COLOR_CARD_BG = "#F8FAFC"   
COLOR_REVENUE = "#10B981"  
COLOR_EXPENSE = "#EF4444"  

# --- INJECTION DU DESIGN CSS ---
pd_st.markdown(f"""
    <style>
        .top-navbar {{
            position: fixed; top: 0; left: 0; width: 100%;
            background-color: {COLOR_PRIMARY}; color: white; text-align: center;
            padding: 15px 0; font-size: 22px; font-weight: 700; z-index: 9999;
            box-shadow: 0 4px 6px rgb(0 0 0 / 0.1); letter-spacing: 1px;
        }}
        .stApp {{ margin-top: 50px !important; }}
        .main {{ background-color: #FFFFFF; }}
        .kpi-card {{
            background-color: {COLOR_CARD_BG}; padding: 24px; border-radius: 12px;
            border-left: 5px solid #64748B; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05); margin-bottom: 15px;
        }}
        .kpi-revenue {{ border-left-color: {COLOR_REVENUE}; }}
        .kpi-expense {{ border-left-color: {COLOR_EXPENSE}; }}
        .kpi-solde {{ border-left-color: #3B82F6; }}
        .kpi-title {{ color: #64748B; font-size: 14px; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }}
        .kpi-value {{ color: #0F172A; font-size: 28px; font-weight: 700; }}
        h1, h2, h3 {{ color: #1E293B !important; font-weight: 700 !important; }}
        .user-badge {{
            background-color: #F1F5F9; padding: 10px; border-radius: 8px;
            text-align: center; margin-bottom: 10px; border: 1px solid #E2E8F0;
            color: #334155; font-weight: 600;
        }}
    </style>
""", unsafe_allow_html=True)

# --- GESTION DE LA SESSION ---
if 'logged_in' not in pd_st.session_state:
    pd_st.session_state['logged_in'] = False
if 'username' not in pd_st.session_state:
    pd_st.session_state['username'] = ""

def login_user(username, password):
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    res = query_db("SELECT * FROM users WHERE username = %s AND password = %s", (username, hashed_pw))
    return not res.empty

# --- ÉCRAN DE CONNEXION ---
if not pd_st.session_state['logged_in']:
    col_l1, col_l2, col_l3 = pd_st.columns([1, 1.5, 1])
    with col_l2:
        pd_st.markdown("<br><br><br>", unsafe_allow_html=True)
        pd_st.markdown("<div style='text-align: center;'><h1>🏢 Salle Victoria</h1><p style='color:#64748B;'>Système de Gestion Sécurisé</p></div>", unsafe_allow_html=True)
        with pd_st.container():
            pd_st.markdown("<div style='background-color:#F8FAFC; padding:30px; border-radius:12px; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);'>", unsafe_allow_html=True)
            input_user = pd_st.text_input("Identifiant")
            password = pd_st.text_input("Mot de passe", type="password")
            btn_connect = pd_st.button("Se connecter", use_container_width=True)
            pd_st.markdown("</div>", unsafe_allow_html=True)
            if btn_connect:
                if login_user(input_user, password):
                    pd_st.session_state['logged_in'] = True
                    pd_st.session_state['username'] = input_user
                    pd_st.success("Connexion réussie !")
                    pd_st.rerun()
                else:
                    pd_st.error("Identifiant ou mot de passe incorrect.")
    pd_st.stop()

# --- APPLICATION PRINCIPALE ---
pd_st.markdown('<div class="top-navbar">⚙️ GESTION SÉCURISÉE - SALLE VICTORIA</div>', unsafe_allow_html=True)
pd_st.sidebar.markdown(f'<div class="user-badge">👤 Administrateur : {pd_st.session_state["username"].upper()}</div>', unsafe_allow_html=True)

if pd_st.sidebar.button("🚪 Déconnexion", use_container_width=True):
    pd_st.session_state['logged_in'] = False
    pd_st.session_state['username'] = ""
    pd_st.rerun()

pd_st.sidebar.markdown("---")

menu = pd_st.sidebar.radio("Navigation Principale", [
    "Tableau de Bord", 
    "Reservations", 
    "Recus et Paiements", 
    "Gestion des Depenses", 
    "Comptabilite et Rapports"
])

# Chargement global des données
df_res = query_db("SELECT * FROM reservations")
df_rec = query_db("SELECT * FROM receipts")
df_exp = query_db("SELECT * FROM expenses")

# --- 1. TABLEAU DE BORD ---
if menu == "Tableau de Bord":
    pd_st.title("📊 Tableau de Bord")
    pd_st.markdown("Suivi en temps réel de l'activité.")
    
    # Calcul des KPIs Globaux
    total_rec = df_rec['amount'].sum() if not df_rec.empty else 0.0
    total_exp = df_exp['amount'].sum() if not df_exp.empty else 0.0
    solde = total_rec - total_exp
    
    c1, c2, c3 = pd_st.columns(3)
    with c1:
        pd_st.markdown(f'<div class="kpi-card kpi-revenue"><div class="kpi-title">Recettes Totales</div><div class="kpi-value">{total_rec:,.2f} $</div></div>', unsafe_allow_html=True)
    with c2:
        pd_st.markdown(f'<div class="kpi-card kpi-expense"><div class="kpi-title">Dépenses Totales</div><div class="kpi-value">{total_exp:,.2f} $</div></div>', unsafe_allow_html=True)
    with c3:
        pd_st.markdown(f'<div class="kpi-card kpi-solde"><div class="kpi-title">Solde de Caisse</div><div class="kpi-value">{solde:,.2f} $</div></div>', unsafe_allow_html=True)

    if not df_res.empty:
        pd_st.subheader("📈 Évolution des réservations")
        fig = px.histogram(df_res, x="date_event", color="status", barmode="group", title="Réservations par Date")
        pd_st.plotly_chart(fig, use_container_width=True)

# --- 2. RESERVATIONS ---
elif menu == "Reservations":
    pd_st.title("📅 Gestion des Réservations")
    
    with pd_st.expander("➕ Enregistrer une nouvelle réservation", expanded=False):
        with pd_st.form("form_res"):
            client = pd_st.text_input("Nom du Client")
            date_ev = pd_st.date_input("Date de l'événement", date.today())
            event_name = pd_st.text_input("Type d'événement (Mariage, Conférence, etc.)")
            status = pd_st.selectbox("Statut Initial", ["Option", "Confirmé", "Annulé"])
            submit = pd_st.form_submit_button("Enregistrer la réservation")
            
            if submit and client and event_name:
                if query_db("INSERT INTO reservations (client, date_event, event_name, status) VALUES (%s, %s, %s, %s)", 
                            (client, str(date_ev), event_name, status), is_select=False):
                    pd_st.success("Réservation ajoutée avec succès !")
                    pd_st.rerun()

    pd_st.subheader("📋 Liste des Réservations")
    if not df_res.empty:
        pd_st.dataframe(df_res, use_container_width=True)
    else:
        pd_st.info("Aucune réservation enregistrée.")

# --- 3. RECUS ET PAIEMENTS ---
elif menu == "Recus et Paiements":
    pd_st.title("💵 Reçus et Encaissements")
    
    if df_res.empty:
        pd_st.warning("Vous devez créer au moins une réservation pour pouvoir enregistrer un reçu de paiement.")
    else:
        with pd_st.expander("➕ Générer un reçu de paiement", expanded=False):
            with pd_st.form("form_rec"):
                # Liaison dynamique avec les réservations existantes
                res_options = {row['id']: f"ID {row['id']} - {row['client']} ({row['event_name']})" for _, row in df_res.iterrows()}
                res_id = pd_st.selectbox("Sélectionner la Réservation", options=list(res_options.keys()), format_func=lambda x: res_options[x])
                
                date_pay = pd_st.date_input("Date de Paiement", date.today())
                amount = pd_st.number_input("Montant Versé ($)", min_value=0.0, step=50.0)
                method = pd_st.selectbox("Mode de paiement", ["Espèces", "Banque", "Mobile Money"])
                ref = pd_st.text_input("Référence de la transaction")
                notes = pd_st.text_area("Notes complémentaires")
                submit = pd_st.form_submit_button("Valider l'encaissement")
                
                if submit and amount > 0:
                    if query_db("INSERT INTO receipts (res_id, date_pay, amount, method, ref, notes) VALUES (%s, %s, %s, %s, %s, %s)", 
                                (int(res_id), str(date_pay), float(amount), method, ref, notes), is_select=False):
                        pd_st.success("Paiement enregistré et reçu généré !")
                        pd_st.rerun()

    pd_st.subheader("📋 Historique des Reçus émis")
    if not df_rec.empty:
        pd_st.dataframe(df_rec, use_container_width=True)
    else:
        pd_st.info("Aucun flux financier entrant enregistré.")

# --- 4. GESTION DES DEPENSES ---
elif menu == "Gestion des Depenses":
    pd_st.title("💸 Gestion des Dépenses (Sorties)")
    
    with pd_st.expander("➕ Enregistrer une nouvelle dépense", expanded=False):
        with pd_st.form("form_exp"):
            category = pd_st.selectbox("Catégorie de Dépense", ["Maintenance", "Personnel", "Électricité/Eau", "Logistique", "Impôts", "Autres"])
