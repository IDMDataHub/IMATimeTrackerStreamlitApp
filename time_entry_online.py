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
CATEGORIES = ['YEAR', 'WEEK', 'STUDY', 'MISE EN PLACE', 'VISITES PATIENT', 'QUERIES', 'SAISIE CRF', 'REUNIONS', 'REMOTE', 
'MONITORING', 'TRAINING', 'ARCHIVAGE EMAIL', 'MAJ DOC', 'AUDIT & INSPECTION', 'CLOTURE', 'COMMENTAIRE', 'NB_VISITE']
INT_CATEGORIES = CATEGORIES[3:-2] + CATEGORIES[-1:]
COLUMN_CONFIG = {
    'YEAR': {"label": 'Année'},
    'WEEK': {"label": 'Semaine'},
    'STUDY': {"label": 'Étude'},
    'MISE EN PLACE': {"label": 'Mise en Place'},
    'VISITES PATIENT': {"label": 'Visites'},
    'QUERIES': {"label": 'Queries'},
    'SAISIE CRF': {"label": 'Saisie CRF'},
    'REUNIONS': {"label": 'Réunions'},
    'REMOTE': {"label": 'Remote'},
    'MONITORING': {"label": 'Monitoring'},
    'TRAINING': {"label": 'Formation'},
    'ARCHIVAGE EMAIL': {"label": 'Archiv. Email'},
    'MAJ DOC': {"label": 'MAJ. Docs'},
    'AUDIT & INSPECTION': {"label": 'Audit & Inspect.'},
    'CLOTURE': {"label": 'Clôture'},
    'COMMENTAIRE': {"label": 'Commentaire'},
    'NB_VISITE': {"label": 'Nb Visites'}
}

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
    two_weeks_ago = previous_week - 1 if previous_week > 1 else 52
    next_week = current_week + 1 if current_week < 52 else 1
    current_year = current_date.year
    return two_weeks_ago, previous_week, current_week, next_week, current_year

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
        rows = [{'YEAR': year, 'WEEK': week, 'STUDY': study, 'MISE EN PLACE': 0, 'VISITES PATIENT': 0, 'QUERIES': 0, 
                 'SAISIE CRF': 0, 'REUNIONS': 0, 'REMOTE': 0, 'MONITORING': 0, 'TRAINING': 0, 
                 'ARCHIVAGE EMAIL': 0, 'MAJ DOC': 0, 'AUDIT & INSPECTION': 0, 'CLOTURE': 0, 'COMMENTAIRE': "Aucun", 'NB_VISITE': 0} for study in assigned_studies]

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

#####################################################################
# ====================== FONCTION PRINCIPALE ====================== #
#####################################################################

def main():
    try:
        st.set_page_config(layout="wide", page_icon=":microscope:", page_title="I-Motion Adulte - Espace ARCs")
    except:
        pass
    st.title("I-Motion Adulte - Espace ARCs")

    # Authentification de l'utilisateur
    arc = st.sidebar.selectbox("Choisissez votre ARC", list(ARC_PASSWORDS.keys()))
    arc_password_entered = st.sidebar.text_input(f"Entrez le mot de passe pour {arc}", type="password")
    
    if not authenticate_user(arc, arc_password_entered):
        st.sidebar.error("Mot de passe incorrect pour l'ARC sélectionné.")
        return

    # I. Chargement des données
    df_data = load_data(arc)
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

    # Appliquer le style
    styled_df = filtered_df1.style.format({
        "YEAR": "{:.0f}",
        "WEEK": "{:.0f}"
    })

    # Utiliser styled_df pour l'affichage


    st.dataframe(styled_df, hide_index=True, column_config=COLUMN_CONFIG)

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
        filtered_df2 = load_weekly_data(arc, selected_week)

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
            rows = [{'YEAR': current_year, 'WEEK': current_week, 'STUDY': study, 'MISE EN PLACE': 0, 'VISITES PATIENT': 0, 'QUERIES': 0, 
             'SAISIE CRF': 0, 'REUNIONS': 0, 'REMOTE': 0, 'MONITORING': 0, 'TRAINING': 0, 
             'ARCHIVAGE EMAIL': 0, 'MAJ DOC': 0, 'AUDIT & INSPECTION': 0, 'CLOTURE': 0, 'COMMENTAIRE': "Aucun", 'NB_VISITE': 0} for study in assigned_studies]
            filtered_df2 = pd.DataFrame(rows)


    # IV. Afficher le DataFrame dans l'éditeur de données
    if not filtered_df2.empty:
        filtered_df2['YEAR'] = filtered_df2['YEAR'].apply(lambda x: f"{x:.0f}")
        filtered_df2['WEEK'] = filtered_df2['WEEK'].apply(lambda x: f"{x:.0f}")
        df = st.data_editor(
            data=filtered_df2,
            hide_index=True,
            disabled=["YEAR", "WEEK", "STUDY"],
            column_config=COLUMN_CONFIG)

    else:
        st.write("Aucune donnée disponible pour la semaine sélectionnée.")
    
    # V. Bouton de sauvegarde
    if st.button("Sauvegarder"):

        # Retirer les anciennes données de la semaine sélectionnée
        df_data = df_data[df_data['WEEK'] != int(selected_week)]

        # Concaténer avec les nouvelles données
        updated_df = pd.concat([df_data, df]).sort_index()

        # Sauvegarder le DataFrame mis à jour
        save_data(updated_df, arc)

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
