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
# =========================== CONSTANTS =========================== #
#####################################################################

BUCKET_NAME = "bucketidb"
ARC_PASSWORDS_FILE = "ARC_MDP.csv"
STUDY_INFO_FILE = "STUDY.csv"
PASSWORD = st.secrets["APP_MDP"]
YEARS = list(range(2024, 2030))
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
    "bbox": dict(facecolor='none', edgecolor='darkorange', boxstyle='round,pad=0.5')}


#####################################################################
# ========================= GENERAL INFO ========================== #
#####################################################################

s3_client = boto3.client(
    's3',
    aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY']
)

def load_csv_from_s3(bucket_name, file_name, sep=';', encoding='utf-8'):
    """
    Loads a CSV file from a specified S3 bucket and converts it into a pandas DataFrame.

    Parameters:
    - bucket_name (str): The name of the S3 bucket from which to load the file.
    - file_name (str): The name of the file to load.
    - sep (str, optional): The column separator in the CSV file. Defaults to ';'.
    - encoding (str, optional): The encoding of the CSV file. Defaults to 'utf-8'.

    Returns:
    - pandas.DataFrame: A DataFrame containing the data from the loaded CSV file.
                         Returns None if loading fails.
    """
    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key=file_name)
        body = obj['Body'].read().decode(encoding)
        
        try:
            # Try reading the file with utf-8 encoding
            return pd.read_csv(StringIO(body), encoding='utf-8', sep=sep)
        except UnicodeDecodeError:
            return pd.read_csv(StringIO(body), encoding='latin1', sep=sep)
        except FileNotFoundError:
            return None
    except:
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
        df = load_csv_from_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        # If an encoding error occurs, try loading with Latin1 encoding
        df = load_csv_from_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, sep=';', encoding='latin1')
    return dict(zip(df['ARC'], df['MDP']))

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
        return load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        # If an encoding error occurs, try loading with Latin1 encoding
        return load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='latin1')

def load_all_study_names(bucket_name):
    """
    Lists all unique study names from CSV files prefixed with "Time_" in a specified S3 bucket.

    Parameters:
    - bucket_name (str): The name of the S3 bucket to query.

    Returns:
    - list: A sorted list of unique study names.
    """
    # Use boto3 to list objects in the S3 bucket
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix="Time_")
    
    # Set to store unique study names
    unique_studies = set()

    if 'Contents' in response:
        # Iterate over each file that starts with "Time_"
        for obj in response['Contents']:
            file_key = obj['Key']
            arc_name = file_key.split('_')[1].split('.')[0]  # Extract the ARC name from the file name in the bucket
            
            # Load data from S3
            df = load_csv_from_s3(bucket_name, file_key, sep=';', encoding='utf-8')
            if not df.empty:
                unique_studies.update(df['STUDY'].unique())
    
    return sorted(list(unique_studies))

def load_arc_info():
    """
    Loads ARC information from a CSV file stored in S3.

    Returns:
    - pandas.DataFrame: A DataFrame containing ARC information.
    """
    return load_csv_from_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, sep=';', encoding='utf-8')

def load_study_info():
    """
    Loads study information from a specific CSV file in S3.

    Returns:
    - pandas.DataFrame: A DataFrame containing study information.
    """
    # Use the load_csv_from_s3 function with the file name STUDY_INFO_FILE and appropriate parameters
    return load_csv_from_s3(BUCKET_NAME, STUDY_INFO_FILE, sep=';', encoding='utf-8')

# ========================================================================================================================================
# SAVE
def save_data_to_s3(bucket_name, file_name, df):
    """
    Saves a DataFrame to a CSV file on S3.

    Parameters:
    - bucket_name (str): The name of the S3 bucket where the file will be saved.
    - file_name (str): The name under which the file will be saved.
    - df (pandas.DataFrame): The DataFrame to be saved.

    Returns:
    None
    """
    # Convert the DataFrame to CSV using StringIO
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8')
    
    # Reset the pointer to the beginning of the stream
    csv_buffer.seek(0)
    
    # Upload the CSV to the S3 bucket
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer.getvalue())

# ========================================================================================================================================
# GRAPH AND DISPLAY
def create_bar_chart(data, title, week_or_month, y='Total Time', y_axis="Hours"):
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
    ax.xaxis.set_ticks_position('none') 
    ax.yaxis.set_ticks_position('none')
    sns.despine(left=False, bottom=False)
    plt.xticks(rotation=45)
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
    
    wedges, texts, autotexts = ax.pie(df_study_sum, labels=df_study_sum.index, autopct=lambda p: '{:.0f} h'.format(p * df_study_sum.sum() / 100), startangle=140, colors=colors)
    
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
    st.write(f"Charts for {period_label} {period}")
    
    if len(studies) > 0:
        nrows = (len(studies) + 1) // 2 if len(studies) % 2 else len(studies) // 2
        fig, axs = plt.subplots(nrows=nrows, ncols=2, figsize=(10, 5 * nrows))
        axs = axs.flatten()  # Flatten the axes array for easy access

        for i, study in enumerate(studies):
            df_study = df[df['STUDY'] == study]
            df_study_sum = df_study[TIME_INT_CAT].fillna(0).sum()
            df_study_sum = df_study_sum[df_study_sum > 0]

            if df_study_sum.sum() > 0:
                plot_pie_chart_on_ax(df_study_sum, f'Temps par Tâche pour {study}', axs[i])
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
    df_activities['Total Time'] = df_activities.sum(axis=1)
    df_activities_sorted = df_activities.sort_values('Total Time', ascending=False)
    create_bar_chart(df_activities_sorted, f'Heures Passées par Étude', f'{period_label} {period_value}')
    
    # Calculating and displaying total time spent and total number of visits
    total_time_spent = int(df_activities_sorted['Total Time'].sum())
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
    Checks and creates, if necessary, an empty file for each ARC mentioned in a DataFrame, in an S3 bucket.

    Parameters:
    - df (pandas.DataFrame): DataFrame containing at least one 'ARC' column with ARC names.

    Returns:
    None
    """
    for arc_name in df['ARC'].dropna().unique():  # Make sure to filter out NaN values and work with unique names
        file_name = f"Time_{arc_name}.csv"
        try:
            # Attempt to retrieve object metadata to see if it already exists
            s3_client.head_object(Bucket=BUCKET_NAME, Key=file_name)
            # If no exception is raised, the file already exists, so we won't create it
        except: 
            # The file does not exist, you can create the file
            new_df = pd.DataFrame(columns=CATEGORIES)  # Create a new DataFrame with desired columns
            csv_buffer = StringIO()
            new_df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8')
            csv_buffer.seek(0)  # Return to the beginning of the buffer to read its content
            # Send CSV content to the file in S3
            s3_client.put_object(Bucket=BUCKET_NAME, Key=file_name, Body=csv_buffer.getvalue())

def create_ongoing_files_for_arcs(df):
    """
    Checks and creates, if necessary, an empty ongoing file for each ARC mentioned in a DataFrame, in an S3 bucket.

    Parameters:
    - df (pandas.DataFrame): DataFrame containing at least one 'ARC' column with ARC names.

    Returns:
    None
    """
    for arc_name in df['ARC'].dropna().unique():  # Ensure uniqueness and absence of NaN values
        file_name = f"Ongoing_{arc_name}.csv"

        try:
            # Attempt to load the file to check its existence
            s3_client.head_object(Bucket=BUCKET_NAME, Key=file_name)
        except:
            # If an exception is raised, it usually means the file doesn't exist
            # Create a new DataFrame with desired columns
            new_df = pd.DataFrame(columns=CATEGORIES)
            csv_buffer = StringIO()
            new_df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8')
            csv_buffer.seek(0)  # Return to the beginning of the buffer to read its content
            # Send CSV content to the file in S3
            s3_client.put_object(Bucket=BUCKET_NAME, Key=file_name, Body=csv_buffer.getvalue())

def add_row_to_df_s3(bucket_name, file_name, df, **kwargs):
    """
    Adds a new row to a DataFrame and saves the updated DataFrame to a CSV file on S3.

    Parameters:
    - bucket_name (str): The name of the S3 bucket.
    - file_name (str): The name of the CSV file on S3.
    - df (pandas.DataFrame): The DataFrame to which to add the new row.
    - **kwargs: The values of the new row to add.

    Returns:
    - pandas.DataFrame: The updated DataFrame.
    """
    # Create a new row from the kwargs
    new_row = pd.DataFrame(kwargs, index=[0])
    # Concatenate the new row to the existing DataFrame
    df = pd.concat([df, new_row], ignore_index=True)

    # Convert the updated DataFrame to CSV string
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8')
    csv_buffer.seek(0)  # Return to the beginning of the buffer to read its content
    
    # Save the updated DataFrame
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer.getvalue())

    return df

def delete_row_s3(bucket_name, file_name, df, row_to_delete):
    """
    Deletes a specific row from a DataFrame and updates the corresponding file on S3.

    Parameters:
    - bucket_name (str): The name of the S3 bucket where the file is stored.
    - file_name (str): The name of the CSV file on S3 to update.
    - df (pandas.DataFrame): The DataFrame from which to delete the row.
    - row_to_delete (int): The index of the row to delete in the DataFrame.

    Returns:
    - pandas.DataFrame: The DataFrame after deleting the row.
    """
    # Delete the specified row from the DataFrame
    df = df.drop(row_to_delete)
    
    # Convert the updated DataFrame to a CSV string
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8')
    csv_buffer.seek(0)  # Return to the beginning of the buffer to read its content
    
    # Save the updated DataFrame to S3
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer.getvalue())
    
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
        st.set_page_config(layout="wide", page_icon="📊", page_title="I-Motion Adult - Project Managers Space")
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
        st.title("I-Motion Adulte - Espace Chefs de Projets")
        st.write("---")

        # Selection tab
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["👥 Gestion - ARCs", "📚 Gestion - Etudes", "📈 Dashboard - par ARCs", "📊 Dashboard - tous ARCs",  "📈 Dashboard - par Etude", "📊 Dashboard - toutes Etudes"])

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
                        arc_df = add_row_to_df_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, arc_df, ARC=new_arc_name, MDP=new_arc_password)
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
                    arc_df = delete_row_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, arc_df, arc_df[arc_df['ARC'] == arc_to_delete].index)
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
                    save_data_to_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, arc_df)
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


                if st.button("Ajouter l'étude"):
                    if new_study_name and new_study_primary_arc:  # Minimal validation
                        # Adding the new study
                        study_df = add_row_to_df_s3(BUCKET_NAME, STUDY_INFO_FILE, study_df,
                                                 STUDY=new_study_name, 
                                                 ARC=new_study_primary_arc, 
                                                 ARC_BACKUP=new_study_backup_arc if new_study_backup_arc else "")
                        st.success(f"Nouvelle étude '{new_study_name}' ajoutée avec succès.")
                        st.rerun()
                    else:
                        st.error("Le nom de l'étude et l'ARC principal sont requis.")

            with col_delete:
                st.markdown("#### Archivage d'une étude")
                study_options = study_df['STUDY'].dropna().astype(str).tolist()
                study_to_delete = st.selectbox("Choisir une étude à archiver", sorted(study_options))
                if st.button("Archiver l'étude sélectionnée"):
                    study_df = delete_row_s3(BUCKET_NAME, STUDY_INFO_FILE ,study_df, study_df[study_df['STUDY'] == study_to_delete].index)
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
                    save_data_to_s3(BUCKET_NAME, STUDY_INFO_FILE, study_df)
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
                        df_arc['Total Time'] = df_arc[TIME_INT_CAT].sum(axis=1)
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
            study_names = load_all_study_names(BUCKET_NAME)
            st.write(study_names)
            study_choice = st.selectbox("Choisissez votre étude", study_names)

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
            total_time_by_category = filtered_df_by_study[TIME_INT_CAT].sum()

            # Using st.columns to divide display space
            col_table, _, col_graph = st.columns([1.5, 0.2, 2])

            with col_table:
                st.write(f"Temps passé sur l'étude {study_choice}, par catégorie d'activité :")
                
                # Start with a Markdown header for the table
                markdown_table = "Catégorie | Heures passées\n:- | -:\n"
                
                # Add each category and corresponding time in Markdown format
                for category, hours in total_time_by_category.items():
                    markdown_table += f"{category} | {hours}\n"
                
                # Display the formatted table in Markdown
                st.markdown(markdown_table)

            with col_graph:
                # Preparation and display of pie chart in the second column
                fig, ax = plt.subplots()
                # Ensure total_time_by_category is defined before this line
                total_time_by_category = total_time_by_category[total_time_by_category > 0]
                if total_time_by_category.sum() > 0:
                    plot_pie_chart_on_ax(total_time_by_category, f"Répartition du temps par catégorie pour l'étude {study_choice}", ax)
                else:
                    ax.text(0.5, 0.5, f"Aucune donnée disponible\npour {study_choice}", ha='center', va='center', transform=ax.transAxes) # Correct reference to study choice variable and positioning
                    ax.set_axis_off()  # Hide axes if no data
                st.pyplot(fig)
                
            st.write("---")
            col_arc, col_scr, col_rand, col_eos, col_calc= st.columns([2, 1, 1, 1, 1])

            with col_arc:
                st.write(f"Temps total passé par ARC sur l'étude {study_choice} :")
                
                # Group data by ARC and calculate total
                total_time_by_arc = filtered_df_by_study.groupby('ARC')[TIME_INT_CAT].sum().sum(axis=1)
                
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
            df_activities_month['Total Time'] = df_activities_month.sum(axis=1)
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