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
from io import StringIO, BytesIO
import math


#####################################################################
# =========================== CONSTANTS =========================== #
#####################################################################

ARC_PASSWORDS_FILE = "ARC_MDP.csv"
STUDY_INFO_FILE = "STUDY.csv"
# PASSWORD = os.getenv('APP_MDP')
PASSWORD = "Masa2024"
YEARS = list(range(2024, 2030))
CATEGORIES = ['YEAR', 'WEEK', 'STUDY', 'TOTAL', 'MISE EN PLACE', 'TRAINING', 'VISITES', 'SAISIE CRF', 'QUERIES', 'MONITORING', 'REMOTE', 'REUNIONS', 
'ARCHIVAGE EMAIL', 'MAJ DOC', 'AUDIT & INSPECTION', 'CLOTURE', 'NB_VISITE', 'NB_PAT_SCR', 'NB_PAT_RAN', 'NB_EOS', 'COMMENTAIRE']
INT_CATEGORIES = CATEGORIES[3:-1]
TIME_INT_CAT = CATEGORIES[3:-5]
ACTION_CAT = CATEGORIES[4:-5]
MONTHS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
SHAPE_BOX = {
    "ha": 'center', 
    "va": 'center', 
    "fontsize": 12, 
    "color": 'darkorange',
    "bbox": dict(facecolor='none', edgecolor='darkorange', boxstyle='round,pad=0.5')}


#####################################################################
# ========================= GENERAL INFO ========================== #
#####################################################################

def load_csv_from_local(file_name, sep=';', encoding='utf-8'):
    """
    Loads a CSV file from the local "imotion" folder and converts it into a pandas DataFrame.

    Parameters:
    - file_name (str): The name of the file to load.
    - sep (str, optional): The column separator in the CSV file. Defaults to ';'.
    - encoding (str, optional): The encoding of the CSV file. Defaults to 'utf-8'.

    Returns:
    - pandas.DataFrame: A DataFrame containing the data from the loaded CSV file.
    """
    file_path = os.path.join("imotion", file_name)
    try:
        return pd.read_csv(file_path, encoding=encoding, sep=sep)
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding='latin1', sep=sep)
    except FileNotFoundError:
        return None
        

# Creating a "viridis" palette with the appropriate number of colors
viridis_palette = sns.color_palette("viridis", len(TIME_INT_CAT))

# Mapping categories to "viridis" palette colors
category_colors = {category: color for category, color in zip(TIME_INT_CAT, viridis_palette)}

def load_arc_passwords():
    """
    Loads ARC passwords from a CSV file stored in an S3 bucket.

    Returns:
    - dict: A dictionary where the keys are ARC names and the values are their corresponding passwords.
    """
    try:
        # Try loading the file with UTF-8 encoding
        df = load_csv_from_local(ARC_PASSWORDS_FILE, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        # If an encoding error occurs, try loading with Latin1 encoding
        df = load_csv_from_local(ARC_PASSWORDS_FILE, sep=';', encoding='latin1')

    # Verify if df is not None and has the expected columns
    if df is not None and 'ARC' in df.columns and 'MDP' in df.columns:
        return dict(zip(df['ARC'], df['MDP']))
    else:
        st.write("Error: The DataFrame is empty or missing required columns.")
        return {}  # Return an empty dictionary if df is None or missing columns

ARC_PASSWORDS = load_arc_passwords()


#####################################################################
# ===================== ASSISTANCE FUNCTIONS ====================== #
#####################################################################

# ========================================================================================================================================
# DATA LOADING
def load_data(arc):
    """
    Loads data for a specific ARC from a CSV file stored in an S3 bucket.

    Parameters:
    - arc (str): The ARC identifier for which data should be loaded.

    Returns:
    - pandas.DataFrame: A DataFrame containing the loaded data for the specified ARC. If an encoding error
                         occurs, tries to reload the data with a different encoding.
    """
    file_name = f"Time_{arc}.csv"
    try:
        # Try loading the file with UTF-8 encoding
        return load_csv_from_local(file_name, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        # If an encoding error occurs, try loading with Latin1 encoding
        return load_csv_from_local(file_name, sep=';', encoding='latin1')

def load_all_study_names():
    """
    Lists all unique study names from CSV files prefixed with "Time_" in the local "imotion" folder.

    Returns:
    - list: A sorted list of unique study names.
    """
    folder_path = "imotion"  # Chemin du dossier contenant les fichiers CSV
    unique_studies = set()

    # Vérifier que le dossier existe
    if not os.path.exists(folder_path):
        return []

    # Parcourir tous les fichiers du dossier
    for file_name in os.listdir(folder_path):
        if file_name.startswith("Time_") and file_name.endswith(".csv"):
            file_path = os.path.join(folder_path, file_name)

            # Charger le fichier CSV
            df = pd.read_csv(file_path, sep=';', encoding='utf-8')

            if not df.empty and "STUDY" in df.columns:
                unique_studies.update(df['STUDY'].dropna().unique())

    return sorted(list(unique_studies))

def load_arc_info():
    """
    Loads ARC information from a CSV file stored in S3.

    Returns:
    - pandas.DataFrame: A DataFrame containing ARC information.
    """
    return load_csv_from_local(ARC_PASSWORDS_FILE, sep=';', encoding='utf-8')

def load_study_info():
    """
    Loads study information from a specific CSV file in S3.

    Returns:
    - pandas.DataFrame: A DataFrame containing study information.
    """
    # Use the load_csv_from_local function with the file name STUDY_INFO_FILE and appropriate parameters
    return load_csv_from_local(STUDY_INFO_FILE, sep=';', encoding='utf-8')

# ========================================================================================================================================
# SAVE
def save_data_to_local(file_name, df):
    """
    Saves a DataFrame to a CSV file in the local "imotion" folder.

    Parameters:
    - file_name (str): The name under which the file will be saved.
    - df (pandas.DataFrame): The DataFrame to be saved.
    """
    file_path = os.path.join("imotion", file_name)
    df.to_csv(file_path, index=False, sep=';', encoding='utf-8')


def convert_df_to_excel(df):
    """
    Convert a DataFrame to an Excel file and return as a BytesIO object.

    Parameters:
    - df (DataFrame): The DataFrame to convert.

    Returns:
    - BytesIO: The Excel file in memory.
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Studies')
    output.seek(0)
    return output

# ========================================================================================================================================
# GRAPH AND DISPLAY
def create_bar_chart(data, title, week_or_month, y='Total Time', y_axis="Nombre d'heure(s)"):
    """
    Creates and displays a bar chart from the provided data.

    Parameters:
    - data (pandas.DataFrame): The data to be displayed in the chart.
    - title (str): The title of the chart.
    - week_or_month (str): A string indicating whether the chart is for a week or a month.
    - y (str, optional): The column of data that will be used for the bar values. Default to 'Total Time'.
    - y_axis (str, optional): The title of the y-axis. Default to "Hours".

    Returns:
    None
    """
    fig, ax = plt.subplots(figsize=(10, 4))

    # Defining the order of categories and corresponding colors
    category_order = data.index.tolist()
    color_palette = sns.color_palette("viridis", len(category_order))

    # Mapping colors to categories
    color_mapping = dict(zip(category_order, color_palette))

    # Creating the bar chart with the defined color order
    sns.barplot(x=data.index, y=y, data=data, ax=ax, palette=color_mapping)
    ax.set_title(f'{title} pour {week_or_month}')
    ax.set_xlabel('')
    ax.set_ylabel(y_axis)
    ax.set_ylim(0, None)  # None means the upper limit will be set automatically based on the data
    ax.xaxis.set_ticks_position('none') 
    ax.yaxis.set_ticks_position('none')
    sns.despine(left=False, bottom=False)
    plt.xticks(rotation=45, ha='right')
    st.pyplot(fig)

def plot_pie_chart_on_ax(df_study_sum, title, ax):
    """
    Draws a pie chart on a specified matplotlib axis, representing the sum of hours spent per task category.

    Parameters:
    - df_study_sum (pandas.Series): A pandas series containing the sum of hours spent per task category.
    - title (str): The title of the pie chart.
    - ax (matplotlib.axes.Axes): The matplotlib axis to draw the pie chart on.

    Returns:
    None
    """
    colors = [category_colors[cat] for cat in df_study_sum.index if cat in category_colors]
    
    wedges, texts, autotexts = ax.pie(df_study_sum, labels=df_study_sum.index, autopct=lambda p: '{:.0f}'.format(p * df_study_sum.sum() / 100), startangle=140, colors=colors)
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_size(10)
    
    ax.set_title(title)

def generate_charts_for_time_period(df, studies, period, period_label):
    """
    Generates pie charts for each selected study over a given period.

    Parameters:
    - df (pandas.DataFrame): DataFrame containing the data to be displayed.
    - studies (list): List of study names to include in the charts.
    - period (str/int): The period for which to generate the charts (e.g., week number or month name).
    - period_label (str): A string describing the period (e.g., "Week" or "Month").

    Returns:
    None
    """
    st.write(f"Données pour {period_label} {period}")
    
    if len(studies) > 0:
        nrows = (len(studies) + 1) // 2 if len(studies) % 2 else len(studies) // 2
        fig, axs = plt.subplots(nrows=nrows, ncols=2, figsize=(10, 5 * nrows))
        axs = axs.flatten()  # Flatten the axes array for easy access

        for i, study in enumerate(studies):
            df_study = df[df['STUDY'] == study]
            df_study_sum = df_study[ACTION_CAT].fillna(0).sum()
            df_study_sum = df_study_sum[df_study_sum > 0]

            if df_study_sum.sum() > 0:
                plot_pie_chart_on_ax(df_study_sum, f'Actions par Tâche pour {study}', axs[i])
            else:
                # Add text with rounded box
                axs[i].text(0.5, 0.5, f"Aucune donnée disponible\npour {study}", **SHAPE_BOX)
                axs[i].set_axis_off()  # Hide axes if no data

        # Hide extra axes if not used
        for j in range(i + 1, len(axs)):
            axs[j].axis('off')

        plt.tight_layout()
        st.pyplot(fig) 
    else:
        st.warning("Aucune étude sélectionnée ou aucune donnée disponible pour les études sélectionnées.")

def process_and_display_data(df, period_label, period_value):
    """
    Processes the provided data and displays a summary and charts.

    Parameters:
    - df (pandas.DataFrame): The DataFrame containing the data to process and display.
    - period_label (str): The label of the period (e.g., "week" or "month").
    - period_value (str/int): The specific value of the period (e.g., week number or month name).

    Returns:
    None
    """
    df_activities = df.groupby('STUDY')[TIME_INT_CAT].sum()
    df_activities['Total Time'] = df_activities['TOTAL']
    df_activities_sorted = df_activities.sort_values('Total Time', ascending=False)
    create_bar_chart(df_activities_sorted, f'Heures Passées par Étude', f'{period_label} {period_value}')
    
    # Calculating and displaying total time spent and total number of visits
    total_time_spent = int(df_activities_sorted['TOTAL'].sum())
    unit = "heure" if total_time_spent <= 1 else "heures"
    total_visits = int(sum(df['NB_VISITE']))
    
    time, visit = st.columns(2)
    with time:
        st.metric(label="Temps total passé", value=f"{total_time_spent} {unit}")
    with visit:
        st.metric(label="Nombre total de visites", value=f"{total_visits}")

def generate_time_series_chart(data_dict, title_prefix, mode='year'):
    """
    Generates a time series chart for the provided data, either by ARC or by study.

    Parameters:
    - data_dict (dict): A dictionary containing the data to plot, with ARC or study names as keys.
    - title_prefix (str): Prefix for the chart title.
    - mode (str): Indicates whether the chart should be generated for 'year' or 'last_5_weeks'.

    Returns:
    None
    """
    if not data_dict:
        st.error("Aucune donnée disponible pour l'affichage du graphique.")
        return

    _, current_week, _, current_year, _ = calculate_weeks()
    if mode == 'year':
        total_weeks = 52 if datetime.date(current_year, 12, 31).isocalendar()[1] == 1 else 53
    else:
        total_weeks = current_week  # Stops at the current week for 'last_5_weeks' mode
    
    fig, ax = plt.subplots(figsize=(12, 6))
    for arc, data in data_dict.items():
        if mode == 'year':
            filtered_data = data[data['WEEK'] <= current_week]  # For the year, stops at the current week
        else:
            filtered_data = data  # For the last 5 weeks, uses all available data
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
# CALCULATIONS
def calculate_weeks():
    """
    Calculates and returns the numbers of the previous, current, and next week, the current year, and month.

    Returns:
    - tuple: Contains the numbers of the previous, current, and next week, the current year, and month.
    """
    current_date = datetime.datetime.now()
    current_week = current_date.isocalendar()[1]
    previous_week = current_week - 1 if current_week > 1 else 52
    next_week = current_week + 1 if current_week < 52 else 1
    current_year = current_date.year
    current_month = current_date.month
    return previous_week, current_week, next_week, current_year, current_month

# ========================================================================================================================================
# CREATION AND MODIFICATION
def create_time_files_for_arcs(df):
    """
    Checks and creates, if necessary, an empty CSV file for each ARC mentioned in a DataFrame, in the local "imotion" folder.

    Parameters:
    - df (pandas.DataFrame): DataFrame containing at least one 'ARC' column with ARC names.

    Returns:
    None
    """
    os.makedirs("imotion", exist_ok=True)  # Assure que le dossier existe

    for arc_name in df['ARC'].dropna().unique():  # Filtrer les valeurs NaN et obtenir des noms uniques
        file_path = os.path.join("imotion", f"Time_{arc_name}.csv")
        
        if not os.path.exists(file_path):  # Vérifie si le fichier existe déjà
            new_df = pd.DataFrame(columns=CATEGORIES)  # Crée un nouveau DataFrame avec les colonnes souhaitées
            new_df.to_csv(file_path, index=False, sep=';', encoding='utf-8')  # Sauvegarde en local

def create_ongoing_files_for_arcs(df):
    """
    Checks and creates, if necessary, an empty ongoing CSV file for each ARC mentioned in a DataFrame, in the local "imotion" folder.

    Parameters:
    - df (pandas.DataFrame): DataFrame containing at least one 'ARC' column with ARC names.

    Returns:
    None
    """
    os.makedirs("imotion", exist_ok=True)  # S'assurer que le dossier "imotion" existe

    for arc_name in df['ARC'].dropna().unique():  # Filtrer les valeurs NaN et obtenir des noms uniques
        file_path = os.path.join("imotion", f"Ongoing_{arc_name}.csv")
        
        if not os.path.exists(file_path):  # Vérifier si le fichier existe déjà
            new_df = pd.DataFrame(columns=CATEGORIES)  # Créer un nouveau DataFrame avec les colonnes souhaitées
            new_df.to_csv(file_path, index=False, sep=';', encoding='utf-8')  # Sauvegarde locale


def add_row_to_df_local(file_name, df, **kwargs):
    """
    Adds a new row to a DataFrame and saves the updated DataFrame to a CSV file locally in the "imotion" folder.

    Parameters:
    - file_name (str): The name of the CSV file.
    - df (pandas.DataFrame): The DataFrame to which the new row will be added.
    - **kwargs: The values of the new row to add.

    Returns:
    - pandas.DataFrame: The updated DataFrame.
    """
    file_path = os.path.join("imotion", file_name)

    # S'assurer que le dossier "imotion" existe
    os.makedirs("imotion", exist_ok=True)

    # Créer une nouvelle ligne à partir des kwargs
    new_row = pd.DataFrame([kwargs])

    # Ajouter la nouvelle ligne au DataFrame existant
    df = pd.concat([df, new_row], ignore_index=True)

    # Sauvegarder le DataFrame mis à jour en local
    df.to_csv(file_path, index=False, sep=';', encoding='utf-8')

    return df


def delete_row_local(file_name, df, row_to_delete):
    """
    Deletes a specific row from a DataFrame and updates the corresponding CSV file locally in the "imotion" folder.

    Parameters:
    - file_name (str): The name of the CSV file.
    - df (pandas.DataFrame): The DataFrame from which to delete the row.
    - row_to_delete (int): The index of the row to delete in the DataFrame.

    Returns:
    - pandas.DataFrame: The DataFrame after deleting the row.
    """
    file_path = os.path.join("imotion", file_name)

    # Vérifier que l'index existe dans le DataFrame avant de le supprimer
    if row_to_delete in df.index:
        df = df.drop(row_to_delete).reset_index(drop=True)  # Supprime la ligne et réindexe proprement

        # Sauvegarder le DataFrame mis à jour en local
        df.to_csv(file_path, index=False, sep=';', encoding='utf-8')

    return df


#####################################################################
# ========================= MAIN FUNCTION ========================= #
#####################################################################

def main():
    """
    Main function running the Streamlit application. Configures the page, handles authentication, and displays different dashboards.

    Returns:
    None
    """
    try:
        st.set_page_config(layout="wide", page_icon="📊", page_title="I-Motion Adulte - Espace Chef de Projet")
                
    except:
        pass

    # Initializing st.session_state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        _, col_password, _ = st.columns([2, 3, 2])
        with col_password:
            password_input = st.text_input("Entrez le mot de passe", type="password")

            if password_input == PASSWORD:
                st.session_state.authenticated = True
            else:
                st.write("Mot de passe incorrect. Veuillez réessayer.")

    if st.session_state.authenticated:
        col_title, col_logout = st.columns([8, 1])

        with col_title:
            st.title("I-Motion Adulte - Espace Chefs de Projets")

        with col_logout:
            if st.button("Se déconnecter"):
                st.session_state.authenticated = False
                st.rerun()
        st.write("---")

        # Selection tab
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["👥 Gestion - ARCs", "📚 Gestion - Etudes", "📈 Dashboard - par ARC", "📊 Dashboard - tous ARCs",  "📈 Dashboard - par Etude", "📊 Dashboard - toutes Etudes"])

    # ----------------------------------------------------------------------------------------------------------
        with tab1:
            arc_df = load_arc_info()

            col_add, _, col_delete, _, col_modify = st.columns([3, 1, 3, 1, 3])
            with col_add:
                st.markdown("#### Ajout d'un nouvel ARC")
                new_arc_name = st.text_input("Nom du nouvel ARC", key="new_arc_name")
                new_arc_password = st.text_input("Mot de passe pour le nouvel ARC", key="new_arc_mdp")
                if st.button("Ajouter l'ARC"):
                    if new_arc_name and new_arc_password:  # Check if fields are not empty
                        arc_df = add_row_to_df_local(ARC_PASSWORDS_FILE, arc_df, ARC=new_arc_name, MDP=new_arc_password)
                        create_time_files_for_arcs(arc_df)
                        create_ongoing_files_for_arcs(arc_df) 
                        st.success(f"Nouvel ARC '{new_arc_name}' ajouté avec succès.")
                        st.rerun()
                    else:
                        st.error("Veuillez remplir le nom de l'ARC et le mot de passe.")

            with col_delete:
                st.markdown("#### Archivage d'un ARC")
                arc_options = arc_df['ARC'].dropna().astype(str).tolist()
                arc_to_delete = st.selectbox("Choisir un ARC à archiver", sorted(arc_options))
                if st.button("Archiver l'ARC sélectionné"):
                    arc_df = delete_row_local(arc_df, arc_df[arc_df['ARC'] == arc_to_delete].index)
                    st.success(f"ARC '{arc_to_delete}' archivé avec succès.")
                    st.rerun()

            with col_modify:
                st.markdown("#### Gestion des mots de passe")
                for i, row in arc_df.iterrows():
                    with st.expander(f"{row['ARC']}"):
                        new_password = st.text_input("New password", value=row['MDP'], key=f"password_{i}")
                        # Update the DataFrame in session_state if the password changes
                        if new_password != row['MDP']:
                            arc_df.at[i, 'MDP'] = new_password
                # Button to save changes
                if st.button('Sauvegarder les modifications'):
                    save_data_to_local(ARC_PASSWORDS_FILE, arc_df)
                    st.success('Modifications sauvegardées avec succès.')
                    st.rerun()

    # ----------------------------------------------------------------------------------------------------------
        with tab2:
            study_df = load_study_info()
            arc_options = arc_df['ARC'].dropna().astype(str).tolist()
            arc_options = sorted(arc_options) + ['Aucun']  # Replace 'nan' with 'Aucun'

            col_add, _, col_delete, _, col_modify = st.columns([3, 1, 3, 1, 3])
            with col_add:
                st.markdown("#### Ajout d'une nouvelle étude")
                new_study_name = st.text_input("Nom de l'étude", key="new_study_name")
                new_study_primary_arc = st.selectbox(f"ARC Principal", arc_options, key="new_study_arc_principal")
                new_study_backup_arc = st.selectbox("ARC de backup (optionnel)", arc_options, key=f"new_study_arc_backup", help="Optionnel")

                col_add, col_list = st.columns(2)
                with col_add:
                    if st.button("Ajouter l'étude"):
                        if new_study_name and new_study_primary_arc:  # Minimal validation
                            # Adding the new study
                            study_df = add_row_to_df_local(STUDY_INFO_FILE, study_df,
                                                     STUDY=new_study_name, 
                                                     ARC=new_study_primary_arc, 
                                                     ARC_BACKUP=new_study_backup_arc if new_study_backup_arc else "")
                            st.success(f"Nouvelle étude '{new_study_name}' ajoutée avec succès.")
                            st.rerun()
                        else:
                            st.error("Le nom de l'étude et l'ARC principal sont requis.")
                with col_list:
                    study_names = load_all_study_names()
                    study_names_df = pd.DataFrame(study_names, columns=['Study Name'])
                    excel_data = convert_df_to_excel(study_names_df)
                    st.download_button(
                        label="Liste des études en cours et archivées",
                        data=excel_data,
                        file_name='liste_etudes.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )


            with col_delete:
                st.markdown("#### Archivage d'une étude")
                study_options = study_df['STUDY'].dropna().astype(str).tolist()
                study_to_delete = st.selectbox("Choisir une étude à archiver", sorted(study_options))
                if st.button("Archiver l'étude sélectionnée"):
                    study_df = delete_row_local(STUDY_INFO_FILE ,study_df, study_df[study_df['STUDY'] == study_to_delete].index)
                    st.success(f"L'étude '{study_to_delete}' est archivée avec succès.")
                    st.rerun()

            with col_modify:
                st.markdown("#### Affectation des études")
                for i, row in study_df.iterrows():
                    with st.expander(f"{row['STUDY']}"):
                        # Find the index of the current primary ARC in the options, treating 'nan' as 'None'
                        current_primary_arc = 'Aucun' if pd.isna(row['ARC']) else row['ARC']
                        primary_arc_index = arc_options.index(current_primary_arc) if current_primary_arc in arc_options else len(arc_options) - 1
                        # Select the primary ARC with the found index
                        new_primary_arc = st.selectbox(f"ARC Principal pour {row['STUDY']}", arc_options, index=primary_arc_index, key=f"primary_{i}")
                        
                        # Find the index of the current backup ARC in the options, treating 'nan' as 'None'
                        current_backup_arc = 'Aucun' if pd.isna(row['ARC_BACKUP']) else row['ARC_BACKUP']
                        backup_arc_index = arc_options.index(current_backup_arc) if current_backup_arc in arc_options else len(arc_options) - 1
                        # Select the backup ARC with the found index
                        new_backup_arc = st.selectbox(f"ARC Backup pour {row['STUDY']}", arc_options, index=backup_arc_index, key=f"backup_{i}", help="Optionnel")

                        # Before saving, replace 'None' with np.nan
                        study_df.at[i, 'ARC'] = np.nan if new_primary_arc == 'Aucun' else new_primary_arc
                        study_df.at[i, 'ARC_BACKUP'] = np.nan if new_backup_arc == 'Aucun' else new_backup_arc

                # Global button to save all modifications
                if st.button('Sauvegarder les modifications', key=19):
                    save_data_to_local(STUDY_INFO_FILE, study_df)
                    st.success('Modifications sauvegardées avec succès.')
                    st.rerun() 

    # ----------------------------------------------------------------------------------------------------------
        with tab3:
            col_arc, col_year, _, _ = st.columns(4)

            with col_arc:
                arc = st.selectbox("Choix de l'ARC", list(ARC_PASSWORDS.keys()), key=2)

            with col_year:
                year_choice = st.selectbox("Année", YEARS, key=3, index=YEARS.index(datetime.datetime.now().year))

            # I. Data Loading
            df_data = load_data(arc)
            previous_week, current_week, next_week, current_year, current_month = calculate_weeks()

            associated_studies = df_data['STUDY'].unique().tolist()
            filtered_studies_df = study_df[study_df['STUDY'].isin(associated_studies)]
            associated_studies = filtered_studies_df['STUDY'].unique().tolist()

            # List of month names
            month_names = MONTHS

            # II. User Interface for Year, Month, and Week selection
            col_week, _, col_month = st.columns([1, 0.25, 1])
            with col_week:
                week_choice = st.slider("Semaine", 1, 52, current_week, key=4)
            with col_month:
                # Ensure month choice uses a different key
                selected_month_name = st.select_slider("Mois", options=month_names, 
                                value=month_names[current_month - 1], key=6)
                # Convert selected month name to number
                month_choice = month_names.index(selected_month_name) + 1

            # Data filtering for Week table
            filtered_week_df = df_data[(df_data['YEAR'] == year_choice) & (df_data['WEEK'] == week_choice)]

            # Data filtering for Month table
            first_day_of_month = datetime.datetime(year_choice, month_choice, 1)
            last_day_of_month = datetime.datetime(year_choice, month_choice + 1, 1) - datetime.timedelta(days=1)
            start_week = first_day_of_month.isocalendar()[1]
            end_week = last_day_of_month.isocalendar()[1]
            filtered_month_df = df_data[(df_data['YEAR'].astype(int) == year_choice) & 
                                (df_data['WEEK'].astype(int) >= start_week) & 
                                (df_data['WEEK'].astype(int) <= end_week)]

            # Convert some columns to integers for both tables
            filtered_week_df[TIME_INT_CAT] = filtered_week_df[TIME_INT_CAT].astype(int)
            filtered_month_df[TIME_INT_CAT] = filtered_month_df[TIME_INT_CAT].astype(int)

            # Using the function for weekly data
            with col_week:
                process_and_display_data(filtered_week_df, "semaine", week_choice)

            # Using the function for monthly data
            with col_month:
                process_and_display_data(filtered_month_df, "mois", selected_month_name)

            st.write("---")

            # Study selection with multiselect
            sel_studies = st.multiselect("Choisir une ou plusieurs études", options=associated_studies, default=associated_studies, key=10)
            num_studies = len(sel_studies)

            # Calculate the number of rows needed for two columns
            nrows = (num_studies + 1) // 2 if num_studies % 2 else num_studies // 2

            # Create main columns for weeks and months
            col_week, col_month = st.columns(2)

            # Generate charts for the week in the left column
            with col_week:
                generate_charts_for_time_period(filtered_week_df, sel_studies, week_choice, "la semaine")

            # Repeat the same structure for the month in the right column
            with col_month:
                generate_charts_for_time_period(filtered_month_df, sel_studies, selected_month_name, "")

    # ----------------------------------------------------------------------------------------------------------
        with tab4:
            arcs = list(ARC_PASSWORDS.keys())

            previous_week, current_week, next_week, current_year, current_month = calculate_weeks()

            # Use current_year instead of directly using 2024
            last_5_weeks = [(current_week - i - 1) % 52 + 1 for i in range(5)]
            all_weeks_current_year = np.arange(1, 53)  # All weeks for the current year
            dfs = {}  # To store the DataFrames

            for arc in arcs:
                if arc is not None and not (isinstance(arc, float) and math.isnan(arc)):
                    try:
                        df_arc = load_data(arc)
                        df_arc['Total Time'] = df_arc['TOTAL']
                        df_arc = df_arc.groupby(['YEAR', 'WEEK'])['Total Time'].sum().reset_index()
                        
                        # Prepare a DataFrame with all weeks for the last 5 weeks with default values as 0
                        df_all_last_5_weeks = pd.DataFrame({'YEAR': current_year, 'WEEK': last_5_weeks, 'Total Time': 0}).merge(
                            df_arc[(df_arc['YEAR'] == current_year) & (df_arc['WEEK'].isin(last_5_weeks))],
                            on=['YEAR', 'WEEK'], how='left', suffixes=('', '_y')).fillna(0)
                        df_all_last_5_weeks['Total Time'] = df_all_last_5_weeks[['Total Time', 'Total Time_y']].max(axis=1)
                        df_all_last_5_weeks.drop(columns=['Total Time_y'], inplace=True)
                        
                        # Prepare a DataFrame for all weeks of the current year with default values as 0
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
            
            # For the chart of the last 5 weeks
            with col_month:
                generate_time_series_chart({arc: data['last_5_weeks'] for arc, data in dfs.items()}, "Évolution Hebdomadaire", mode='last_5_weeks')

            # For the chart of the current year
            with col_year:
                generate_time_series_chart({arc: data['current_year'] for arc, data in dfs.items()}, f"Évolution Hebdomadaire en {current_year}", mode='year')

    # ----------------------------------------------------------------------------------------------------------
        with tab5:
            # Study selection
            study_names = load_all_study_names()
            study_choice = st.selectbox("Choisissez votre étude (en cours et archivées)", study_names)

            # Loading and combining data from all ARCs
            all_arcs_df = pd.DataFrame()
            for arc in ARC_PASSWORDS.keys():
                if arc is not None and not (isinstance(arc, float) and math.isnan(arc)):
                    try:
                        df_arc = load_data(arc)
                        df_arc['ARC'] = arc
                        all_arcs_df = pd.concat([all_arcs_df, df_arc], ignore_index=True)
                    except:
                        pass

            # Filtering data by selected study
            filtered_df_by_study = all_arcs_df[all_arcs_df['STUDY'] == study_choice]

            # Ensure that columns of interest are of numeric type for calculation
            filtered_df_by_study[TIME_INT_CAT] = filtered_df_by_study[TIME_INT_CAT].apply(pd.to_numeric, errors='coerce')

            # Calculate total time spent by activity category for the selected study
            total_time_by_category = filtered_df_by_study[ACTION_CAT].sum()

            # Using st.columns to divide display space
            col_table, _, col_graph = st.columns([1.5, 0.2, 2])

            with col_table:
                st.write(f"Temps passé sur l'étude {study_choice}, par catégorie d'activité :")
                
                # Start with a Markdown header for the table
                markdown_table = "Catégorie | Actions réalisées\n:- | -:\n"
                
                # Add each category and corresponding time in Markdown format
                for category, hours in total_time_by_category.items():
                    if category != "TOTAL":
                        markdown_table += f"{category} | {int(hours)}\n"
                
                # Display the formatted table in Markdown
                st.markdown(markdown_table)

            with col_graph:
                # Preparation and display of pie chart in the second column
                fig, ax = plt.subplots()
                # Ensure total_time_by_category is defined before this line
                total_time_by_category = total_time_by_category[total_time_by_category > 0]
                if total_time_by_category.sum() > 0:
                    plot_pie_chart_on_ax(total_time_by_category, f"Répartition des actions par catégorie pour l'étude {study_choice}", ax)
                else:
                    ax.text(0.5, 0.5, f"Aucune donnée disponible\npour {study_choice}", ha='center', va='center', transform=ax.transAxes) # Correct reference to study choice variable and positioning
                    ax.set_axis_off()  # Hide axes if no data
                st.pyplot(fig)
                
            st.write("---")
            col_arc, col_scr, col_rand, col_eos, col_calc= st.columns([2, 1, 1, 1, 1])

            with col_arc:
                st.write(f"Temps total passé par ARC sur l'étude {study_choice} :")
                
                # Group data by ARC and calculate total
                total_time_by_arc = filtered_df_by_study.groupby('ARC')['TOTAL'].sum()
                
                # Check if DataFrame is not empty
                if not total_time_by_arc.empty:
                    # Option 1: Display as table using Markdown
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

            with col_eos:
                eos_pat = int(filtered_df_by_study['NB_EOS'].sum())
                st.metric(label="Nombre total de patients EOS", value=eos_pat)

            with col_calc:
                calc_pat = rando_pat - eos_pat
                st.metric(label="Nombre total de patients en cours de suivi", value=calc_pat)

    # ----------------------------------------------------------------------------------------------------------
        with tab6:
            study_df = load_study_info()
            month_names = MONTHS
            previous_week, current_week, next_week, current_year, current_month = calculate_weeks()

            col_year, col_month, _ = st.columns([1, 3, 3])
            with col_year:
                year_choice = st.selectbox("Année", YEARS, key=13, index=YEARS.index(datetime.datetime.now().year))
            with col_month:
                # Ensure the month choice uses a different key
                selected_month_name = st.select_slider("Mois", options=month_names, 
                                value=month_names[current_month - 1], key=16)
                # Convert selected month name to number
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

            # Filtering data for the month table
            first_day_of_month = datetime.datetime(year_choice, month_choice, 1)
            last_day_of_month = datetime.datetime(year_choice, month_choice + 1, 1) - datetime.timedelta(days=1)
            start_week = first_day_of_month.isocalendar()[1]
            end_week = last_day_of_month.isocalendar()[1]
            filtered_month_df = all_arcs_df[(all_arcs_df['YEAR'] == year_choice) & 
                                        (all_arcs_df['WEEK'] >= start_week) & 
                                        (all_arcs_df['WEEK'] <= end_week)]

            df_activities_month = filtered_month_df.groupby('STUDY')[TIME_INT_CAT].sum()
            df_activities_month['Total Time'] = df_activities_month['TOTAL']
            df_activities_month_sorted = df_activities_month.sort_values('Total Time', ascending=False)

            filtered_year_df = all_arcs_df[(all_arcs_df['YEAR'] == year_choice)]
            df_patient_included_year = filtered_year_df.groupby('STUDY').sum()

            col_graph1, col_graph2 = st.columns([3, 3])
            with col_graph1:
                create_bar_chart(df_activities_month_sorted, 'Heures Passées par Étude', selected_month_name)
            with col_graph2:
                df_patient_included_month = filtered_month_df.groupby('STUDY').sum()
                create_bar_chart(df_patient_included_month, "Nombre d'inclusions", selected_month_name, 'NB_PAT_SCR', y_axis="")
            
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
# ========================== ALGO LAUNCH ========================== #
#####################################################################

if __name__ == "__main__":
    main()
