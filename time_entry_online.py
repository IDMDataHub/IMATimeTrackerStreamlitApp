#####################################################################
# =========================== LIBRAIRIES ========================== #
#####################################################################

import streamlit as st
import pandas as pd
import datetime
import locale
import os
import boto3
from io import StringIO, BytesIO


#####################################################################
# =========================== CONSTANTES ========================== #
#####################################################################

# Configuration et constantes
BUCKET_NAME = "bucketidb"
ARC_PASSWORDS_FILE = "ARC_MDP.csv"
ANNEES = list(range(2024, 2030))
CATEGORIES = ['YEAR', 'WEEK', 'STUDY', 'VISITES PATIENT', 'QUERIES', 'SAISIE CRF', 'REUNIONS', 'REMOTE', 'MONITORING', 'TRAINING', 'ARCHIVAGE EMAIL', 'COMMENTAIRE', 'NB_VISITE']
INT_CATEGORIES = CATEGORIES[3:-2] + CATEGORIES[-1:]

s3_client = boto3.client(
    's3',
    aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY']
)

def load_csv_from_s3(bucket_name, file_name, sep=';', encoding='utf-8'):
    # Utilisez boto3 pour accéder à S3 et charger le fichier spécifié
    obj = s3_client.get_object(Bucket=bucket_name, Key=file_name)
    body = obj['Body'].read().decode(encoding)
    
    # Utilisez pandas pour lire le CSV
    data = pd.read_csv(StringIO(body), sep=sep)
    return data

def save_csv_to_s3(df, bucket_name, file_name, sep=';', encoding='utf-8'):
    # Convertir le DataFrame en CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=sep, encoding=encoding)
    
    # Réinitialiser le curseur du buffer au début
    csv_buffer.seek(0)
    
    # Utiliser s3_client pour sauvegarder le fichier CSV dans S3
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer.getvalue())

def load_arc_passwords():
    try:
        # Tentez de charger le fichier avec l'encodage UTF-8
        df = load_csv_from_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        # Si une erreur d'encodage survient, tentez de charger avec l'encodage Latin1
        df = load_csv_from_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, sep=';', encoding='latin1')
    return dict(zip(df['ARC'], df['MDP']))

ARC_PASSWORDS = load_arc_passwords()

# # Essayer de configurer la locale en français
# try:
#     locale.setlocale(locale.LC_TIME, 'fr_FR')
# except locale.Error:
#     st.error("Locale française non disponible sur ce système.")


#####################################################################
# ==================== FONCTIONS D'ASSISTANCES ==================== #
#####################################################################
def load_data(arc):
    file_name = f"Time_{arc}.csv"  # Nom du fichier dans le bucket S3
    try:
        # Tentez de charger le fichier avec l'encodage UTF-8
        return load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        # Si une erreur d'encodage survient, tentez de charger avec l'encodage Latin1
        return load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='latin1')

def authenticate_user(arc, password_entered):
    return ARC_PASSWORDS.get(arc) == password_entered.lower()

def calculate_weeks():
    current_date = datetime.datetime.now()
    current_week = current_date.isocalendar()[1]
    previous_week = current_week - 1 if current_week > 1 else 52
    next_week = current_week + 1 if current_week < 52 else 1
    current_year = datetime.datetime.now().year
    return previous_week, current_week, next_week, current_year

def save_data(df, arc):
    # Création du chemin complet du fichier dans le bucket S3
    file_name = f"Time_{arc}.csv"
    
    # Conversion du DataFrame en chaîne CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=";", encoding='utf-8')
    
    # Réinitialisation de la position du curseur au début du buffer
    csv_buffer.seek(0)
    
    # Envoi du contenu CSV au bucket S3
    s3_client.put_object(Bucket=BUCKET_NAME, Body=csv_buffer.getvalue(), Key=file_name)

def load_time_data(arc, week):
    file_name = f"Time_{arc}.csv"  # Nom du fichier dans le bucket S3
    
    # Tentative de chargement du fichier depuis S3
    try:
        df = load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
        # Filtrer les données pour la semaine spécifiée
        return df[df['WEEK'] == week]
    except Exception as e:
        # Gestion des erreurs, par exemple si le fichier n'existe pas
        print(f"Erreur lors du chargement des données depuis S3 : {e}")
        return pd.DataFrame()

def get_start_end_dates(year, week_number):
    # Trouver le premier jour de l'année
    first_day_of_year = datetime.datetime(year-1, 12, 31)
    first_monday_of_year = first_day_of_year + datetime.timedelta(days=(7-first_day_of_year.weekday()))
    week_start_date = first_monday_of_year + datetime.timedelta(weeks=week_number-1)
    week_end_date = week_start_date + datetime.timedelta(days=4)
    return week_start_date, week_end_date

def load_assigned_studies(arc):
    file_name = "STUDY.csv"  # Nom du fichier dans le bucket S3
    
    # Chargement du fichier depuis S3
    df_study = load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
    
    # Filtrage pour obtenir les études assignées à l'ARC spécifié
    assigned_studies = df_study[(df_study['ARC'] == arc) | (df_study['ARC_BACKUP'] == arc)]
    
    return assigned_studies['STUDY'].tolist()

def check_create_weekly_file(arc, year, week):
    file_name = f"Ongoing_{arc}.csv"

    try:
        df_existing = load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
    except Exception as e:
        # Si le fichier n'existe pas ou une autre erreur se produit, créer un nouveau DataFrame
        df_existing = pd.DataFrame(columns=CATEGORIES)
    
    # Chargement des études assignées
    assigned_studies = load_assigned_studies(arc)
    if assigned_studies:
        # Filtrer pour ne garder que les études non présentes pour cette semaine et année
        existing_studies = df_existing[(df_existing['YEAR'] == year) & (df_existing['WEEK'] == week)]['STUDY']
        new_studies = [study for study in assigned_studies if study not in existing_studies.tolist()]
        
        # Préparation des nouvelles lignes à ajouter uniquement pour les nouvelles études
        rows = [{'YEAR': year, 'WEEK': week, 'STUDY': study, 'VISITES PATIENT': 0, 'QUERIES': 0,
                 'SAISIE CRF': 0, 'REUNIONS': 0, 'REMOTE': 0, 'MONITORING': 0, 'TRAINING': 0,
                 'ARCHIVAGE EMAIL': 0, 'COMMENTAIRE': "Aucun", 'NB_VISITE': 0} for study in new_studies]

        if rows:  # S'il y a de nouvelles études à ajouter
            df_existing = pd.concat([df_existing, pd.DataFrame(rows)], ignore_index=True, sort=False)

            # Sauvegarde du DataFrame mis à jour sur S3
            save_csv_to_s3(df_existing, BUCKET_NAME, file_name, sep=';', encoding='utf-8')
    else:
        st.error("Aucune étude n'a été affectée. Merci de voir avec vos managers.")
        return None

    return file_name

def load_weekly_data(arc, week):
    file_name = f"Ongoing_{arc}.csv"  # Construit le nom du fichier basé sur l'ARC
    
    # Tentative de chargement du fichier depuis S3
    try:
        df = load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
        # Filtrer les données pour la semaine spécifiée et retourner le DataFrame
        return df[df['WEEK'] == week]
    except Exception as e:
        # En cas d'erreur, par exemple si le fichier n'existe pas, retourner un DataFrame vide
        print(f"Erreur lors du chargement des données depuis S3 : {e}")
        return pd.DataFrame()

def delete_ongoing_file(arc):
    file_name = f"Ongoing_{arc}.csv"  # Construit le nom du fichier basé sur l'ARC
    
    # Suppression du fichier depuis le bucket S3
    try:
        response = s3_client.delete_object(Bucket=BUCKET_NAME, Key=file_name)
        if response['ResponseMetadata']['HTTPStatusCode'] == 204:
            print(f"Le fichier {file_name} a été supprimé avec succès.")
        else:
            print(f"Erreur lors de la suppression du fichier {file_name}.")
    except Exception as e:
        # Gestion d'erreurs potentielles lors de la suppression
        print(f"Erreur lors de la tentative de suppression du fichier {file_name} : {e}")

def update_session_data(original_data, new_data, year, week):
    # Fonction pour mettre à jour les données en session_state après édition ou fusion
    original_data.drop(original_data[(original_data['YEAR'] == year) & (original_data['WEEK'] == week)].index, inplace=True)
    updated_data = pd.concat([original_data, new_data]).reset_index(drop=True)
    return updated_data

def save_changes_to_data(data, arc):
    # Fonction pour persister les modifications dans S3 ou autre storage
    save_data(data, arc)

def merge_data_for_current_week(time_df, ongoing_df, arc, year, week):
    # Fusionne les dataframes sur les colonnes 'YEAR', 'WEEK' et 'STUDY' tout en gardant toutes les entrées.
    merged_df = pd.merge(ongoing_df, time_df, on=['YEAR', 'WEEK', 'STUDY'], how='outer', suffixes=('', '_new'))
    
    # Mettre à jour les valeurs en utilisant les valeurs de 'time_df' si elles existent.
    for column in CATEGORIES[3:]:
        merged_df[column] = merged_df.apply(
            lambda row: row[column + '_new'] if not pd.isna(row[column + '_new']) else row[column], axis=1
        )
    
    # Supprimer les colonnes temporairement ajoutées '_new'
    merged_df.drop(columns=[col + '_new' for col in CATEGORIES[3:]], inplace=True)

    # S'assurer que les données des nouvelles études sont incluses
    # En supposant que load_assigned_studies(arc) renvoie toutes les études assignées à cet ARC
    assigned_studies = set(load_assigned_studies(arc))
    for study in assigned_studies:
        if study not in merged_df['STUDY'].tolist():
            new_row = {'YEAR': year, 'WEEK': week, 'STUDY': study}
            new_row.update({col: 0 for col in CATEGORIES[3:]})
            new_row['COMMENTAIRE'] = "Aucun"
            merged_df = merged_df.append(new_row, ignore_index=True)
    
    # Retourner uniquement les données pour la semaine et l'année en cours
    merged_df = merged_df[(merged_df['YEAR'] == year) & (merged_df['WEEK'] == week)]
    
    return merged_df

#####################################################################
# ====================== FONCTION PRINCIPALE ====================== #
#####################################################################

def main():
    try:
        st.set_page_config(layout="wide")
    except:
        pass
    st.title("I-Motion Adulte - Espace ARCs")

    # Authentification de l'utilisateur
    arc = st.sidebar.selectbox("Choisissez votre ARC", list(ARC_PASSWORDS.keys()))
    arc_password_entered = st.sidebar.text_input("Entrez le mot de passe pour {}".format(arc), type="password")
    
    if not authenticate_user(arc, arc_password_entered):
        st.sidebar.error("Mot de passe incorrect pour l'ARC sélectionné.")
        return

    # Chargement initial des données
    previous_week, current_week, next_week, current_year = calculate_weeks()

    # Interface utilisateur pour la sélection de l'année et de la semaine
    col1, col2 = st.columns([1, 3])
    with col1:
        year_choice = st.selectbox("Année", ANNEES, index=ANNEES.index(current_year))
    with col2:
        week_choice = st.slider("Semaine", 1, 52, current_week)

    # Gérer le chargement et la mise en cache des données avec st.session_state
    if 'data_loaded' not in st.session_state:
        st.session_state['data_loaded'] = False

    if not st.session_state['data_loaded'] or 'data_to_edit' not in st.session_state:
        df_data = load_data(arc)
        st.session_state['data_to_edit'] = df_data
        st.session_state['data_loaded'] = True
    else:
        df_data = st.session_state['data_to_edit']

    # Filtrage des données pour la visualisation
    filtered_df = df_data[(df_data['YEAR'] == year_choice) & (df_data['WEEK'] == week_choice)]
    int_columns = INT_CATEGORIES
    filtered_df[int_columns] = filtered_df[int_columns].astype(int)
    styled_df = filtered_df.style.format({"YEAR": "{:.0f}", "WEEK": "{:.0f}"})
    st.dataframe(styled_df, height=600)

    # Section pour la modification et la fusion des données
    if 'edit_mode' not in st.session_state:
        st.session_state['edit_mode'] = False

    edit_mode_button = st.button("Modifier les Données")
    if edit_mode_button:
        st.session_state['edit_mode'] = not st.session_state['edit_mode']

    if st.session_state['edit_mode']:
        week_choice2 = st.radio(
            "Choisissez une semaine",
            [f"Semaine précédente (Semaine {previous_week})", f"Semaine en cours (Semaine {current_week})"],
            index=1
        )

        selected_week = int(week_choice2.split()[-1].strip(')'))
        time_df = load_time_data(arc, selected_week)

        # Traitement spécifique pour la semaine en cours
        if "Semaine en cours" in week_choice2:
            weekly_file_path = check_create_weekly_file(arc, current_year, current_week)
            filtered_df2 = load_weekly_data(arc, selected_week)
            if not time_df.empty:
                # Fusionner les données pour la semaine en cours avec les données existantes
                merged_df, filtered_df2 = merge_data_for_current_week(time_df, filtered_df2, arc, current_year, current_week)
                
                # Sauvegarde des modifications dans session_state
                st.session_state['data_to_edit'] = update_session_data(st.session_state['data_to_edit'], merged_df, current_year, current_week)

        # Affichage du st.data_editor pour la modification
        edited_data = st.data_editor(data=filtered_df2, key="data_editor")

        if st.button('Sauvegarder les Modifications'):
            # Mettre à jour les données en session_state et persister les modifications
            save_changes_to_data(st.session_state['data_to_edit'], arc)
            st.success("Les modifications ont été sauvegardées avec succès.")
            st.session_state['edit_mode'] = False
            st.rerun()

#####################################################################
# ====================== LANCEMENT DE L'ALGO ====================== #
#####################################################################

if __name__ == "__main__":
    main()
