import streamlit as pd_st
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor
import io

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

# --- 1. TABLEAU DE BORD (AVEC FILTRE MENSUEL AUTOMATIQUE) ---
if menu == "Tableau de Bord":
    pd_st.title("📊 Tableau de Bord")
    pd_st.markdown("Suivi des performances et de la rentabilité de la Salle Victoria.")
    pd_st.markdown("<br>", unsafe_allow_html=True)
    
    # Extraction brute de la base de données
    df_res = query_db("SELECT * FROM reservations")
    df_rec = query_db("SELECT * FROM receipts")
    df_exp = query_db("SELECT * FROM expenses")
    
    # --- FILTRE PAR MOIS ---
    pd_st.subheader("🔍 Période d'analyse")
    
    # Créer une liste unique de tous les mois disponibles dans le système (ex: 2026-06)
    tous_les_mois = set()
    if not df_rec.empty:
        tous_les_mois.update(pd.to_datetime(df_rec['date_pay']).dt.strftime('%Y-%m').tolist())
    if not df_exp.empty:
        tous_les_mois.update(pd.to_datetime(df_exp['date_exp']).dt.strftime('%Y-%m').tolist())
        
    liste_mois = sorted(list(tous_les_mois), reverse=True)
    mois_actuel = datetime.now().strftime('%Y-%m')
    
    # Ajouter le mois en cours par défaut s'il n'y a pas encore d'écriture
    if mois_actuel not in liste_mois:
        liste_mois.insert(0, mois_actuel)
        
    # Interface de filtrage
    col_f1, col_f2 = pd_st.columns(2)
    with col_f1:
        mode_filtre = pd_st.radio("Choisir la vue :", ["Mois en cours / Sélectionné", "Historique Global (Toutes périodes)"], horizontal=True)
    with col_f2:
        selection_mois = pd_st.selectbox("Sélectionner le mois à analyser :", liste_mois, index=liste_mois.index(mois_actuel))
        
    # Application du filtre sur les données
    if mode_filtre == "Mois en cours / Sélectionné":
        pd_st.info(f"📅 Affichage des résultats pour le mois de : **{selection_mois}**")
        if not df_rec.empty:
            df_rec = df_rec[pd.to_datetime(df_rec['date_pay']).dt.strftime('%Y-%m') == selection_mois]
        if not df_exp.empty:
            df_exp = df_exp[pd.to_datetime(df_exp['date_exp']).dt.strftime('%Y-%m') == selection_mois]
        if not df_res.empty:
            df_res = df_res[pd.to_datetime(df_res['date_event']).dt.strftime('%Y-%m') == selection_mois]
    else:
        pd_st.info("🌍 Affichage de l'historique financier global (Cumul de tous les mois)")

    # Calcul des indicateurs filtrés
    total_rev = df_rec['amount'].sum() if not df_rec.empty else 0.0
    total_exp = df_exp['amount'].sum() if not df_exp.empty else 0.0
    solde = total_rev - total_exp
    
    # Affichage des Cartes KPI (Mises à jour selon le filtre)
    pd_st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3, col4 = pd_st.columns(4)
    with col1:
        pd_st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Réservations (Période)</div><div class='kpi-value'>{len(df_res)}</div></div>", unsafe_allow_html=True)
    with col2:
        pd_st.markdown(f"<div class='kpi-card kpi-revenue'><div class='kpi-title'>Revenus (Période)</div><div class='kpi-value'>{total_rev:,.2f} $</div></div>", unsafe_allow_html=True)
    with col3:
        pd_st.markdown(f"<div class='kpi-card kpi-expense'><div class='kpi-title'>Dépenses (Période)</div><div class='kpi-value'>{total_exp:,.2f} $</div></div>", unsafe_allow_html=True)
    with col4:
        pd_st.markdown(f"<div class='kpi-card kpi-solde'><div class='kpi-title'>Solde (Période)</div><div class='kpi-value'>{solde:,.2f} $</div></div>", unsafe_allow_html=True)
    
    # Section Graphique Évolution
    pd_st.markdown("<br>", unsafe_allow_html=True)
    pd_st.subheader("📈 Graphique Comparatif")
    
    # Recharger les données globales uniquement pour le graphique pour toujours voir la tendance
    df_g_rec = query_db("SELECT * FROM receipts")
    df_g_exp = query_db("SELECT * FROM expenses")
    
    if not df_g_rec.empty or not df_g_exp.empty:
        if not df_g_rec.empty:
            df_g_rec['mois'] = pd.to_datetime(df_g_rec['date_pay']).dt.strftime('%Y-%m')
            rev_mensuel = df_g_rec.groupby('mois')['amount'].sum().reset_index().rename(columns={'amount': 'Revenus'})
        else:
            rev_mensuel = pd.DataFrame(columns=['mois', 'Revenus'])
            
        if not df_g_exp.empty:
            df_g_exp['mois'] = pd.to_datetime(df_g_exp['date_exp']).dt.strftime('%Y-%m')
            exp_mensuel = df_g_exp.groupby('mois')['amount'].sum().reset_index().rename(columns={'amount': 'Dépenses'})
        else:
            exp_mensuel = pd.DataFrame(columns=['mois', 'Dépenses'])
            
        df_fusion = pd.merge(rev_mensuel, exp_mensuel, on='mois', how='outer').fillna(0.0)
        df_fusion = df_fusion.sort_values('mois')
        df_fusion['Revenus'] = df_fusion['Revenus'].astype(float)
        df_fusion['Dépenses'] = df_fusion['Dépenses'].astype(float)
        
        fig = px.bar(df_fusion, x='mois', y=['Revenus', 'Dépenses'], barmode='group',
                     color_discrete_map={'Revenus': COLOR_REVENUE, 'Dépenses': COLOR_EXPENSE},
                     template="simple_white",
                     labels={'mois': 'Mois', 'value': 'Montant ($)', 'variable': 'Flux'})
        
        fig.update_layout(margin=dict(l=20, r=20, t=10, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        pd_st.plotly_chart(fig, use_container_width=True)
    else:
        pd_st.info("Aucune transaction enregistrée pour bâtir le graphique.")


# --- 2. GESTION DES RÉSERVATIONS (AVEC STATUT CHRONOLOGIQUE) ---
# --- 2. RESERVATIONS ---
elif menu == "Reservations":
    pd_st.title("📅 Gestion des Réservations")
    
    # Création des deux sous-onglets pour correspondre à votre design visuel
    tab1, tab2 = pd_st.tabs(["🚀 Nouvelle Réservation", "🔍 Liste & Disponibilités"])
    
    with tab1:
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

    with tab2:
        pd_st.subheader("🔍 Filtrer & Rechercher")
        
        # Interface de filtrage par date
        filtre_date = pd_st.date_input("Sélectionnez une date pour filtrer", date.today())
        
        col_btn1, col_btn2 = pd_st.columns(2)
        with col_btn1:
            appliquer_filtre = pd_st.button("🔍 Appliquer le filtre par Date")
        with col_btn2:
            afficher_tout = pd_st.button("🔄 Afficher tout (Retirer le filtre)")
            
        # Logique de chargement des données sans alias de texte buggés (Pas de guillemets simples)
        if appliquer_filtre:
            query = "SELECT id, client, date_event, event_name, status FROM reservations WHERE date_event = %s"
            df_filtre = query_db(query, (str(filtre_date),), is_select=True)
        else:
            query = "SELECT id, client, date_event, event_name, status FROM reservations ORDER BY date_event DESC"
            df_filtre = query_db(query, (), is_select=True)
            
        # Renommage propre des colonnes directement dans Python
        if not df_filtre.empty:
            df_filtre.columns = ["ID", "Client", "Date Événement", "Type d'Événement", "Statut"]
            pd_st.dataframe(df_filtre, use_container_width=True)
            
            # --- BLOC DE TÉLÉCHARGEMENT EXCEL (XLSX) ---
            pd_st.markdown("<br>", unsafe_allow_html=True)
            
            # Conversion du DataFrame en fichier Excel en mémoire (binaire)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_filtre.to_excel(writer, index=False, sheet_name='Réservations')
            buffer.seek(0)
            
            # Création du bouton de téléchargement vert
            pd_st.download_button(
                label="📥 Télécharger la liste en Excel (.xlsx)",
                data=buffer,
                file_name=f"reservations_salle_victoria_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
                    # Requête SQL propre sans alias buggés pour Supabase
        query_hist = """
            SELECT r.id, r.res_id, r.date_pay, r.amount, r.method, r.ref, r.notes 
            FROM receipts r 
            ORDER BY r.date_pay DESC
        """
        df_hist = query_db(query_hist, (), is_select=True)
        
        # Renommage des colonnes géré proprement par Python pour l'affichage
        if not df_hist.empty:
            df_hist.columns = ["N° Reçu", "ID Réservation", "Date de Paiement", "Montant Versé ($)", "Mode de Paiement", "Référence", "Notes"]
            pd_st.dataframe(df_hist, use_container_width=True)
        else:
            pd_st.info("Aucun versement n'a encore été enregistré.")

# --- 3. ENREGISTREMENT & GESTION DES REÇUS ---
# --- 3. ENREGISTREMENT & SUIVI DES AVANCES ET PAIEMENTS ---
# --- 3. RECUS ET PAIEMENTS ---
# --- 3. RECUS ET PAIEMENTS ---
# --- 3. RECUS ET PAIEMENTS ---
elif menu == "Recus et Paiements":
    pd_st.title("💵 Suivi des Avances & Paiements par Tranches")
    
    tab_av1, tab_av2 = pd_st.tabs(["➕ Enregistrer une Avance / Paiement", "📜 Historique complet des Versements"])
    
    with tab_av1:
        if df_res.empty:
            pd_st.warning("Vous devez créer au moins une réservation pour enregistrer un versement.")
        else:
            res_options = {row['id']: f"{row['client']} — {row['event_name']} (ID {row['id']})" for _, row in df_res.iterrows()}
            res_id_sel = pd_st.selectbox("Sélectionner la réservation du client :", options=list(res_options.keys()), format_func=lambda x: res_options[x])
            
            df_total_verse = query_db("SELECT SUM(amount) as total FROM receipts WHERE res_id = %s", (int(res_id_sel),), is_select=True)
            deja_verse = float(df_total_verse['total'].iloc[0]) if not df_total_verse.empty and pd.notna(df_total_verse['total'].iloc[0]) else 0.0
            pd_st.markdown(f"#### 📊 État actuel pour ce client : *Déjà versé au total : {deja_verse:,.2f} $*")
            
            with pd_st.form("form_rec_tranche"):
                date_pay = pd_st.date_input("Date du versement", date.today())
                amount = pd_st.number_input("Montant de cette avance ($)", min_value=0.0, step=50.0)
                method = pd_st.selectbox("Mode de paiement", ["Espèces", "Banque", "Mobile Money"])
                ref = pd_st.text_input("Référence de la transaction")
                notes = pd_st.text_area("Note")
                submit = pd_st.form_submit_button("🔒 Valider le reçu")
                if submit and amount > 0:
                    if query_db("INSERT INTO receipts (res_id, date_pay, amount, method, ref, notes) VALUES (%s, %s, %s, %s, %s, %s)", (int(res_id_sel), str(date_pay), float(amount), method, ref, notes), is_select=False):
                        pd_st.success("Versement enregistré !")
                        pd_st.rerun()

    with tab_av2:
        pd_st.subheader("📜 Historique chronologique de toutes les tranches versées")
        
        # Requête avec JOIN pour récupérer dynamiquement le nom du client et l'événement associé
        query_jointure = """
            SELECT r.id, res.client, res.event_name, r.date_pay, r.amount, r.method, r.ref, r.notes 
            FROM receipts r
            JOIN reservations res ON r.res_id = res.id
            ORDER BY r.date_pay DESC
        """
        df_hist_raw = query_db(query_jointure, (), is_select=True)
        
        if not df_hist_raw.empty:
            # 1. BOUTON TÉLÉCHARGEMENT EXCEL
            buffer_rec = io.BytesIO()
            with pd.ExcelWriter(buffer_rec, engine='openpyxl') as writer:
                df_hist_raw.to_excel(writer, index=False, sheet_name='Versements')
            buffer_rec.seek(0)
            pd_st.download_button(
                label="📥 Télécharger l'historique en Excel (.xlsx)",
                data=buffer_rec,
                file_name=f"versements_victoria_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            pd_st.markdown("---")
            
            pd_st.markdown("💡 *Double-cliquez sur une case pour modifier sa valeur. Cochez 'Supprimer' à droite puis validez.*")
            
            df_hist_raw["Supprimer"] = False
            
            # 2. CONFIGURATION DE L'ÉDITEUR AVEC AFFICHAGE DU CLIENT ET ÉVÉNEMENT
            edited_df = pd_st.data_editor(
                df_hist_raw,
                column_config={
                    "id": pd_st.column_config.NumberColumn("N° Reçu", disabled=True),
                    "client": pd_st.column_config.TextColumn("Nom du Client", disabled=True),
                    "event_name": pd_st.column_config.TextColumn("Événement", disabled=True),
                    "date_pay": "Date de Paiement",
                    "amount": pd_st.column_config.NumberColumn("Montant Versé ($)"),
                    "method": pd_st.column_config.SelectboxColumn("Mode de Paiement", options=["Espèces", "Banque", "Mobile Money"]),
                    "ref": "Référence",
                    "notes": "Notes",
                    "Supprimer": pd_st.column_config.CheckboxColumn("Supprimer ?")
                },
                hide_index=True,
                use_container_width=True,
                key="editor_receipts"
            )
            
            if pd_st.button("💾 Enregistrer les changements (Modifications / Suppressions)"):
                for index, row in edited_df.iterrows():
                    rec_id = int(row['id'])
                    
                    if row['Supprimer']:
                        query_db("DELETE FROM receipts WHERE id = %s", (rec_id,), is_select=False)
                    else:
                        query_db(
                            "UPDATE receipts SET date_pay = %s, amount = %s, method = %s, ref = %s, notes = %s WHERE id = %s",
                            (str(row['date_pay']), float(row['amount']), row['method'], row['ref'], row['notes'], rec_id),
                            is_select=False
                        )
                pd_st.success("Base de données mise à jour avec succès !")
                pd_st.rerun()
        else:
            pd_st.info("Aucun versement enregistré.")



# --- 4. GESTION ET SUIVI DES DÉPENSES ---
elif menu == "Gestion des Depenses":
    pd_st.title("📉 Contrôle & Suivi des Dépenses")
    
    tab_exp1, tab_exp2 = pd_st.tabs(["✨ Enregistrer une Dépense", "🔍 Historique, Actions & Export"])
    
    with tab_exp1:
        # Formulaire d'insertion robuste rattaché à son objet formulaire
        form_exp = pd_st.form(key="form_saisie_depense", clear_on_submit=True)
        form_exp.markdown("### Saisie d'une nouvelle sortie de caisse")
        category = form_exp.selectbox("Rubrique / Catégorie de Charge", ["Énergie", "Entretien", "Fournitures", "Salaire", "Assurances", "Taxes", "Autres"])
        amount = form_exp.number_input("Montant Décaissé ($)", min_value=0.0, step=50.0)
        date_exp = form_exp.date_input("Date comptable de la dépense", value=date.today())
        desc = form_exp.text_input("Bénéficiaire / Motif de la dépense (ex: SNEL, Facture Nettoyage...)")
        status_exp = form_exp.selectbox("Statut du règlement", ["Payé", "En attente"])
        submit_exp = form_exp.form_submit_button("🔒 Valider et comptabiliser la dépense")
        
        if submit_exp:
            if amount > 0 and desc:
                query_db("INSERT INTO expenses (category, amount, date_exp, desc, status) VALUES (?, ?, ?, ?, ?)",
                         (category, amount, str(date_exp), desc, status_exp), is_select=False)
                pd_st.success(f"✅ Dépense de {amount:,.2f} $ enregistrée avec succès pour '{desc}' !")
                pd_st.rerun()
            else:
                form_exp.error("❌ Veuillez saisir un montant supérieur à 0 $ et indiquer un bénéficiaire/motif.")
                
    with tab_exp2:
        pd_st.subheader("📋 Liste des charges de la Salle Victoria")
        
        # Initialisation de l'état du filtre par date pour les dépenses
        if 'filter_date_exp' not in pd_st.session_state:
            pd_st.session_state.filter_date_exp = None
            
        col_sexp1, col_sexp2 = pd_st.columns(2)
        with col_sexp1:
            search_d_exp = pd_st.date_input("Filtrer l'historique par date", value=date.today())
            if pd_st.button("🔍 Filtrer les Dépenses"):
                pd_st.session_state.filter_date_exp = str(search_d_exp)
        with col_sexp2:
            pd_st.markdown("<br>", unsafe_allow_html=True)
            if pd_st.button("🔄 Réinitialiser l'historique"):
                pd_st.session_state.filter_date_exp = None
                pd_st.rerun()
                
        # Extraction brute filtrée ou globale
        if pd_st.session_state.filter_date_exp:
            df_exp_list = query_db("SELECT id as 'ID', category as 'Catégorie', amount as 'Montant ($)', date_exp as 'Date Charge', desc as 'Bénéficiaire/Motif', status as 'État' FROM expenses WHERE date_exp = ? ORDER BY id DESC", (pd_st.session_state.filter_date_exp,))
            pd_st.info(f"Filtre actif : Dépenses enregistrées le {pd_st.session_state.filter_date_exp}")
        else:
            df_exp_list = query_db("SELECT id as 'ID', category as 'Catégorie', amount as 'Montant ($)', date_exp as 'Date Charge', desc as 'Bénéficiaire/Motif', status as 'État' FROM expenses ORDER BY id DESC")
            
        if not df_exp_list.empty:
            # Affichage de la table des dépenses
            pd_st.dataframe(df_exp_list, use_container_width=True, hide_index=True)
            
            # --- EXTRACTION EXCEL DES DÉPENSES ---
            buffer_exp = io.BytesIO()
            with pd.ExcelWriter(buffer_exp, engine='openpyxl') as writer:
                df_exp_list.to_excel(writer, index=False, sheet_name='Charges_Victoria')
                
            pd_st.download_button(
                label="📥 Télécharger le journal des dépenses sous Excel (.xlsx)",
                data=buffer_exp.getvalue(),
                file_name=f"depenses_victoria_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            # --- ACTIONS : MODIFIER / SUPPRIMER UNE DÉPENSE ---
            pd_st.markdown("---")
            pd_st.subheader("🛠️ Actions sur une note de dépense")
            
            # Création d'une description lisible par bénéficiaire et montant pour la liste déroulante
            exp_options = {
                f"ID {row['ID']} — {row['Bénéficiaire/Motif']} ({row['Montant ($)']} $)": row['ID']
                for _, row in df_exp_list.iterrows()
            }
            
            selected_exp_desc = pd_st.selectbox("Sélectionnez la ligne de dépense à traiter", list(exp_options.keys()))
            selected_exp_id = exp_options[selected_exp_desc]
            
            # Charger les données actuelles de la dépense
                        # Charger les données actuelles de la dépense de manière sécurisée (Bloc corrigé)
            df_target_exp = query_db("SELECT * FROM expenses WHERE id = ?", (int(selected_exp_id),))
            
            if not df_target_exp.empty:
                exp_data = df_target_exp.iloc[0] # Correction de l'indexation Pandas
                
                col_exp_act1, col_exp_act2 = pd_st.columns(2)
                
                with col_exp_act1:
                    pd_st.markdown("**✏️ Formulaire de Modification de la Charge**")
                    with pd_st.form(key=f"edit_exp_form_{selected_exp_id}"):
                        categories_dispo = ["Énergie", "Entretien", "Fournitures", "Salaire", "Assurances", "Taxes", "Autres"]
                        idx_cat = categories_dispo.index(exp_data['category']) if exp_data['category'] in categories_dispo else 0
                        
                        edit_cat = pd_st.selectbox("Modifier la Catégorie", categories_dispo, index=idx_cat)
                        edit_amount = pd_st.number_input("Modifier le Montant ($)", min_value=0.0, value=float(exp_data['amount']))
                        edit_desc = pd_st.text_input("Modifier le Motif", value=str(exp_data['desc']))
                        edit_status = pd_st.selectbox("Modifier l'État", ["Payé", "En attente"], index=0 if exp_data['status'] == "Payé" else 1)
                        
                        submit_edit_exp = pd_st.form_submit_button("💾 Enregistrer les modifications de la charge")
                        
                        if submit_edit_exp:
                            query_db("""UPDATE expenses SET category = ?, amount = ?, desc = ?, status = ? 
                                        WHERE id = ?""", 
                                     (edit_cat, edit_amount, edit_desc, edit_status, int(selected_exp_id)), is_select=False)
                            pd_st.success("✅ La note de dépense a été mise à jour avec succès !")
                            pd_st.rerun()
                            
                with col_exp_act2:
                    pd_st.markdown("**❌ Zone de Suppression Définitive**")
                    pd_st.warning(f"Vous allez supprimer définitivement la dépense liée à '{exp_data['desc']}' pour un montant de {exp_data['amount']} $. Cette action ajustera immédiatement le solde du Tableau de Bord.")
                    if pd_st.button("🗑️ Supprimer définitivement cette dépense", use_container_width=True, key=f"del_exp_{selected_exp_id}"):
                        query_db("DELETE FROM expenses WHERE id = ?", (int(selected_exp_id),), is_select=False)
                        pd_st.success("🗑️ Note de dépense supprimée de la base de données !")
                        pd_st.rerun()

# --- 5. COMPTABILITÉ GÉNÉRALE & RAPPORTS CHRONOLOGIQUES ---
elif menu == "Comptabilite et Rapports":
    pd_st.title("🗄️ Grand Livre & Rapports Financiers")
    pd_st.markdown("Analyse des flux de trésorerie, bilans intermédiaires et exports comptables.")
    pd_st.markdown("<br>", unsafe_allow_html=True)
    
    # 1. Extraction brute des flux depuis la base de données
    df_rec = query_db("SELECT date_pay as Date, 'Recette (Avance/Paiement Hall)' as Libellé, amount as Montant, 'Entrant' as Flux FROM receipts")
    df_exp = query_db("SELECT date_exp as Date, category || ' — ' || desc as Libellé, amount as Montant, 'Sortant' as Flux FROM expenses")
    
    # Fusionner les deux tableaux pour créer le Grand Livre historique
        # Fusionner les deux tableaux en réinitialisant les index proprement (Ligne corrigée)
    grand_livre_global = pd.concat([df_rec, df_exp]).sort_values(by="Date", ascending=False).reset_index(drop=True)

    
    if grand_livre_global.empty:
        pd_st.info("Aucun mouvement comptable (revenu ou dépense) trouvé dans le système.")
    else:
        # --- FILTRES DU RAPPORT ---
        pd_st.subheader("📊 Générateur de Rapports")
        type_rapport = pd_st.radio("Sélectionnez la période du rapport :", ["Journalier", "Mensuel", "Annuel", "Grand Livre Complet"], horizontal=True)
        
        aujourdhui = date.today()
        df_rapport = grand_livre_global.copy()
        titre_periode = "Global"
        
        if type_rapport == "Journalier":
            choix_date = pd_st.date_input("Sélectionnez le jour à analyser :", value=aujourdhui)
            df_rapport = df_rapport[df_rapport['Date'] == str(choix_date)]
            titre_periode = f"du Jour {choix_date}"
            
        elif type_rapport == "Mensuel":
            # Récupérer la liste des mois disponibles pour le filtre
            mois_dispo = sorted(list(set(pd.to_datetime(grand_livre_global['Date']).dt.strftime('%Y-%m'))), reverse=True)
            mois_actuel = aujourdhui.strftime('%Y-%m')
            if mois_actuel not in mois_dispo:
                mois_dispo.insert(0, mois_actuel)
            choix_mois = pd_st.selectbox("Sélectionnez le mois :", mois_dispo, index=mois_dispo.index(mois_actuel))
            df_rapport = df_rapport[pd.to_datetime(df_rapport['Date']).dt.strftime('%Y-%m') == choix_mois]
            titre_periode = f"du Mois {choix_mois}"
            
        elif type_rapport == "Annuel":
            annees_dispo = sorted(list(set(pd.to_datetime(grand_livre_global['Date']).dt.strftime('%Y'))), reverse=True)
            annee_actuelle = aujourdhui.strftime('%Y')
            if annee_actuelle not in annees_dispo:
                annees_dispo.insert(0, annee_actuelle)
            choix_annee = pd_st.selectbox("Sélectionnez l'année :", annees_dispo, index=annees_dispo.index(annee_actuelle))
            df_rapport = df_rapport[pd.to_datetime(df_rapport['Date']).dt.strftime('%Y') == choix_annee]
            titre_periode = f"de l'Année {choix_annee}"
            
        # --- AFFICHAGE DU COMPTE DE RÉSULTAT DU RAPPORT ---
        pd_st.markdown("---")
        pd_st.markdown(f"### 📋 Rapport Comptable {titre_periode}")
        
        # Séparer les flux entrants et sortants de la période sélectionnée
        produits = df_rapport[df_rapport['Flux'] == 'Entrant']['Montant'].sum()
        charges = df_rapport[df_rapport['Flux'] == 'Sortant']['Montant'].sum()
        resultat_net = produits - charges
        
        # Affichage du bilan intermédiaire sous forme de colonnes épurées
        col_b1, col_b2, col_b3 = pd_st.columns(3)
        with col_b1:
            pd_st.markdown(f"<div class='kpi-card kpi-revenue'><div class='kpi-title'>Total Recettes</div><div class='kpi-value'>{produits:,.2f} $</div></div>", unsafe_allow_html=True)
        with col_b2:
            pd_st.markdown(f"<div class='kpi-card kpi-expense'><div class='kpi-title'>Total Charges</div><div class='kpi-value'>{charges:,.2f} $</div></div>", unsafe_allow_html=True)
        with col_b3:
            if resultat_net >= 0:
                pd_st.markdown(f"<div class='kpi-card kpi-solde'><div class='kpi-title'>Résultat Net (Bénéfice)</div><div class='kpi-value' style='color:{COLOR_REVENUE};'>{resultat_net:,.2f} $</div></div>", unsafe_allow_html=True)
            else:
                pd_st.markdown(f"<div class='kpi-card kpi-solde' style='border-left-color:{COLOR_EXPENSE};'><div class='kpi-title'>Résultat Net (Déficit)</div><div class='kpi-value' style='color:{COLOR_EXPENSE};'>{resultat_net:,.2f} $</div></div>", unsafe_allow_html=True)
                
        # --- TABLEAU ET EXPORTATION ---
        if not df_rapport.empty:
            pd_st.markdown("#### Journal des écritures sur la période")
            
            # Coloration conditionnelle des lignes (Vert pour les entrées, Rouge pour les sorties)
            def colorer_lignes(row):
                back_color = '#E8F5E9' if row['Flux'] == 'Entrant' else '#FFEBEE'
                return [f'background-color: {back_color}'] * len(row)
                
            pd_st.dataframe(df_rapport.style.apply(colorer_lignes, axis=1).format({'Montant': '{:.2f} $'}), use_container_width=True, hide_index=True)
            
            # Génération du fichier Excel personnalisé
            buffer_compta = io.BytesIO()
            with pd.ExcelWriter(buffer_compta, engine='openpyxl') as writer:
                df_rapport.to_excel(writer, index=False, sheet_name='Rapport_Victoria')
                
            pd_st.download_button(
                label=f"📥 Exporter ce rapport {type_rapport.lower()} vers Excel (.xlsx)",
                data=buffer_compta.getvalue(),
                file_name=f"rapport_{type_rapport.lower()}_victoria_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            pd_st.info(f"Aucun mouvement financier n'a été enregistré sur la période sélectionnée ({type_rapport.lower()}).")
