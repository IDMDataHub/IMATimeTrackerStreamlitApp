#####################################################################
# =========================== LIBRAIRIES ========================== #
#####################################################################

import streamlit as st
import pandas as pd
import datetime
import locale
import os
from io import StringIO, BytesIO

#####################################################################
# =========================== CONSTANTES ========================== #
#####################################################################

# Configuration et constantes
DATA_FOLDER = "C:/Users/m.jacoupy/OneDrive - Institut/Documents/3 - Developpements informatiques/IMATimeTrackerStreamlitApp/Data/"
ARC_PASSWORDS_FILE = "ARC_MDP.csv"
ANNEES = list(range(2024, 2030))
TIME_FILES = "Time_{arc}.csv"
CATEGORIES = ['YEAR', 'WEEK', 'STUDY', 'MISE EN PLACE', 'TRAINING', 'VISITES', 'SAISIE CRF', 'QUERIES', 'MONITORING', 'REMOTE', 'REUNIONS', 
'ARCHIVAGE EMAIL', 'MAJ DOC', 'AUDIT & INSPECTION', 'CLOTURE', 'NB_VISITE', 'NB_PAT_SCR', 'NB_PAT_RAN', 'NB_EOS', 'COMMENTAIRE']
INT_CATEGORIES = CATEGORIES[3:-1] 
COLUMN_CONFIG = {
    'YEAR': {"label": 'Année', "description": "Année"},
    'WEEK': {"label": 'Semaine', "description": "Numéro de la semaine"},
    'STUDY': {"label": 'Étude', "description": "Nom de l'étude"},
    'MISE EN PLACE': {"label": 'MEP', "description": "Mise en place"},
    'TRAINING': {"label": 'Form.', "description": "Formation"},
    'VISITES': {"label": 'Vis.', "description": "Organisation des Visites"},
    'SAISIE CRF': {"label": 'CRF', "description": "Saisie CRF"},
    'QUERIES': {"label": 'Quer.', "description": "Queries"},
    'MONITORING': {"label": 'Monit.', "description": "Monitoring"},
    'REMOTE': {"label": 'Remote', "description": "Remote"},
    'REUNIONS': {"label": 'Réunion', "description": "Réunions"},
    'ARCHIVAGE EMAIL': {"label": 'Arch. Email', "description": "Archivage des emails"},
    'MAJ DOC': {"label": 'Maj. Doc', "description": "Mise à jour des documents (ISF & Gaia)"},
    'AUDIT & INSPECTION': {"label": 'Audit & Insp.', "description": "Audit et Inspection"},
    'CLOTURE': {"label": 'Clôture', "description": "Clôture"},
    'NB_VISITE': {"label": 'Nb Visite', "description": "Nombre de visites"},
    'NB_PAT_SCR': {"label": 'Nb Pat. Scr.', "description": "Nombre de patients screenés"},
    'NB_PAT_RAN': {"label": 'Nb Pat. Rand.', "description": "Nombre de patients randomisés"},
    'NB_EOS': {"label": 'Nb EOS.', "description": "Nombre d'EOS"},
    'COMMENTAIRE': {"label": 'Comm.', "description": "Commentaires"}
}


# Chargement des mots de passe ARC
def load_arc_passwords():
    file_path = os.path.join(DATA_FOLDER, ARC_PASSWORDS_FILE)
    df = pd.read_csv(file_path, sep=';')
    return dict(zip(df['ARC'], df['MDP']))

ARC_PASSWORDS = load_arc_passwords()

# Essayer de configurer la locale en français
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR')
except locale.Error:
    st.error("Locale française non disponible sur ce système.")

# Clés pour df1 (de YEAR à CLOTURE)
keys_df_time = list(COLUMN_CONFIG.keys())[:list(COLUMN_CONFIG.keys()).index('CLOTURE')+1]

# Clés pour df2 (YEAR, WEEK, STUDY et NB_VISITE à COMMENTAIRE)
keys_df_quantity = ['YEAR', 'WEEK', 'STUDY'] + list(COLUMN_CONFIG.keys())[list(COLUMN_CONFIG.keys()).index('NB_VISITE'):]

# Création des configurations pour chaque partie
column_config_df_time = {k: COLUMN_CONFIG[k] for k in keys_df_time}
column_config_df_quantity = {k: COLUMN_CONFIG[k] for k in keys_df_quantity}

#####################################################################
# ==================== FONCTIONS D'ASSISTANCES ==================== #
#####################################################################

def load_data(data_folder, arc):
    # Chemin vers le fichier Excel en fonction de l'ARC sélectionné
    csv_file_path = os.path.join(data_folder, f"Time_{arc}.csv")
    try:
        return pd.read_csv(csv_file_path, encoding='utf-8', sep=";")
    except UnicodeDecodeError:
        return pd.read_csv(csv_file_path, encoding='latin1', sep=";")

def authenticate_user(arc, password_entered):
    return ARC_PASSWORDS.get(arc) == password_entered.lower()

def calculate_weeks():
    current_date = datetime.datetime.now()
    current_week = current_date.isocalendar()[1]
    previous_week = current_week - 1 if current_week > 1 else 52
    two_weeks_ago = previous_week - 1 if previous_week > 1 else 52
    next_week = current_week + 1 if current_week < 52 else 1
    current_year = current_date.year
    return two_weeks_ago, previous_week, current_week, next_week, current_year

def save_data(DATA_FOLDER, df, arc):
    csv_file_path = os.path.join(DATA_FOLDER, f"Time_{arc}.csv")
    df.to_csv(csv_file_path, index=False, sep=";", encoding='utf-8')

def load_time_data(arc, week):
    time_file_path = os.path.join(DATA_FOLDER, f"Time_{arc}.csv")
    if os.path.exists(time_file_path):
        df = pd.read_csv(time_file_path, sep=";", encoding='utf-8')
        return df[df['WEEK'] == week]
    else:
        return pd.DataFrame()

def get_start_end_dates(year, week_number):
    # Trouver le premier jour de l'année
    first_day_of_year = datetime.datetime(year-1, 12, 31)
    first_monday_of_year = first_day_of_year + datetime.timedelta(days=(7-first_day_of_year.weekday()))
    week_start_date = first_monday_of_year + datetime.timedelta(weeks=week_number-1)
    week_end_date = week_start_date + datetime.timedelta(days=4)
    return week_start_date, week_end_date

def load_assigned_studies(arc):
    study_file_path = os.path.join(DATA_FOLDER, "STUDY.csv")
    df_study = pd.read_csv(study_file_path, sep=";")
    assigned_studies = df_study[(df_study['ARC'] == arc) | (df_study['ARC_BACKUP'] == arc)]
    return assigned_studies['STUDY'].tolist()

def check_create_weekly_file(arc, year, week):
    file_path = os.path.join(DATA_FOLDER, f"Ongoing_{arc}.csv")
    try:
        if os.path.exists(file_path):
            df_existing = pd.read_csv(file_path, sep=';', encoding='utf-8')
            if not ((df_existing['YEAR'] == year) & (df_existing['WEEK'] == week)).any():
                os.remove(file_path)
                # Créer un nouveau DataFrame avec les mêmes colonnes et le sauvegarder
                df_new = pd.DataFrame(columns=df_existing.columns)
                df_new.to_csv(file_path, index=False, sep=';', encoding='utf-8')
                return file_path
            else:
                return file_path
    except pd.errors.EmptyDataError:
        st.error("Aucune étude n'a été affectées. Merci de voir avec vos managers.")
        # Créer un nouveau DataFrame avec des colonnes par défaut et le sauvegarder
        columns = CATEGORIES

        df_new = pd.DataFrame(columns=columns)
        df_new.to_csv(file_path, index=False, sep=';', encoding='utf-8')
        return None

    assigned_studies = load_assigned_studies(arc)
    rows = [{'YEAR': year, 'WEEK': week, 'STUDY': study, 'MISE EN PLACE': 0, 'TRAINING': 0, 'VISITES': 0, 'SAISIE CRF': 0, 'QUERIES': 0, 
             'MONITORING': 0, 'REMOTE': 0, 'REUNIONS': 0, 'ARCHIVAGE EMAIL': 0, 'MAJ DOC': 0, 'AUDIT & INSPECTION': 0, 'CLOTURE': 0, 
             'NB_VISITE': 0, 'NB_PAT_SCR':0, 'NB_PAT_RAN':0, 'NB_EOS':0, 'COMMENTAIRE': "Aucun"} for study in assigned_studies]
    pd.DataFrame(rows).to_csv(file_path, index=False, sep=";", encoding='utf-8')
    return file_path

# Charger les données hebdomadaires pour l'ARC
def load_weekly_data(file_path):
    if file_path is None:
        # Retourner un DataFrame vide ou gérer comme nécessaire
        return pd.DataFrame()

    return pd.read_csv(file_path, sep=";", encoding='utf-8')

def delete_ongoing_file(arc):
    ongoing_file_path = os.path.join(DATA_FOLDER, f"Ongoing_{arc}.csv")
    if os.path.exists(ongoing_file_path):
        os.remove(ongoing_file_path)

def display_glossary(column_config):
    glossary_html = "<div style='margin-left: 10px;'>"
    for term, config in column_config.items():
        label = config["label"]
        description = config.get("description", "Description non fournie")
        glossary_html += f"<b>{label}</b> : {description}<br>"
    glossary_html += "</div>"
    st.markdown(glossary_html, unsafe_allow_html=True)

#####################################################################
# ====================== FONCTION PRINCIPALE ====================== #
#####################################################################

def main():
    st.set_page_config(layout="wide", page_icon="data/icon.png", page_title="I-Motion Adulte - Espace ARCs")
    st.title("I-Motion Adulte - Espace ARCs")
    st.write("---")

    # Authentification de l'utilisateur
    arc_options = [key for key in ARC_PASSWORDS.keys() if key == key]  # Les NaN ne sont pas égaux à eux-mêmes
    arc = st.sidebar.selectbox("Choisissez votre ARC", sorted(arc_options))
    arc_password_entered = st.sidebar.text_input(f"Entrez le mot de passe", type="password")
    
    if not authenticate_user(arc, arc_password_entered):
        st.sidebar.error("Mot de passe incorrect pour l'ARC sélectionné.")
        return

    with st.sidebar.expander("Glossaire des catégories"):
        display_glossary(COLUMN_CONFIG)

    # I. Chargement des données
    df_data = load_data(DATA_FOLDER, arc)
    two_weeks_ago, previous_week, current_week, next_week, current_year = calculate_weeks()

    # II. Interface utilisateur pour la sélection de l'année et de la semaine
    st.subheader("Visualisation")
    col1, col2 = st.columns([1, 3])
    with col1:
        year_choice = st.selectbox("Année", ANNEES, index=ANNEES.index(datetime.datetime.now().year))
    with col2:
        week_choice = st.slider("Semaine", 1, 52, current_week)

    # Filtrage et manipulation des données
    filtered_df1 = df_data[(df_data['YEAR'] == year_choice) & (df_data['WEEK'] == week_choice)]

    # Convertir certaines colonnes en entiers
    int_columns = INT_CATEGORIES
    filtered_df1[int_columns] = filtered_df1[int_columns].astype(int)

    df_time = filtered_df1[keys_df_time]
    df_quantity = filtered_df1[keys_df_quantity]
    
    # Appliquer le style
    styled_df_time = df_time.style.format({
        "YEAR": "{:.0f}",
        "WEEK": "{:.0f}"
    })
    styled_df_quantity = df_quantity.style.format({
        "YEAR": "{:.0f}",
        "WEEK": "{:.0f}"
    })

    st.markdown('**Partie "Temps"**')
    st.dataframe(styled_df_time, hide_index=True, column_config=column_config_df_time)
    st.markdown('**Partie "Quantité"**')
    st.dataframe(styled_df_quantity, hide_index=True, column_config=column_config_df_quantity)


    # III. Section pour la modification des données
    st.write("---")
    st.subheader("Entrée d'heures")
    
    week_choice2 = st.radio(
        "Choisissez une semaine",
        [f"Deux semaines avant (Semaine {two_weeks_ago})", 
         f"Semaine précédente (Semaine {previous_week})",
         f"Semaine en cours (Semaine {current_week})"],
        index=2)

    # Récupérer la valeur sélectionnée (numéro de la semaine)
    selected_week = int(week_choice2.split()[-1].strip(')'))
    time_df = load_time_data(arc, selected_week)


    if "Semaine précédente" in week_choice2:
        # Charger les données de la semaine précédente à partir de Time_arc.csv
        filtered_df2 = time_df
    else:
        # Charger les données de la semaine en cours à partir de Ongoing_arc.csv
        weekly_file_path = check_create_weekly_file(arc, current_year, current_week)
        filtered_df2 = load_weekly_data(weekly_file_path)

        if not time_df.empty:
            if not time_df[(time_df['YEAR'] == current_year) & (time_df['WEEK'] == current_week)].empty:
                # Il y a des données dans time_df pour l'année et la semaine en cours
                # Fusionner les données
                merged_df = pd.merge(filtered_df2, time_df, on=['YEAR', 'WEEK', 'STUDY'], suffixes=('_ongoing', '_time'), how='outer')
                # Récupérer les études actuellement assignées à cet ARC
                assigned_studies = set(load_assigned_studies(arc))
                merged_df = merged_df[merged_df['STUDY'].isin(assigned_studies)]
                # Remplacer les valeurs dans Ongoing avec celles de Time si elles ne sont pas 0
                columns_to_update = CATEGORIES[3:]
                for col in columns_to_update:
                    merged_df[col + '_ongoing'] = merged_df.apply(
                        lambda row: row[col + '_time'] if not pd.isna(row[col + '_time']) and row[col + '_ongoing'] == 0 else row[col + '_ongoing'], axis=1)

                # Ajouter des lignes pour les nouvelles études assignées manquantes
                for study in assigned_studies:
                    if study not in merged_df['STUDY'].tolist():
                        new_row_data = {'YEAR': current_year, 'WEEK': current_week, 'STUDY': study}
                        new_row_data.update({col + '_ongoing': 0 for col in columns_to_update[:]})
                        new_row_data['COMMENTAIRE_ongoing'] = "Aucun"
                        new_row = pd.DataFrame([new_row_data])
                        merged_df = pd.concat([merged_df, new_row], ignore_index=True)
                # Filtrer les colonnes pour éliminer celles avec '_time'
                filtered_columns = [col for col in merged_df.columns if '_time' not in col]

                # Créer le DataFrame final avec les colonnes filtrées
                final_df = merged_df[filtered_columns]
                filtered_df2 = final_df.rename(columns={col + '_ongoing': col for col in columns_to_update})
    

            else:
                # Il y a des données dans time_df, mais pas pour l'année et la semaine en cours
                filtered_df2 = time_df
        else:
            # time_df est complètement vide
            assigned_studies = set(load_assigned_studies(arc))
            rows = [{'YEAR': current_year, 'WEEK': current_week, 'STUDY': study, 'MISE EN PLACE': 0, 'TRAINING': 0, 'VISITES': 0, 'SAISIE CRF': 0, 'QUERIES': 0, 
             'MONITORING': 0, 'REMOTE': 0, 'REUNIONS': 0, 'ARCHIVAGE EMAIL': 0, 'MAJ DOC': 0, 'AUDIT & INSPECTION': 0, 'CLOTURE': 0, 
             'NB_VISITE': 0, 'NB_PAT_SCR':0, 'NB_PAT_RAN':0, 'NB_EOS':0, 'COMMENTAIRE': "Aucun"} for study in assigned_studies]
            filtered_df2 = pd.DataFrame(rows)
 
    if not filtered_df2.empty:
        filtered_df2['YEAR'] = filtered_df2['YEAR'].astype(str)
        filtered_df2['WEEK'] = filtered_df2['WEEK'].astype(str)

        # Séparer votre DataFrame en deux selon les clés spécifiées
        df_time2 = filtered_df2[keys_df_time]
        df_quantity2 = filtered_df2[keys_df_quantity]

        # Afficher la première partie avec sa configuration de colonne
        st.markdown('**Partie "Temps"**')
        df1_edited = st.data_editor(
            data=df_time2,
            hide_index=True,
            disabled=["YEAR", "WEEK", "STUDY"],
            column_config=column_config_df_time  # Utilisez votre configuration de colonne spécifique ici
        )

        # Afficher la seconde partie avec sa configuration de colonne
        st.markdown('**Partie "Quantité"**')
        df2_edited = st.data_editor(
            data=df_quantity2,
            hide_index=True,
            disabled=["YEAR", "WEEK", "STUDY"],
            column_config=column_config_df_quantity  # Utilisez votre configuration de colonne spécifique ici
        )

    else:
        st.write("Aucune donnée disponible pour la semaine sélectionnée.")
    
    # V. Bouton de sauvegarde
    if st.button("Sauvegarder"):

        # Retirer les anciennes données de la semaine sélectionnée
        df_data = df_data[df_data['WEEK'] != int(selected_week)]

        # Assurez-vous que 'YEAR', 'WEEK', 'STUDY' sont présents dans les deux DataFrames pour l'alignement
        df1_edited = df1_edited.set_index(['YEAR', 'WEEK', 'STUDY'])
        df2_edited = df2_edited.set_index(['YEAR', 'WEEK', 'STUDY'])

        # Concaténation des deux DataFrames sur l'axe des colonnes
        df = pd.concat([df1_edited, df2_edited], axis=1)

        # Réinitialiser l'indice si nécessaire
        df.reset_index(inplace=True)

        # Concaténer avec les nouvelles données
        updated_df = pd.concat([df_data, df]).sort_index()

        # Sauvegarder le DataFrame mis à jour
        save_data(DATA_FOLDER, updated_df, arc)

        # Supprimer le fichier Ongoing_ARC.csv
        delete_ongoing_file(arc)

        st.success("Les données ont été sauvegardées et le fichier temporaire a été supprimé.")

        # Recharger la page
        st.rerun()

#####################################################################
# ====================== LANCEMENT DE L'ALGO ====================== #
#####################################################################

if __name__ == "__main__":
    main()
