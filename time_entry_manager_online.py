#####################################################################
# =========================== LIBRAIRIES ========================== #
#####################################################################

import streamlit as st
import pandas as pd
import os
import datetime
import locale
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import boto3
from io import StringIO, BytesIO
import math
from botocore.exceptions import ClientError


#####################################################################
# =========================== CONSTANTES ========================== #
#####################################################################

# Configuration et constantes
BUCKET_NAME = "bucketidb"
ARC_PASSWORDS_FILE = "ARC_MDP.csv"
STUDY_INFO_FILE = "STUDY.csv"
MOT_DE_PASSE = st.secrets["APP_MDP"]
ANNEES = list(range(2024, 2030))
CATEGORIES = ['YEAR', 'WEEK', 'STUDY', 'MISE EN PLACE', 'TRAINING', 'VISITES', 'SAISIE CRF', 'QUERIES', 'MONITORING', 'REMOTE', 'REUNIONS', 
'ARCHIVAGE EMAIL', 'MAJ DOC', 'AUDIT & INSPECTION', 'CLOTURE', 'NB_VISITE', 'NB_PAT_SCR', 'NB_PAT_RAN', 'NB_EOS', 'COMMENTAIRE']
INT_CATEGORIES = CATEGORIES[3:-1]
TIME_INT_CAT = CATEGORIES[3:-5]
MONTHS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
SHAPE_BOX = {
    "ha": 'center', 
    "va": 'center', 
    "fontsize": 12, 
    "color": 'darkorange',
    "bbox": dict(facecolor='none', edgecolor='darkorange', boxstyle='round,pad=0.5')
}

#####################################################################
# ========================= INFO GENERALES========================= #
#####################################################################

s3_client = boto3.client(
    's3',
    aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY']
)

def load_csv_from_s3(bucket_name, file_name, sep=';', encoding='utf-8'):
    # Utilisez boto3 pour accéder à S3 et charger le fichier spécifié
    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key=file_name)
        body = obj['Body'].read().decode(encoding)
        
        try:
            # Essayer de lire le fichier avec l'encodage utf-8
            return pd.read_csv(StringIO(body), encoding='utf-8', sep=sep)
        except UnicodeDecodeError:
            return pd.read_csv(StringIO(body), encoding='latin1', sep=sep)
        except FileNotFoundError:
            return None
    except:
        return None

# Création d'une palette "viridis" avec le nombre approprié de couleurs
viridis_palette = sns.color_palette("viridis", len(TIME_INT_CAT))

# Mapping des catégories aux couleurs de la palette "viridis"
category_colors = {category: color for category, color in zip(TIME_INT_CAT, viridis_palette)}

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

# ========================================================================================================================================
# CHARGEMENT DE DONNEE
def load_data(arc):
    file_name = f"Time_{arc}.csv"  # Nom du fichier dans le bucket S3
    try:
        # Tentez de charger le fichier avec l'encodage UTF-8
        return load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        # Si une erreur d'encodage survient, tentez de charger avec l'encodage Latin1
        return load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='latin1')


def load_all_study_names(bucket_name):
    # Utiliser boto3 pour lister les objets dans le bucket S3
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix="Time_")
    
    # Ensemble pour stocker les noms d'études uniques
    unique_studies = set()

    if 'Contents' in response:
        # Itérer sur chaque fichier qui commence par "Time_"
        for obj in response['Contents']:
            file_key = obj['Key']
            arc_name = file_key.split('_')[1].split('.')[0]  # Extraire le nom de l'ARC depuis le nom du fichier dans le bucket
            
            # Charger les données depuis S3
            df = load_csv_from_s3(bucket_name, file_key, sep=';', encoding='utf-8')
            if not df.empty:
                unique_studies.update(df['STUDY'].unique())
    
    return sorted(list(unique_studies))


def load_arc_info():
    return load_csv_from_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, sep=';', encoding='utf-8')

def load_study_info():
    # Utilisez la fonction load_csv_from_s3 avec le nom de fichier STUDY_INFO_FILE et les paramètres appropriés
    return load_csv_from_s3(BUCKET_NAME, STUDY_INFO_FILE, sep=';', encoding='utf-8')

# ========================================================================================================================================
# SAUVEGARDE
# Sauvegarde des données modifiées
def save_data_to_s3(bucket_name, file_name, df):
    # Convertir le DataFrame en CSV en utilisant StringIO
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8')
    
    # Réinitialiser le pointeur au début du flux
    csv_buffer.seek(0)
    
    # Uploader le CSV dans le bucket S3
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer.getvalue())

# ========================================================================================================================================
# GRAPH ET AFFICHAGE

def create_bar_chart(data, title, week_or_month, y='Total Time'):
    """Crée un graphique en barres pour les données fournies avec des couleurs cohérentes."""
    fig, ax = plt.subplots(figsize=(10, 4))

    # Définition de l'ordre des catégories et des couleurs correspondantes
    category_order = data.index.tolist()
    color_palette = sns.color_palette("viridis", len(category_order))

    # Mapping des couleurs aux catégories
    color_mapping = dict(zip(category_order, color_palette))

    # Création du graphique en barres avec l'ordre des couleurs défini
    sns.barplot(x=data.index, y=y, data=data, ax=ax, palette=color_mapping)
    ax.set_title(f'{title} pour {week_or_month}')
    ax.set_xlabel('')
    ax.set_ylabel('Heures')
    ax.xaxis.set_ticks_position('none') 
    ax.yaxis.set_ticks_position('none')
    sns.despine(left=False, bottom=False)
    plt.xticks(rotation=45)
    st.pyplot(fig)

def plot_pie_chart_on_ax(df_study_sum, titre, ax):
    colors = [category_colors[cat] for cat in df_study_sum.index if cat in category_colors]
    
    wedges, texts, autotexts = ax.pie(df_study_sum, labels=df_study_sum.index, autopct=lambda p: '{:.0f} h'.format(p * df_study_sum.sum() / 100), startangle=140, colors=colors)
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_size(10)
    
    ax.set_title(titre)

def generate_charts_for_time_period(df, studies, period, period_label):
    st.write(f"Graphiques pour {period_label} {period}")
    
    if len(studies) > 0:
        nrows = (len(studies) + 1) // 2 if len(studies) % 2 else len(studies) // 2
        fig, axs = plt.subplots(nrows=nrows, ncols=2, figsize=(10, 5 * nrows))
        axs = axs.flatten()  # Aplatir le tableau d'axes pour un accès simplifié

        for i, study in enumerate(studies):
            df_study = df[df['STUDY'] == study]
            df_study_sum = df_study[TIME_INT_CAT].fillna(0).sum()
            df_study_sum = df_study_sum[df_study_sum > 0]

            if df_study_sum.sum() > 0:
                plot_pie_chart_on_ax(df_study_sum, f'Temps par Tâche pour {study}', axs[i])
            else:
                # Ajouter le texte avec un cadre arrondi
                axs[i].text(0.5, 0.5, f"Aucune donnée disponible\npour {study}", **SHAPE_BOX)
                axs[i].set_axis_off()  # Masquer les axes si pas de données

        # Masquer les axes supplémentaires s'ils ne sont pas utilisés
        for j in range(i + 1, len(axs)):
            axs[j].axis('off')

        plt.tight_layout()
        st.pyplot(fig) 
    else:
        st.warning("Aucune étude sélectionnée ou aucune donnée disponible pour les études sélectionnées.")

def process_and_display_data(df, period_label, period_value):
    df_activities = df.groupby('STUDY')[TIME_INT_CAT].sum()
    df_activities['Total Time'] = df_activities.sum(axis=1)
    df_activities_sorted = df_activities.sort_values('Total Time', ascending=False)
    create_bar_chart(df_activities_sorted, f'Heures Passées par Étude', f'{period_label} {period_value}')
    
    # Calcul et affichage du temps total passé et du nombre total de visites
    total_time_spent = int(df_activities_sorted['Total Time'].sum())
    unit = "heure" if total_time_spent <= 1 else "heures"
    total_visits = int(sum(df['NB_VISITE']))
    
    time, visit = st.columns(2)
    with time:
        st.metric(label="Temps total passé", value=f"{total_time_spent} {unit}")
    with visit:
        st.metric(label="Nombre total de visites", value=f"{total_visits}")

def generate_time_series_chart(data_dict, title_prefix, mode='year'):
    """Génère et affiche un graphique en série temporelle pour les données fournies.
    
    Args:
        data_dict (dict): Dictionnaire des données à tracer.
        title_prefix (str): Préfixe pour le titre du graphique.
        mode (str): 'last_5_weeks' pour les 5 dernières semaines, 'year' pour l'année en cours.
    """
    if not data_dict:
        st.error("Aucune donnée disponible pour l'affichage du graphique.")
        return

    _, current_week, _, current_year, _ = calculate_weeks()
    if mode == 'year':
        total_weeks = 52 if datetime.date(current_year, 12, 31).isocalendar()[1] == 1 else 53
    else:
        total_weeks = current_week  # S'arrête à la semaine en cours pour le mode 'last_5_weeks'
    
    fig, ax = plt.subplots(figsize=(12, 6))
    for arc, data in data_dict.items():
        if mode == 'year':
            filtered_data = data[data['WEEK'] <= current_week]  # Pour l'année, s'arrête à la semaine en cours
        else:
            filtered_data = data  # Pour les 5 dernières semaines, utilise toutes les données disponibles
        sns.lineplot(ax=ax, x='WEEK', y='Total Time', data=filtered_data, label=arc)

    plt.title(f"{title_prefix} du Temps Total Passé par Chaque ARC")
    plt.xlabel('Semaines')
    plt.ylabel('Temps Total (Heures)')
    
    if mode == 'year':
        plt.xlim(1, total_weeks)
        ax.set_xticks(np.arange(1, total_weeks + 1))
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    plt.legend()
    st.pyplot(fig)

# ========================================================================================================================================
# CALCULS
def calculate_weeks():
    current_date = datetime.datetime.now()
    current_week = current_date.isocalendar()[1]
    previous_week = current_week - 1 if current_week > 1 else 52
    next_week = current_week + 1 if current_week < 52 else 1
    current_year = current_date.year
    current_month = current_date.month
    return previous_week, current_week, next_week, current_year, current_month

# ========================================================================================================================================
# CREATION ET MODIFICATION
# Vérifie et crée un fichier pour chaque ARC dans le DataFrame
def create_time_files_for_arcs(df):
    for arc_name in df['ARC'].dropna().unique():  # Assurez-vous de filtrer les valeurs NaN et de travailler avec des noms uniques
        file_name = f"Time_{arc_name}.csv"
        try:
            # Tentez de récupérer les métadonnées de l'objet pour voir s'il existe déjà
            s3_client.head_object(Bucket=BUCKET_NAME, Key=file_name)
            # Si aucune exception n'est levée, le fichier existe déjà, donc nous n'allons pas le créer
        except: 
            # Le fichier n'existe pas, vous pouvez créer le fichier
            new_df = pd.DataFrame(columns=CATEGORIES)  # Création d'un nouveau DataFrame avec les colonnes souhaitées
            csv_buffer = StringIO()
            new_df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8')
            csv_buffer.seek(0)  # Retour au début du buffer pour lire son contenu
            # Envoi du contenu CSV au fichier dans S3
            s3_client.put_object(Bucket=BUCKET_NAME, Key=file_name, Body=csv_buffer.getvalue())

def create_ongoing_files_for_arcs(df):
    for arc_name in df['ARC'].dropna().unique():  # Assurer l'unicité et l'absence de valeurs NaN
        file_name = f"Ongoing_{arc_name}.csv"

        try:
            # Tentative de chargement du fichier pour vérifier son existence
            s3_client.head_object(Bucket=BUCKET_NAME, Key=file_name)
        except:
            # Si une exception est levée, cela signifie généralement que le fichier n'existe pas
            # Création d'un nouveau DataFrame avec les colonnes souhaitées
            new_df = pd.DataFrame(columns=CATEGORIES)
            csv_buffer = StringIO()
            new_df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8')
            csv_buffer.seek(0)  # Retour au début du buffer pour lire son contenu
            # Envoi du contenu CSV au fichier dans S3
            s3_client.put_object(Bucket=BUCKET_NAME, Key=file_name, Body=csv_buffer.getvalue())

def add_row_to_df_s3(bucket_name, file_name, df, **kwargs):
    # Créer une nouvelle ligne à partir des kwargs
    new_row = pd.DataFrame(kwargs, index=[0])
    # Concaténer la nouvelle ligne au DataFrame existant
    df = pd.concat([df, new_row], ignore_index=True)

    # Convertir le DataFrame mis à jour en chaîne CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8')
    csv_buffer.seek(0)  # Retour au début du buffer pour lire son contenu
    
    # Sauvegarder le DataFrame mis à jour
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer.getvalue())

    return df

def delete_row_s3(bucket_name, file_name, df, row_to_delete):
    # Supprimer la ligne spécifiée du DataFrame
    df = df.drop(row_to_delete)
    
    # Convertir le DataFrame mis à jour en chaîne CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8')
    csv_buffer.seek(0)  # Retour au début du buffer pour lire son contenu
    
    # Sauvegarder le DataFrame mis à jour sur S3
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer.getvalue())
    
    return df


#####################################################################
# ====================== FONCTION PRINCIPALE ====================== #
#####################################################################

# Fonction principale de l'application Streamlit
def main():
    try:
        st.set_page_config(layout="wide", page_icon="📊", page_title="I-Motion Adulte - Espace Chefs de Projets")
    except:
        pass


    # Initialisation de st.session_state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        espace1, col_mdp, espace2 = st.columns([2, 3, 2])
        with col_mdp:
            mot_de_passe_saisi = st.text_input("Entrez le mot de passe", type="password")

            if mot_de_passe_saisi == MOT_DE_PASSE:
                st.session_state.authenticated = True
            else:
                st.write("Mot de passe incorrect. Veuillez réessayer.")

    if st.session_state.authenticated:
        st.title("I-Motion Adulte - Espace Chefs de Projets")
        st.write("---")

        # Onglet de sélection
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["👥 Gestion - ARCs", "📚 Gestion - Etudes", "📈 Dashboard - par ARCs", "📊 Dashboard - tous ARCs",  "📈 Dashboard - par Etude", "📊 Dashboard - toutes Etudes"])

    # ----------------------------------------------------------------------------------------------------------
        with tab1:
            arc_df = load_arc_info()

            col_ajout, espace, col_suppr, espace, col_modif = st.columns([3, 1, 3, 1, 3])
            with col_ajout:
                st.markdown("#### Ajout d'un nouvel ARC")
                new_arc_name = st.text_input("Nom du nouvel ARC", key="new_arc_name")
                new_arc_mdp = st.text_input("Mot de passe pour le nouvel ARC", key="new_arc_mdp")
                if st.button("Ajouter l'ARC"):
                    if new_arc_name and new_arc_mdp:  # Vérifier que les champs ne sont pas vides
                        arc_df = add_row_to_df_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, arc_df, 
                            ARC=new_arc_name, 
                            MDP=new_arc_mdp)
                        create_time_files_for_arcs(arc_df)
                        create_ongoing_files_for_arcs(arc_df) 
                        st.success(f"Nouvel ARC '{new_arc_name}' ajouté avec succès.")
                        st.rerun()
                    else:
                        st.error("Veuillez remplir le nom de l'ARC et le mot de passe.")            


            with col_suppr:
                st.markdown("#### Archivage d'un ARC")
                arc_options = arc_df['ARC'].dropna().astype(str).tolist()
                arc_to_delete = st.selectbox("Choisir un ARC à archiver", sorted(arc_options))
                if st.button("Archiver l'ARC sélectionné"):
                    arc_df = delete_row_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, arc_df, arc_df[arc_df['ARC'] == arc_to_delete].index)
                    st.success(f"ARC '{arc_to_delete}' archivé avec succès.")
                    st.rerun()

            with col_modif:
                st.markdown("#### Gestion des mots de passe")
                for i, row in arc_df.iterrows():
                    with st.expander(f"{row['ARC']}"):
                        new_mdp = st.text_input(f"Nouveau mot de passe", value=row['MDP'], key=f"mdp_{i}")
                        # Mettre à jour le DataFrame en session_state si le mot de passe change
                        if new_mdp != row['MDP']:
                            arc_df.at[i, 'MDP'] = new_mdp
                # Bouton pour sauvegarder les modifications
                if st.button('Sauvegarder les modifications'):
                    # Utilisez ici votre fonction de sauvegarde des données
                    save_data_to_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, arc_df)
                    st.success('Modifications sauvegardées avec succès.')
                    st.rerun()
    # ----------------------------------------------------------------------------------------------------------
        with tab2:
            study_df = load_study_info()

            col_ajout, espace, col_suppr, espace, col_modif = st.columns([3, 1, 3, 1, 3])
            with col_ajout:
                st.markdown("#### Ajout d'une nouvelle étude")
                new_study_name = st.text_input("Nom de l'étude", key="new_study_name")
                new_study_arc_principal = st.text_input("ARC principal", key="new_study_arc_principal")
                new_study_arc_backup = st.text_input("ARC de backup (optionnel)", key="new_study_arc_backup")

                if st.button("Ajouter l'étude"):
                    if new_study_name and new_study_arc_principal:  # Vérification minimale
                        # Ajout de la nouvelle étude
                        study_df = add_row_to_df_s3(BUCKET_NAME, STUDY_INFO_FILE, study_df,
                                                 STUDY=new_study_name, 
                                                 ARC=new_study_arc_principal, 
                                                 ARC_BACKUP=new_study_arc_backup if new_study_arc_backup else "")
                        st.success(f"Nouvelle étude '{new_study_name}' ajoutée avec succès.")
                        st.rerun()
                    else:
                        st.error("Le nom de l'étude et l'ARC principal sont requis.")        

            with col_suppr:
                st.markdown("#### Archivage d'une étude")
                study_options = study_df['STUDY'].dropna().astype(str).tolist()
                study_to_delete = st.selectbox("Choisir une étude à archiver", sorted(study_options))
                if st.button("Archiver l'étude sélectionnée"):
                    study_df = delete_row_s3(BUCKET_NAME, STUDY_INFO_FILE ,study_df, study_df[study_df['STUDY'] == study_to_delete].index)
                    st.success(f"L'étude '{study_to_delete}' est archivée avec succès.")
                    st.rerun()

            with col_modif:
                st.markdown("#### Affectation des études")
                arc_options = arc_df['ARC'].dropna().astype(str).tolist()
                arc_options = sorted(arc_options) + ['Aucun']  # Remplace 'nan' par 'Aucun'

                for i, row in study_df.iterrows():
                    with st.expander(f"{row['STUDY']}"):
                        # Trouvez l'index de l'ARC principal actuel dans les options, en traitant 'nan' comme 'Aucun'
                        arc_principal_current = 'Aucun' if pd.isna(row['ARC']) else row['ARC']
                        arc_principal_index = arc_options.index(arc_principal_current) if arc_principal_current in arc_options else len(arc_options) - 1
                        # Sélectionnez l'ARC principal avec l'index trouvé
                        new_arc_principal = st.selectbox(f"ARC Principal pour {row['STUDY']}", arc_options, index=arc_principal_index, key=f"principal_{i}")
                        
                        # Trouvez l'index de l'ARC de secours actuel dans les options, en traitant 'nan' comme 'Aucun'
                        arc_backup_current = 'Aucun' if pd.isna(row['ARC_BACKUP']) else row['ARC_BACKUP']
                        arc_backup_index = arc_options.index(arc_backup_current) if arc_backup_current in arc_options else len(arc_options) - 1
                        # Sélectionnez l'ARC de secours avec l'index trouvé
                        new_arc_backup = st.selectbox(f"ARC Backup pour {row['STUDY']}", arc_options, index=arc_backup_index, key=f"backup_{i}", help="Optionnel")

                        # Avant de sauvegarder, remplacez 'Aucun' par np.nan
                        study_df.at[i, 'ARC'] = np.nan if new_arc_principal == 'Aucun' else new_arc_principal
                        study_df.at[i, 'ARC_BACKUP'] = np.nan if new_arc_backup == 'Aucun' else new_arc_backup


                # Bouton global pour sauvegarder toutes les modifications
                if st.button('Sauvegarder les modifications', key=19):
                    save_data_to_s3(BUCKET_NAME, STUDY_INFO_FILE, study_df)
                    st.success('Modifications sauvegardées avec succès.')
                    st.rerun() 

    # ----------------------------------------------------------------------------------------------------------
        with tab3:
            col_arc, col_year, espace1, espace2 = st.columns(4)

            with col_arc:
                arc = st.selectbox("Choix de l'ARC", list(ARC_PASSWORDS.keys()), key=2)

            with col_year:
                year_choice = st.selectbox("Année", ANNEES, key=3, index=ANNEES.index(datetime.datetime.now().year))

            # I. Chargement des données
            df_data = load_data(arc)
            previous_week, current_week, next_week, current_year, current_month = calculate_weeks()

            associated_studies = df_data['STUDY'].unique().tolist()
            filtered_studies_df = study_df[study_df['STUDY'].isin(associated_studies)]
            associated_studies = filtered_studies_df['STUDY'].unique().tolist()

            # Liste des noms de mois
            month_names = MONTHS

            # II. Interface utilisateur pour la sélection de l'année, du mois et de la semaine
            col_week, espace, col_month = st.columns([1, 0.25, 1])
            with col_week:
                week_choice = st.slider("Semaine", 1, 52, current_week, key=4)
            with col_month:
                # Assurez-vous que le choix du mois utilise une clé différente
                selected_month_name = st.select_slider("Mois", options=month_names, 
                                value=month_names[current_month - 1], key=6)
                # Convertir le nom du mois sélectionné en numéro
                month_choice = month_names.index(selected_month_name) + 1

            # Filtrage des données pour le tableau de la semaine
            filtered_week_df = df_data[(df_data['YEAR'] == year_choice) & (df_data['WEEK'] == week_choice)]

            # Filtrage des données pour le tableau du mois
            first_day_of_month = datetime.datetime(year_choice, month_choice, 1)
            last_day_of_month = datetime.datetime(year_choice, month_choice + 1, 1) - datetime.timedelta(days=1)
            start_week = first_day_of_month.isocalendar()[1]
            end_week = last_day_of_month.isocalendar()[1]
            filtered_month_df = df_data[(df_data['YEAR'].astype(int) == year_choice) & 
                                (df_data['WEEK'].astype(int) >= start_week) & 
                                (df_data['WEEK'].astype(int) <= end_week)]


            # Convertir certaines colonnes en entiers pour les deux tableaux
            filtered_week_df[TIME_INT_CAT] = filtered_week_df[TIME_INT_CAT].astype(int)
            filtered_month_df[TIME_INT_CAT] = filtered_month_df[TIME_INT_CAT].astype(int)


            # Utilisation de la fonction pour les données hebdomadaires
            with col_week:
                process_and_display_data(filtered_week_df, "semaine", week_choice)

            # Utilisation de la fonction pour les données mensuelles
            with col_month:
                process_and_display_data(filtered_month_df, "mois", selected_month_name)

            st.write("---")

            # Selection des études avec multiselect
            sel_studies = st.multiselect("Choisir une ou plusieurs études", options=associated_studies, default=associated_studies, key=10)
            num_studies = len(sel_studies)

            # Calculer le nombre de lignes nécessaires pour deux colonnes
            nrows = (num_studies + 1) // 2 if num_studies % 2 else num_studies // 2

            # Créer les colonnes principales pour les semaines et les mois
            col_week, col_month = st.columns(2)

            # Générer les graphiques pour la semaine dans la colonne de gauche
            with col_week:
                generate_charts_for_time_period(filtered_week_df, sel_studies, week_choice, "la semaine")
         
            # Répéter la même structure pour le mois dans la colonne de droite
            with col_month:
                generate_charts_for_time_period(filtered_month_df, sel_studies, selected_month_name, "")

    # ----------------------------------------------------------------------------------------------------------
        with tab4:
            arcs = list(ARC_PASSWORDS.keys())

            previous_week, current_week, next_week, current_year, current_month = calculate_weeks()

            # Utiliser current_year au lieu de 2024 directement
            last_5_weeks = [(current_week - i - 1) % 52 + 1 for i in range(5)]
            all_weeks_current_year = np.arange(1, 53)  # Toutes les semaines pour l'année courante
            dfs = {}  # Pour stocker les DataFrames

            for arc in arcs:
                if arc is not None and not (isinstance(arc, float) and math.isnan(arc)):
                    try:
                        df_arc = load_data(arc)
                        df_arc['Total Time'] = df_arc[TIME_INT_CAT].sum(axis=1)
                        df_arc = df_arc.groupby(['YEAR', 'WEEK'])['Total Time'].sum().reset_index()
                        
                        # Préparer un DataFrame avec toutes les semaines pour les 5 dernières semaines avec des valeurs par défaut à 0
                        df_all_last_5_weeks = pd.DataFrame({'YEAR': current_year, 'WEEK': last_5_weeks, 'Total Time': 0}).merge(
                            df_arc[(df_arc['YEAR'] == current_year) & (df_arc['WEEK'].isin(last_5_weeks))],
                            on=['YEAR', 'WEEK'], how='left', suffixes=('', '_y')).fillna(0)
                        df_all_last_5_weeks['Total Time'] = df_all_last_5_weeks[['Total Time', 'Total Time_y']].max(axis=1)
                        df_all_last_5_weeks.drop(columns=['Total Time_y'], inplace=True)
                        
                        # Préparer un DataFrame pour toutes les semaines de l'année courante avec des valeurs par défaut à 0
                        df_all_current_year = pd.DataFrame({'YEAR': current_year, 'WEEK': all_weeks_current_year, 'Total Time': 0}).merge(
                            df_arc[df_arc['YEAR'] == current_year],
                            on=['YEAR', 'WEEK'], how='left', suffixes=('', '_y')).fillna(0)
                        df_all_current_year['Total Time'] = df_all_current_year[['Total Time', 'Total Time_y']].max(axis=1)
                        df_all_current_year.drop(columns=['Total Time_y'], inplace=True)
                        
                        dfs[arc] = {'last_5_weeks': df_all_last_5_weeks, 'current_year': df_all_current_year}
                    except:
                        pass
                else:
                    st.error(f"Le dataframe pour {arc} n'a pas pu être chargé.")

            col_month, col_year = st.columns(2)
            
            # Pour le graphique des 5 dernières semaines
            with col_month:
                generate_time_series_chart({arc: data['last_5_weeks'] for arc, data in dfs.items()}, "Évolution Hebdomadaire", mode='last_5_weeks')

                    # Pour le graphique de l'année en cours
            with col_year:
                generate_time_series_chart({arc: data['current_year'] for arc, data in dfs.items()}, f"Évolution Hebdomadaire en {current_year}", mode='year')

    # ----------------------------------------------------------------------------------------------------------
        with tab5:
            # Sélection d'une étude
            study_names = load_all_study_names(BUCKET_NAME)
            study_choice = st.selectbox("Choisissez votre étude", study_names)

            # Chargement et combinaison des données de tous les ARCs
            all_arcs_df = pd.DataFrame()
            for arc in ARC_PASSWORDS.keys():
                if arc is not None and not (isinstance(arc, float) and math.isnan(arc)):
                    try:
                        df_arc = load_data(arc)
                        df_arc['ARC'] = arc
                        all_arcs_df = pd.concat([all_arcs_df, df_arc], ignore_index=True)
                    except:
                        pass

            # Filtrage des données par étude sélectionnée
            filtered_df_by_study = all_arcs_df[all_arcs_df['STUDY'] == study_choice]

            # Assurez-vous que les colonnes d'intérêt sont de type numérique pour le calcul
            filtered_df_by_study[TIME_INT_CAT] = filtered_df_by_study[TIME_INT_CAT].apply(pd.to_numeric, errors='coerce')

            # Calculer le temps total passé par catégorie d'activité pour l'étude sélectionnée
            total_time_by_category = filtered_df_by_study[TIME_INT_CAT].sum()


            # Utilisation de st.columns pour diviser l'espace d'affichage
            col_table, espace, col_graph = st.columns([1.5, 0.2, 2])

            with col_table:
                st.write(f"Temps passé sur l'étude {study_choice}, par catégorie d'activité :")
                
                # Commencer par un header de Markdown pour le tableau
                markdown_table = "Catégorie | Heures passées\n:- | -:\n"
                
                # Ajouter chaque catégorie et le temps correspondant dans le format Markdown
                for category, hours in total_time_by_category.items():
                    markdown_table += f"{category} | {hours:}\n"
                
                # Afficher le tableau formaté en Markdown
                st.markdown(markdown_table)

            with col_graph:
                # Préparation et affichage du graphique en camembert dans la deuxième colonne
                fig, ax = plt.subplots()
                # Assurez-vous que total_time_by_category est défini avant cette ligne
                total_time_by_category = total_time_by_category[total_time_by_category > 0]
                if total_time_by_category.sum() > 0:
                    plot_pie_chart_on_ax(total_time_by_category, f"Répartition du temps par catégorie pour l'étude {study_choice}", ax)
                else:
                    ax.text(0.5, 0.5, f"Aucune donnée disponible\npour {study_choice}", ha='center', va='center', transform=ax.transAxes)  # Correction de la référence à la variable de choix d'étude et positionnement
                    ax.set_axis_off()  # Masquer les axes s'il n'y a pas de données
                st.pyplot(fig)
                
            st.write("---")
            col_arc, col_scr, col_rand= st.columns([1, 1, 1])

            with col_arc:
                st.write(f"Temps total passé par ARC sur l'étude {study_choice} :")
                
                # Grouper les données par ARC et calculer le total
                total_time_by_arc = filtered_df_by_study.groupby('ARC')[TIME_INT_CAT].sum().sum(axis=1)
                
                # Vérifier si le DataFrame n'est pas vide
                if not total_time_by_arc.empty:
                    # Option 1: Afficher sous forme de tableau avec Markdown
                    markdown_table = "ARC | Heures Totales\n:- | -:\n"
                    for arc, total_hours in total_time_by_arc.items():
                        markdown_table += f"{arc} | {total_hours:.2f}\n"
                    st.markdown(markdown_table)
                else:
                    st.write("Aucune donnée disponible pour cette étude.")
            with col_scr:
                screened_pat = int(filtered_df_by_study['NB_PAT_SCR'].sum())
                st.metric(label="Nombre total de patients inclus", value=screened_pat)

            with col_rand:
                rando_pat = int(filtered_df_by_study['NB_PAT_RAN'].sum())
                st.metric(label="Nombre total de patients randomisés", value=rando_pat)

    # ----------------------------------------------------------------------------------------------------------
        with tab6:
            study_df = load_study_info()
            month_names = MONTHS
            previous_week, current_week, next_week, current_year, current_month = calculate_weeks()

            col_year, col_month, espace = st.columns([1, 3, 3])
            with col_year:
                year_choice = st.selectbox("Année", ANNEES, key=13, index=ANNEES.index(datetime.datetime.now().year))
            with col_month:
                # Assurez-vous que le choix du mois utilise une clé différente
                selected_month_name = st.select_slider("Mois", options=month_names, 
                                value=month_names[current_month - 1], key=16)
                # Convertir le nom du mois sélectionné en numéro
                month_choice = month_names.index(selected_month_name) + 1

            all_arcs_df = pd.DataFrame()
            for arc in ARC_PASSWORDS.keys():
                if arc is not None and not (isinstance(arc, float) and math.isnan(arc)):
                    try:
                        df_arc = load_data(arc)
                        df_arc['ARC'] = arc
                        all_arcs_df = pd.concat([all_arcs_df, df_arc], ignore_index=True)
                    except:
                        pass

            # Filtrage des données pour le tableau du mois
            first_day_of_month = datetime.datetime(year_choice, month_choice, 1)
            last_day_of_month = datetime.datetime(year_choice, month_choice + 1, 1) - datetime.timedelta(days=1)
            start_week = first_day_of_month.isocalendar()[1]
            end_week = last_day_of_month.isocalendar()[1]
            filtered_month_df = all_arcs_df[(all_arcs_df['YEAR'] == year_choice) & 
                                        (all_arcs_df['WEEK'] >= start_week) & 
                                        (all_arcs_df['WEEK'] <= end_week)]

            df_activities_month = filtered_month_df.groupby('STUDY')[TIME_INT_CAT].sum()
            df_activities_month['Total Time'] = df_activities_month.sum(axis=1)
            df_activities_month_sorted = df_activities_month.sort_values('Total Time', ascending=False)

            filtered_year_df = all_arcs_df[(all_arcs_df['YEAR'] == year_choice)]
            df_patient_included_year = filtered_year_df.groupby('STUDY').sum()

            col_graph1, col_graph2 = st.columns([3, 3])
            with col_graph1:
                create_bar_chart(df_activities_month_sorted, 'Heures Passées par Étude', selected_month_name)
            with col_graph2:
                df_patient_included_month = filtered_month_df.groupby('STUDY').sum()
                create_bar_chart(df_patient_included_month, "Nombre d'inclusions", selected_month_name, 'NB_PAT_SCR')
            
            metrics_year, metrics_month, metrics_suivi = st.columns([3, 3, 3])
            with metrics_year:
                nb_incl = int(df_patient_included_year['NB_PAT_SCR'].sum())
                st.metric(label=f"Nombre total de patients inclus en {year_choice}", value=nb_incl)

            with metrics_month: 
                nb_incl = int(df_patient_included_month['NB_PAT_SCR'].sum())
                st.metric(label=f"Nombre total de patients inclus en {selected_month_name} {year_choice}", value=nb_incl)

            with metrics_suivi:
                nb_incl = int(df_patient_included_month['NB_PAT_SCR'].sum())
                nb_eos = int(df_patient_included_month['NB_EOS'].sum())
                st.metric(label=f"Nombre total de patients suivi en {selected_month_name} {year_choice}", value=nb_incl-nb_eos)

#####################################################################
# ====================== LANCEMENT DE L'ALGO ====================== #
#####################################################################

if __name__ == "__main__":
    main()
