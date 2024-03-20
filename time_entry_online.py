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

@st.cache(allow_output_mutation=True)

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

def authenticate_user_interface():
    """Interface d'authentification utilisateur et validation."""
    arc = st.sidebar.selectbox("Choisissez votre ARC", list(ARC_PASSWORDS.keys()))
    arc_password_entered = st.sidebar.text_input(f"Entrez le mot de passe pour {arc}", type="password")
    if not authenticate_user(arc, arc_password_entered):
        st.sidebar.error("Mot de passe incorrect pour l'ARC sélectionné.")
        return None
    return arc

def load_and_display_data(arc):
    """Chargement et affichage des données sélectionnées."""
    df_data = load_data(arc)
    previous_week, current_week, next_week, current_year = calculate_weeks()

    year_choice, week_choice = user_date_selection(previous_week, current_week, next_week, current_year)

    filtered_df1 = df_data[(df_data['YEAR'] == year_choice) & (df_data['WEEK'] == week_choice)]
    filtered_df1[INT_CATEGORIES] = filtered_df1[INT_CATEGORIES].astype(int)
    styled_df = filtered_df1.style.format({"YEAR": "{:.0f}", "WEEK": "{:.0f}"})
    st.dataframe(styled_df, hide_index=True)

    return df_data, year_choice, week_choice

def user_date_selection(previous_week, current_week, next_week, current_year):
    """Sélection de la date par l'utilisateur."""
    st.subheader("Visualisation")
    col1, col2 = st.columns([1, 3])
    with col1:
        year_choice = st.selectbox("Année", ANNEES, index=ANNEES.index(current_year))
    with col2:
        week_choice = st.slider("Semaine", 1, 52, current_week)
    return year_choice, week_choice

def handle_week_selection(arc, year_choice, week_choice):
    """Gestion de la sélection de la semaine pour l'affichage et la modification."""
    selected_week = week_choice
    time_df = load_time_data(arc, selected_week)
    if not time_df.empty and not time_df[(time_df['YEAR'] == year_choice) & (time_df['WEEK'] == selected_week)].empty:
        filtered_df2 = merge_and_filter_data(time_df, arc, year_choice, selected_week)
    else:
        filtered_df2 = time_df
    return selected_week, time_df, filtered_df2

def display_weekly_data_editor(filtered_df2):
    """Affichage de l'éditeur de données hebdomadaires."""
    if not filtered_df2.empty:
        filtered_df2['YEAR'] = filtered_df2['YEAR'].apply(lambda x: f"{x:.0f}")
        filtered_df2['WEEK'] = filtered_df2['WEEK'].apply(lambda x: f"{x:.0f}")
        st.data_editor(data=filtered_df2, hide_index=True, disabled=["YEAR", "WEEK", "STUDY"])
    else:
        st.write("Aucune donnée disponible pour la semaine sélectionnée.")

def handle_data_saving(df_data, selected_week, arc):
    """Gère la sauvegarde des modifications apportées aux données."""
    if st.button("Sauvegarder"):
        save_updated_data(df_data, selected_week, arc)

def save_updated_data(df_data, selected_week, arc):
    """Sauvegarde les modifications apportées aux données et supprime les fichiers temporaires."""
    updated_df = update_data(df_data, selected_week)
    save_data(updated_df, arc)
    delete_ongoing_file(arc)
    st.success("Les données ont été sauvegardées et le fichier temporaire a été supprimé.")
    st.rerun()

#####################################################################
# ====================== FONCTION PRINCIPALE ====================== #
#####################################################################

def main():
    st.set_page_config(layout="wide")
    st.title("I-Motion Adulte - Espace ARCs")

    arc = authenticate_user_interface()
    if arc is None:
        return  # Arrête l'exécution si l'authentification échoue

    df_data, year_choice, week_choice = load_and_display_data(arc)
    if df_data is None:
        return  # Si aucun data n'est chargé, arrêtez l'exécution

    selected_week, time_df, filtered_df2 = handle_week_selection(arc, year_choice, week_choice)

    display_weekly_data_editor(filtered_df2)

    handle_data_saving(df_data, selected_week, arc)

#####################################################################
# ====================== LANCEMENT DE L'ALGO ====================== #
#####################################################################

if __name__ == "__main__":
    main()
