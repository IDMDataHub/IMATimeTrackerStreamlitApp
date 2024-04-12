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
CATEGORIES = ['YEAR', 'WEEK', 'STUDY', 'MISE EN PLACE', 'TRAINING', 'VISITES', 'SAISIE CRF', 'QUERIES', 'MONITORING', 'REMOTE', 'REUNIONS', 
'ARCHIVAGE EMAIL', 'MAJ DOC', 'AUDIT & INSPECTION', 'CLOTURE', 'NB_VISITE', 'NB_PAT_SCR', 'NB_PAT_RAN', 'NB_EOS', 'COMMENTAIRE']
INT_CATEGORIES = CATEGORIES[3:-1]
COLUMN_CONFIG = {
    'YEAR': {"label": 'Année', "description": "Année"},
    'WEEK': {"label": 'Sem.', "description": "Numéro de la semaine"},
    'STUDY': {"label": 'Étude', "description": "Nom de l'étude"},
    'MISE EN PLACE': {"label": 'MEP', "description": "Mise en place"},
    'TRAINING': {"label": 'Form.', "description": "Formation"},
    'VISITES': {"label": 'Vis.', "description": "Organisation des Visites"},
    'SAISIE CRF': {"label": 'CRF', "description": "Saisie CRF"},
    'QUERIES': {"label": 'Quer.', "description": "Queries"},
    'MONITORING': {"label": 'Monit.', "description": "Monitoring"},
    'REMOTE': {"label": 'Rem.', "description": "Remote"},
    'REUNIONS': {"label": 'Réu.', "description": "Réunions"},
    'ARCHIVAGE EMAIL': {"label": 'Arch. Email', "description": "Archivage des emails"},
    'MAJ DOC': {"label": 'Maj. Doc', "description": "Mise à jour des documents (ISF & Gaia)"},
    'AUDIT & INSPECTION': {"label": 'Aud.&Insp.', "description": "Audit et Inspection"},
    'CLOTURE': {"label": 'Clôture', "description": "Clôture"},
    'NB_VISITE': {"label": 'Nb Vis.', "description": "Nombre de visites"},
    'NB_PAT_SCR': {"label": 'Nb Pat. Scr. .', "description": "Nombre de patients screenés"},
    'NB_PAT_RAN': {"label": 'Nb Pat. Rand.', "description": "Nombre de patients randomisés"},
    'NB_EOS': {"label": 'Nb EOS.', "description": "Nombre d'EOS"},
    'COMMENTAIRE': {"label": 'Comm.', "description": "Commentaires"}
}

s3_client = boto3.client(
    's3',
    aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY']
)

def load_csv_from_s3(bucket_name, file_name, sep=';', encoding='utf-8'):
    """
    Charge un fichier CSV depuis un bucket S3 AWS en utilisant boto3, puis le lit dans un DataFrame pandas.

    Parameters:
    - bucket_name (str): Nom du bucket S3 où se trouve le fichier.
    - file_name (str): Nom du fichier à charger depuis le bucket S3.
    - sep (str, optional): Séparateur de champ dans le fichier CSV. Par défaut, c'est ';'.
    - encoding (str, optional): Encodage du fichier CSV. Par défaut, c'est 'utf-8'.

    Returns:
    - pandas.DataFrame: Un DataFrame contenant les données du fichier CSV.

    Raises:
    - Exception: Relève une exception si le chargement du fichier échoue pour une raison quelconque.
    """
    # Utilisez boto3 pour accéder à S3 et charger le fichier spécifié
    obj = s3_client.get_object(Bucket=bucket_name, Key=file_name)
    body = obj['Body'].read().decode(encoding)
    
    # Utilisez pandas pour lire le CSV
    data = pd.read_csv(StringIO(body), sep=sep)
    return data

def save_csv_to_s3(df, bucket_name, file_name, sep=';', encoding='utf-8'):
    """
    Sauvegarde un DataFrame pandas dans un fichier CSV sur un bucket S3 AWS en utilisant boto3.

    Parameters:
    - df (pandas.DataFrame): Le DataFrame à sauvegarder.
    - bucket_name (str): Le nom du bucket S3 où le fichier sera sauvegardé.
    - file_name (str): Le nom sous lequel le fichier CSV sera sauvegardé dans le bucket S3.
    - sep (str, optional): Le séparateur de champ à utiliser dans le fichier CSV. Par défaut, c'est ';'.
    - encoding (str, optional): L'encodage du fichier CSV. Par défaut, c'est 'utf-8'.

    Returns:
    None

    Raises:
    - Exception: Relève une exception si la sauvegarde échoue pour une raison quelconque.
    """
    # Convertir le DataFrame en CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=sep, encoding=encoding)
    
    # Réinitialiser le curseur du buffer au début
    csv_buffer.seek(0)
    
    # Utiliser s3_client pour sauvegarder le fichier CSV dans S3
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer.getvalue())

def load_arc_passwords():
    """
    Charge les mots de passe depuis un fichier CSV dans S3 en tentant d'abord avec l'encodage UTF-8,
    puis avec l'encodage Latin1 en cas d'échec d'encodage.

    Parameters:
    None

    Returns:
    - dict: Un dictionnaire avec les ARC comme clés et les mots de passe correspondants comme valeurs.

    Raises:
    None
    """
    try:
        # Tentez de charger le fichier avec l'encodage UTF-8
        df = load_csv_from_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        # Si une erreur d'encodage survient, tentez de charger avec l'encodage Latin1
        df = load_csv_from_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, sep=';', encoding='latin1')
    return dict(zip(df['ARC'], df['MDP']))

ARC_PASSWORDS = load_arc_passwords()

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

# ========================================================================================================================================
# CHARGEMENT DE DONNEES
def load_data(arc):
    """
    Charge les données d'un ARC spécifique depuis un fichier CSV situé dans un bucket S3.

    Parameters:
    - arc (str): Identifiant de l'ARC pour lequel charger les données.

    Returns:
    - pandas.DataFrame: DataFrame contenant les données chargées pour l'ARC spécifié.

    Raises:
    - UnicodeDecodeError: Relève une exception si un problème d'encodage survient lors du chargement des données.
    """
    file_name = f"Time_{arc}.csv" # Nom du fichier dans le bucket S3
    try:
        # Tentez de charger le fichier avec l'encodage UTF-8
        return load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        # Si une erreur d'encodage survient, tentez de charger avec l'encodage Latin1
        return load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='latin1')

def load_time_data(arc, week):
    """
    Charge les données de temps pour un ARC spécifique et une semaine donnée à partir d'un fichier CSV stocké dans S3.

    Parameters:
    - arc (str): L'identifiant de l'ARC pour lequel charger les données.
    - week (int): Le numéro de la semaine pour laquelle les données doivent être chargées.

    Returns:
    - pandas.DataFrame: Un DataFrame contenant les données de temps filtrées pour l'ARC et la semaine spécifiés.
    Si une erreur survient lors du chargement, un DataFrame vide est retourné.

    Raises:
    - Exception: Relève une exception si une erreur survient lors du chargement des données depuis S3.
    """
    file_name = f"Time_{arc}.csv" # Nom du fichier dans le bucket S3
    
    # Tentative de chargement du fichier depuis S3
    try:
        df = load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
        # Filtrer les données pour la semaine spécifiée
        return df[df['WEEK'] == week]
    except Exception as e:
        # Gestion des erreurs, par exemple si le fichier n'existe pas
        print(f"Erreur lors du chargement des données depuis S3 : {e}")
        return pd.DataFrame()

def load_assigned_studies(arc):
    """
    Charge la liste des études assignées à un ARC spécifique depuis un fichier CSV stocké dans S3.

    Parameters:
    - arc (str): L'identifiant de l'ARC pour lequel les études assignées doivent être chargées.

    Returns:
    - list: Une liste contenant les noms des études assignées à l'ARC spécifié.

    Raises:
    None
    """
    file_name = "STUDY.csv" # Nom du fichier dans le bucket S3
    
    # Chargement du fichier depuis S3
    df_study = load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
    
    # Filtrage pour obtenir les études assignées à l'ARC spécifié
    assigned_studies = df_study[(df_study['ARC'] == arc) | (df_study['ARC_BACKUP'] == arc)]
    
    return assigned_studies['STUDY'].tolist()

def load_weekly_data(arc, week):
    """
    Charge les données hebdomadaires pour un ARC spécifique et une semaine donnée à partir d'un fichier CSV stocké dans S3.

    Parameters:
    - arc (str): L'identifiant de l'ARC pour lequel charger les données hebdomadaires.
    - week (int): Le numéro de la semaine pour laquelle les données doivent être chargées.

    Returns:
    - pandas.DataFrame: Un DataFrame contenant les données hebdomadaires filtrées pour l'ARC et la semaine spécifiés.
    Si une erreur survient lors du chargement, un DataFrame vide est retourné.

    Raises:
    - Exception: Relève une exception si une erreur survient lors du chargement des données depuis S3.
    """
    file_name = f"Ongoing_{arc}.csv" # Construit le nom du fichier basé sur l'ARC
    
    # Tentative de chargement du fichier depuis S3
    try:
        df = load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
        # Filtrer les données pour la semaine spécifiée et retourner le DataFrame
        return df[df['WEEK'] == week]
    except Exception as e:
        # En cas d'erreur, par exemple si le fichier n'existe pas, retourner un DataFrame vide
        print(f"Erreur lors du chargement des données depuis S3 : {e}")
        return pd.DataFrame()

# ========================================================================================================================================
# SAUVEGARDE
def save_data(df, arc):
    """
    Sauvegarde les données d'un DataFrame dans un fichier CSV spécifique à un ARC sur S3.

    Parameters:
    - df (pandas.DataFrame): Le DataFrame contenant les données à sauvegarder.
    - arc (str): L'identifiant de l'ARC auquel les données sont associées.

    Returns:
    None

    Raises:
    - Exception: Relève une exception si la sauvegarde échoue pour une raison quelconque.
    """
    file_name = f"Time_{arc}.csv"
    
    # Conversion du DataFrame en chaîne CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=";", encoding='utf-8')
    
    # Réinitialisation de la position du curseur au début du buffer
    csv_buffer.seek(0)
    
    # Envoi du contenu CSV au bucket S3
    s3_client.put_object(Bucket=BUCKET_NAME, Body=csv_buffer.getvalue(), Key=file_name)

# ========================================================================================================================================
# GRAPH ET AFFICHAGE
def display_glossary(column_config):
    """
    Affiche un glossaire des termes et descriptions à partir d'une configuration de colonnes, en utilisant Streamlit.

    Parameters:
    - column_config (dict): Un dictionnaire contenant les configurations des colonnes, où chaque clé représente un terme 
      et chaque valeur est un dictionnaire avec des clés comme 'label' et 'description' pour ce terme.

    Returns:
    None

    Raises:
    None
    
    Utilise Streamlit pour rendre le glossaire sous forme de HTML.
    """
    glossary_html = "<div style='margin-left: 10px;'>"
    for term, config in column_config.items():
        label = config["label"]
        description = config.get("description", "Description non fournie")
        glossary_html += f"<b>{label}</b> : {description}<br>"
    glossary_html += "</div>"
    st.markdown(glossary_html, unsafe_allow_html=True)

# ========================================================================================================================================
# CALCULS
def authenticate_user(arc, password_entered):
    """
    Vérifie si le mot de passe saisi correspond au mot de passe de l'ARC dans la base de données.

    Parameters:
    - arc (str): L'identifiant de l'ARC.
    - password_entered (str): Le mot de passe saisi par l'utilisateur.

    Returns:
    - bool: Retourne True si le mot de passe correspond, sinon False.

    Raises:
    None
    """
    return ARC_PASSWORDS.get(arc) == password_entered.lower()

def calculate_weeks():
    """
    Calcule les numéros des semaines actuelle, précédente, suivante, et deux semaines avant, ainsi que l'année en cours.

    Parameters:
    None

    Returns:
    - tuple: Contient les numéros des deux semaines précédentes, de la semaine actuelle, de la semaine suivante, et de l'année en cours.

    Raises:
    None
    """
    current_date = datetime.datetime.now()
    current_week = current_date.isocalendar()[1]
    previous_week = current_week - 1 if current_week > 1 else 52
    two_weeks_ago = previous_week - 1 if previous_week > 1 else 52
    next_week = current_week + 1 if current_week < 52 else 1
    current_year = current_date.year
    return two_weeks_ago, previous_week, current_week, next_week, current_year

def get_start_end_dates(year, week_number):
    """
    Calcule les dates de début et de fin pour une semaine donnée d'une année spécifique.

    Parameters:
    - year (int): L'année pour laquelle calculer les dates.
    - week_number (int): Le numéro de la semaine pour laquelle calculer les dates de début et de fin.

    Returns:
    - tuple: Contient les dates de début et de fin de la semaine spécifiée.

    Raises:
    None
    
    Les dates sont calculées en se basant sur le système ISO de numérotation des semaines.
    """
    # Trouver le premier jour de l'année
    first_day_of_year = datetime.datetime(year-1, 12, 31)
    first_monday_of_year = first_day_of_year + datetime.timedelta(days=(7-first_day_of_year.weekday()))
    week_start_date = first_monday_of_year + datetime.timedelta(weeks=week_number-1)
    week_end_date = week_start_date + datetime.timedelta(days=4)
    return week_start_date, week_end_date

# ========================================================================================================================================
# CREATION ET MODIFICATION
def check_create_weekly_file(arc, year, week):
    """
    Vérifie l'existence d'un fichier hebdomadaire pour un ARC donné. Si le fichier n'existe pas,
    crée un nouveau DataFrame avec les colonnes spécifiées et le sauvegarde sur S3.

    Parameters:
    - arc (str): L'identifiant de l'ARC.
    - year (int): L'année concernée.
    - week (int): Le numéro de la semaine concernée.

    Returns:
    - str or None: Le nom du fichier créé ou modifié sur S3, ou None si aucune étude n'est affectée à l'ARC.

    Raises:
    - Exception: Relève une exception si une erreur survient lors de la création ou la modification du fichier.
    """
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
        rows = [{'YEAR': year, 'WEEK': week, 'STUDY': study, 'MISE EN PLACE': 0, 'TRAINING': 0, 'VISITES': 0, 'SAISIE CRF': 0, 'QUERIES': 0, 
             'MONITORING': 0, 'REMOTE': 0, 'REUNIONS': 0, 'ARCHIVAGE EMAIL': 0, 'MAJ DOC': 0, 'AUDIT & INSPECTION': 0, 'CLOTURE': 0, 
             'NB_VISITE': 0, 'NB_PAT_SCR':0, 'NB_PAT_RAN':0, 'NB_EOS':0, 'COMMENTAIRE': "Aucun"} for study in new_studies]
        if rows:  # S'il y a de nouvelles études à ajouter
            df_existing = pd.concat([df_existing, pd.DataFrame(rows)], ignore_index=True, sort=False)
            # Sauvegarde du DataFrame mis à jour sur S3
            save_csv_to_s3(df_existing, BUCKET_NAME, file_name, sep=';', encoding='utf-8')
    else:
        st.error("Aucune étude n'a été affectée. Merci de voir avec vos managers.")
        return None

    return file_name

def delete_ongoing_file(arc):
    """
    Supprime un fichier "ongoing" spécifique à un ARC sur S3, identifié par son nom construit.

    Parameters:
    - arc (str): L'identifiant de l'ARC dont le fichier ongoing doit être supprimé.

    Returns:
    None

    Raises:
    - Exception: Relève une exception si la suppression échoue pour une raison quelconque.
    """
    file_name = f"Ongoing_{arc}.csv"
    
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
    """
    Fonction principale exécutant l'application Streamlit. Elle configure la page, gère l'authentification des utilisateurs,
    l'affichage et la modification des données, ainsi que la sauvegarde des modifications.

    Parameters:
    None

    Returns:
    None

    Raises:
    None
    
    Cette fonction orchestre les interactions de l'utilisateur avec l'interface Streamlit, y compris le chargement et
    la modification des données, et appelle d'autres fonctions pour réaliser ces tâches.
    """
    try:
        st.set_page_config(layout="wide", page_icon=":microscope:", page_title="I-Motion Adulte - Espace ARCs")
    except:
        pass
    st.title("I-Motion Adulte - Espace ARCs")
    st.write("---")

    # Authentification de l'utilisateur
    arc = st.sidebar.selectbox("Choisissez votre ARC", list(ARC_PASSWORDS.keys()))
    arc_password_entered = st.sidebar.text_input(f"Entrez le mot de passe", type="password")
    
    if not authenticate_user(arc, arc_password_entered):
        st.sidebar.error("Mot de passe incorrect pour l'ARC sélectionné.")
        return
    
    with st.sidebar.expander("Glossaire des catégories"):
        display_glossary(COLUMN_CONFIG)

    # I. Chargement des données
    df_data = load_data(arc)
    two_weeks_ago, previous_week, current_week, next_week, current_year = calculate_weeks()

    # II. Section pour la modification des données
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
            column_config=column_config_df_time # Utilisez votre configuration de colonne spécifique ici
        )

        # Afficher la seconde partie avec sa configuration de colonne
        st.markdown('**Partie "Quantité"**')
        df2_edited = st.data_editor(
            data=df_quantity2,
            hide_index=True,
            disabled=["YEAR", "WEEK", "STUDY"],
            column_config=column_config_df_quantity # Utilisez votre configuration de colonne spécifique ici
        )

    else:
        st.write("Aucune donnée disponible pour la semaine sélectionnée.")
    
    
    # III. Bouton de sauvegarde
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
        save_data(updated_df, arc)

        # Supprimer le fichier Ongoing_ARC.csv
        delete_ongoing_file(arc)

        st.success("Les données ont été sauvegardées et le fichier temporaire a été supprimé.")

        # Recharger la page
        st.rerun()

    # IV. Interface utilisateur pour la sélection de l'année et de la semaine
    st.write("---")
    st.subheader("Visualisation de l'historique")
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


#####################################################################
# ====================== LANCEMENT DE L'ALGO ====================== #
#####################################################################

if __name__ == "__main__":
    main()