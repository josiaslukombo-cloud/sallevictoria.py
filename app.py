import streamlit as pd_st
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor

pd_st.set_page_config(page_title="Salle Victoria - Management", layout="wide", page_icon="🏢")

def get_db_connection():
    # Connexion directe en utilisant l'URI de vos Secrets Streamlit
    return psycopg2.connect(pd_st.secrets["connection_uri"])

def query_db(query, params=(), is_select=True):
    conn = get_db_connection()
    if is_select:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            data = cursor.fetchall()
            cursor.close()
            conn.close()
            return pd.DataFrame(data) if data else pd.DataFrame()
        except Exception as e:
            pd_st.error(f"Erreur de lecture SQL : {e}")
            conn.close()
            return pd.DataFrame()
    else:
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            pd_st.error(f"Erreur d'écriture SQL : {e}")
            conn.rollback()
            conn.close()
            return False

COLOR_PRIMARY = "#1E293B"  
COLOR_CARD_BG = "#F8FAFC"   
COLOR_REVENUE = "#10B981"  
COLOR_EXPENSE = "#EF4444"  

pd_st.markdown(f"""
    <style>
        .top-navbar {{ position: fixed; top: 0; left: 0; width: 100%; background-color: {COLOR_PRIMARY}; color: white; text-align: center; padding: 15px 0; font-size: 22px; font-weight: 700; z-index: 9999; box-shadow: 0 4px 6px rgb(0 0 0 / 0.1); letter-spacing: 1px; }}
        .stApp {{ margin-top: 50px !important; }}
        .main {{ background-color: #FFFFFF; }}
        .kpi-card {{ background-color: {COLOR_CARD_BG}; padding: 24px; border-radius: 12px; border-left: 5px solid #64748B; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05); margin-bottom: 15px; }}
        .kpi-revenue {{ border-left-color: {COLOR_REVENUE}; }}
        .kpi-expense {{ border-left-color: {COLOR_EXPENSE}; }}
        .kpi-solde {{ border-left-color: #3B82F6; }}
        .kpi-title {{ color: #64748B; font-size: 14px; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }}
        .kpi-value {{ color: #0F172A; font-size: 28px; font-weight: 700; }}
        h1, h2, h3 {{ color: #1E293B !important; font-weight: 700 !important; }}
        .user-badge {{ background-color: #F1F5F9; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px; border: 1px solid #E2E8F0; color: #334155; font-weight: 600; }}
    </style>
""", unsafe_allow_html=True)

if 'logged_in' not in pd_st.session_state:
    pd_st.session_state['logged_in'] = False
if 'username' not in pd_st.session_state:
    pd_st.session_state['username'] = ""

def login_user(username, password):
    # Sécurité absolue : Si la base de données est vide, l'accès fonctionne quand même
    if username == "admin" and password == "admin123":
        # On en profite pour forcer l'insertion dans Supabase en arrière-plan
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        query_db("INSERT INTO users (username, password) VALUES (%s, %s) ON CONFLICT (username) DO NOTHING", (username, hashed_pw), is_select=False)
        return True
        
    # Vérification classique pour les autres comptes s'il y en a
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    res = query_db("SELECT * FROM users WHERE username = %s AND password = %s", (username, hashed_pw))
    return not res.empty


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

df_res = query_db("SELECT * FROM reservations")
df_rec = query_db("SELECT * FROM receipts")
df_exp = query_db("SELECT * FROM expenses")

if menu == "Tableau de Bord":
    pd_st.title("📊 Tableau de Bord")
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
        fig = px.histogram(df_res, x="date_event", color="status", barmode="group", title="Réservations par Date")
        pd_st.plotly_chart(fig, use_container_width=True)

elif menu == "Reservations":
    pd_st.title("📅 Gestion des Réservations")
    with pd_st.expander("➕ Enregistrer une nouvelle réservation"):
        with pd_st.form("form_res"):
            client = pd_st.text_input("Nom du Client")
            date_ev = pd_st.date_input("Date de l'événement", date.today())
            event_name = pd_st.text_input("Type d'événement")
            status = pd_st.selectbox("Statut Initial", ["Option", "Confirmé", "Annulé"])
            submit = pd_st.form_submit_button("Enregistrer")
            if submit and client and event_name:
                if query_db("INSERT INTO reservations (client, date_event, event_name, status) VALUES (%s, %s, %s, %s)", (client, str(date_ev), event_name, status), is_select=False):
                    pd_st.success("Réservation ajoutée !")
                    pd_st.rerun()
    pd_st.dataframe(df_res, use_container_width=True) if not df_res.empty else pd_st.info("Aucune réservation.")

elif menu == "Recus et Paiements":
    pd_st.title("💵 Reçus et Encaissements")
    if df_res.empty:
        pd_st.warning("Créez d'abord une réservation.")
    else:
        with pd_st.expander("➕ Générer un reçu"):
            with pd_st.form("form_rec"):
                res_options = {row['id']: f"ID {row['id']} - {row['client']}" for _, row in df_res.iterrows()}
                res_id = pd_st.selectbox("Réservation", options=list(res_options.keys()), format_func=lambda x: res_options[x])
                date_pay = pd_st.date_input("Date", date.today())
                amount = pd_st.number_input("Montant ($)", min_value=0.0)
                method = pd_st.selectbox("Mode", ["Espèces", "Banque", "Mobile Money"])
                ref = pd_st.text_input("Référence")
                submit = pd_st.form_submit_button("Valider")
                if submit and amount > 0:
                    if query_db("INSERT INTO receipts (res_id, date_pay, amount, method, ref) VALUES (%s, %s, %s, %s, %s)", (int(res_id), str(date_pay), float(amount), method, ref), is_select=False):
                        pd_st.success("Paiement enregistré !")
                        pd_st.rerun()
    pd_st.dataframe(df_rec, use_container_width=True) if not df_rec.empty else pd_st.info("Aucun reçu.")

elif menu == "Gestion des Depenses":
    pd_st.title("💸 Gestion des Dépenses")
    with pd_st.expander("➕ Nouvelle dépense"):
        with pd_st.form("form_exp"):
            category = pd_st.selectbox("Catégorie", ["Maintenance", "Personnel", "Électricité/Eau", "Autres"])
            amount = pd_st.number_input("Montant ($)", min_value=0.0)
            date_exp = pd_st.date_input("Date", date.today())
            desc = pd_st.text_input("Description")
            status = pd_st.selectbox("Statut", ["Payé", "En attente"])
            submit = pd_st.form_submit_button("Enregistrer")
            if submit and amount > 0 and desc:
                if query_db('INSERT INTO expenses (category, amount, date_exp, "desc", status) VALUES (%s, %s, %s, %s, %s)', (category, float(amount), str(date_exp), desc, status), is_select=False):
                    pd_st.success("Dépense enregistrée !")
                    pd_st.rerun()
    pd_st.dataframe(df_exp, use_container_width=True) if not df_exp.empty else pd_st.info("Aucune dépense.")

elif menu == "Comptabilite et Rapports":
    pd_st.title("🗄️ Comptabilité & Rapports")
    total_rec = df_rec['amount'].sum() if not df_rec.empty else 0.0
    total_exp = df_exp['amount'].sum() if not df_exp.empty else 0.0
