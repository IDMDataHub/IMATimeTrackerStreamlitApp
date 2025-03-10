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
import sys


#####################################################################
# =========================== CONSTANTS =========================== #
#####################################################################

BUCKET_NAME = "imotion"
ARC_PASSWORDS_FILE = "ARC_MDP.csv"
YEARS = list(range(2024, 2030))
CATEGORIES = ['YEAR', 'WEEK', 'STUDY', 'TOTAL', 'MISE EN PLACE', 'TRAINING', 'VISITES', 'SAISIE CRF', 'QUERIES', 'MONITORING', 'REMOTE', 'REUNIONS', 
'ARCHIVAGE EMAIL', 'MAJ DOC', 'AUDIT & INSPECTION', 'CLOTURE', 'NB_VISITE', 'NB_PAT_SCR', 'NB_PAT_RAN', 'NB_EOS', 'COMMENTAIRE']
INT_CATEGORIES = CATEGORIES[3:-1]
# Configuration des colonnes avec "help" pour toutes les colonnes
COLUMN_CONFIG = {
    'YEAR': st.column_config.TextColumn("Année", help="Année"),
    'WEEK': st.column_config.TextColumn("Sem.", help="Numéro de la semaine"),
    'STUDY': st.column_config.TextColumn("Étude", help="Nom de l'étude"),
    'TOTAL': st.column_config.NumberColumn("Total", help="Temps total passé"),
    
    # Pour les cases à cocher
    'MISE EN PLACE': st.column_config.CheckboxColumn("MEP", help="Mise en place"),
    'TRAINING': st.column_config.CheckboxColumn("Form.", help="Formation"),
    'VISITES': st.column_config.CheckboxColumn("Vis.", help="Organisation des Visites"),
    'SAISIE CRF': st.column_config.CheckboxColumn("CRF", help="Saisie CRF"),
    'QUERIES': st.column_config.CheckboxColumn("Quer.", help="Queries"),
    'MONITORING': st.column_config.CheckboxColumn("Monit.", help="Monitoring"),
    'REMOTE': st.column_config.CheckboxColumn("Rem.", help="Remote"),
    'REUNIONS': st.column_config.CheckboxColumn("Réu.", help="Réunions"),
    'ARCHIVAGE EMAIL': st.column_config.CheckboxColumn("Arch. Email", help="Archivage des emails"),
    'MAJ DOC': st.column_config.CheckboxColumn("Maj. Doc", help="Mise à jour des documents"),
    'AUDIT & INSPECTION': st.column_config.CheckboxColumn("Aud.&Insp.", help="Audit et Inspection"),
    'CLOTURE': st.column_config.CheckboxColumn("Clôture", help="Clôture"),
    
    # Colonnes numériques ou textuelles avec "help"
    'NB_VISITE': st.column_config.NumberColumn("Nb Vis.", help="Nombre de visites"),
    'NB_PAT_SCR': st.column_config.NumberColumn("Nb Pat. Scr.", help="Nombre de patients screenés"),
    'NB_PAT_RAN': st.column_config.NumberColumn("Nb Pat. Rand.", help="Nombre de patients randomisés"),
    'NB_EOS': st.column_config.NumberColumn("Nb EOS.", help="Nombre d'EOS"),
    'COMMENTAIRE': st.column_config.TextColumn("Commentaires", help="Commentaires")
}


s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

def load_csv_from_s3(bucket_name, file_name, sep=';', encoding='utf-8'):    
    """
    Load a CSV file from an AWS S3 bucket using boto3, then read it into a pandas DataFrame.

    Parameters:
    - bucket_name (str): Name of the S3 bucket where the file is located.
    - file_name (str): Name of the file to load from the S3 bucket.
    - sep (str, optional): Field separator in the CSV file. Default is ';'.
    - encoding (str, optional): Encoding of the CSV file. Default is 'utf-8'.

    Returns:
    - pandas.DataFrame: A DataFrame containing the data from the CSV file.

    Raises:
    - Exception: Raises an exception if loading the file fails for any reason.
    """
    # Use boto3 to access S3 and load the specified file
    obj = s3_client.get_object(Bucket=bucket_name, Key=file_name)
    body = obj['Body'].read().decode(encoding)
    
    # Use pandas to read the CSV
    data = pd.read_csv(StringIO(body), sep=sep)
    return data

def save_csv_to_s3(df, bucket_name, file_name, sep=';', encoding='utf-8'):
    """
    Save a pandas DataFrame to a CSV file on an AWS S3 bucket using boto3.

    Parameters:
    - df (pandas.DataFrame): The DataFrame to be saved.
    - bucket_name (str): The name of the S3 bucket where the file will be saved.
    - file_name (str): The name under which the CSV file will be saved in the S3 bucket.
    - sep (str, optional): The field separator to use in the CSV file. Default is ';'.
    - encoding (str, optional): The encoding of the CSV file. Default is 'utf-8'.

    Returns:
    None

    Raises:
    - Exception: Raises an exception if the saving fails for any reason.
    """
    # Convert the DataFrame to CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=sep, encoding=encoding)
    
    # Reset the buffer cursor to the beginning
    csv_buffer.seek(0)
    
    # Use s3_client to save the CSV file to S3
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer.getvalue())

def load_arc_passwords():
    """
    Load passwords from a CSV file in S3, first attempting with UTF-8 encoding,
    then with Latin1 encoding if encoding fails.

    Parameters:
    None

    Returns:
    - dict: A dictionary with ARCs as keys and corresponding passwords as values.

    Raises:
    None
    """
    try:
        # Attempt to load the file with UTF-8 encoding
        df = load_csv_from_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        # If encoding error occurs, attempt to load with Latin1 encoding
        df = load_csv_from_s3(BUCKET_NAME, ARC_PASSWORDS_FILE, sep=';', encoding='latin1')
    return dict(zip(df['ARC'], df['MDP']))

ARC_PASSWORDS = load_arc_passwords()

# Keys for df1 (from YEAR to CLOTURE)
keys_df_time = list(COLUMN_CONFIG.keys())[:list(COLUMN_CONFIG.keys()).index('CLOTURE')+1]

# Keys for df2 (YEAR, WEEK, STUDY, and NB_VISITE to COMMENTAIRE)
keys_df_quantity = ['YEAR', 'WEEK', 'STUDY'] + list(COLUMN_CONFIG.keys())[list(COLUMN_CONFIG.keys()).index('NB_VISITE'):]

# Create configurations for each part
column_config_df_time = {k: COLUMN_CONFIG[k] for k in keys_df_time}
column_config_df_quantity = {k: COLUMN_CONFIG[k] for k in keys_df_quantity}

#####################################################################
# ===================== ASSISTANCE FUNCTIONS ====================== #
#####################################################################

# ========================================================================================================================================
# DATA LOADING
def load_data(arc):
    """
    Load data for a specific ARC from a CSV file located in an S3 bucket.

    Parameters:
    - arc (str): Identifier of the ARC for which to load the data.

    Returns:
    - pandas.DataFrame: DataFrame containing the loaded data for the specified ARC.

    Raises:
    - UnicodeDecodeError: Raises an exception if an encoding problem occurs during data loading.
    """
    file_name = f"Time_{arc}.csv"  # Name of the file in the S3 bucket
    try:
        # Attempt to load the file with UTF-8 encoding
        return load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        # If an encoding error occurs, attempt to load with Latin1 encoding
        return load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='latin1')

def load_time_data(arc, week):
    """
    Load time data for a specific ARC and given week from a CSV file stored in S3.

    Parameters:
    - arc (str): The identifier of the ARC for which to load the data.
    - week (int): The week number for which the data should be loaded.

    Returns:
    - pandas.DataFrame: A DataFrame containing filtered time data for the specified ARC and week.
    If an error occurs during loading, an empty DataFrame is returned.

    Raises:
    - Exception: Raises an exception if an error occurs during data loading from S3.
    """
    file_name = f"Time_{arc}.csv"  # Name of the file in the S3 bucket
    
    # Attempt to load the file from S3
    try:
        df = load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
        # Filter the data for the specified week
        return df[df['WEEK'] == week]
    except Exception as e:
        # Error handling, for example if the file does not exist
        print(f"Erreur lors du chargement des données depuis S3 : {e}")
        return pd.DataFrame()
        
def load_assigned_studies_with_roles(arc):
    """
    Load the list of studies assigned to a specific ARC and identify if the ARC is the principal or backup for each study from a CSV file stored in S3.

    Parameters:
    - arc (str): The identifier of the ARC for which assigned studies should be loaded.

    Returns:
    - pandas.DataFrame: A DataFrame containing the studies assigned to the specified ARC, with an additional column 'ROLE'
    indicating whether the ARC is the 'Principal' or 'Backup' for each study.

    Raises:
    None
    """
    # Specify the name of the file in the S3 bucket
    file_name = "STUDY.csv"  # Name of the file in the S3 bucket
    
    # Load the study data from the CSV file in the S3 bucket into a DataFrame
    df_study = load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
    
    # Create a new column 'ROLE' to identify if the ARC is 'Principal' or 'Backup' for each study
    df_study['ROLE'] = df_study.apply(lambda row: 'Principal' if row['ARC'] == arc else 'Backup' if row['ARC_BACKUP'] == arc else None, axis=1)
    
    # Filter the DataFrame to include only the studies where the ARC has a role (either 'Principal' or 'Backup')
    assigned_studies = df_study[df_study['ROLE'].notnull()]
    
    # Return the filtered DataFrame with the 'ROLE' information
    return assigned_studies



def load_assigned_studies(arc):
    """
    Load the list of studies assigned to a specific ARC from a CSV file stored in S3.

    Parameters:
    - arc (str): The identifier of the ARC for which assigned studies should be loaded.

    Returns:
    - list: A list containing the names of studies assigned to the specified ARC.

    Raises:
    None
    """
    file_name = "STUDY.csv"  # Name of the file in the S3 bucket
    
    # Load the file from S3
    df_study = load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
    
    # Filter to get studies assigned to the specified ARC
    assigned_studies = df_study[(df_study['ARC'] == arc) | (df_study['ARC_BACKUP'] == arc)]
    
    return assigned_studies['STUDY'].tolist()

def load_weekly_data(arc, week):
    """
    Load weekly data for a specific ARC and given week from a CSV file stored in S3.

    Parameters:
    - arc (str): The identifier of the ARC for which to load weekly data.
    - week (int): The week number for which the data should be loaded.

    Returns:
    - pandas.DataFrame: A DataFrame containing filtered weekly data for the specified ARC and week.
    If an error occurs during loading, an empty DataFrame is returned.

    Raises:
    - Exception: Raises an exception if an error occurs during data loading from S3.
    """
    file_name = f"Ongoing_{arc}.csv"  # Construct the file name based on the ARC
    
    # Attempt to load the file from S3
    try:
        df = load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
        # Filter the data for the specified week and return the DataFrame
        return df[df['WEEK'] == week]
    except Exception as e:
        # Error handling, for example if the file does not exist, return an empty DataFrame
        print(f"Erreur lors du chargement des données depuis S3 : {e}")
        return pd.DataFrame()

# ========================================================================================================================================
# SAVE
def save_data(df, arc):
    """
    Save DataFrame data to a specific ARC's CSV file on S3.

    Parameters:
    - df (pandas.DataFrame): The DataFrame containing the data to be saved.
    - arc (str): The identifier of the ARC to which the data is associated.

    Returns:
    None

    Raises:
    - Exception: Raises an exception if the save operation fails for any reason.
    """
    file_name = f"Time_{arc}.csv"
    
    # Convert the DataFrame to a CSV string
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=";", encoding='utf-8')
    
    # Reset the cursor position to the beginning of the buffer
    csv_buffer.seek(0)
    
    # Send the CSV content to the S3 bucket
    s3_client.put_object(Bucket=BUCKET_NAME, Body=csv_buffer.getvalue(), Key=file_name)

# ========================================================================================================================================
# CALCULATIONS
def authenticate_user(arc, password_entered):
    """
    Verifies if the entered password matches the ARC's password in the database.

    Parameters:
    - arc (str): The ARC's identifier.
    - password_entered (str): The password entered by the user.

    Returns:
    - bool: Returns True if the password matches, otherwise False.

    Raises:
    None
    """
    return ARC_PASSWORDS.get(arc) == password_entered.lower()

def calculate_weeks():
    """
    Calculates the current, previous, next, and two weeks ago week numbers, along with the current year.

    Parameters:
    None

    Returns:
    - tuple: Contains the numbers of the two previous weeks, the current week, the next week, and the current year.

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
    Calculates the start and end dates for a given week of a specific year.

    Parameters:
    - year (int): The year for which to calculate the dates.
    - week_number (int): The week number for which to calculate the start and end dates.

    Returns:
    - tuple: Contains the start and end dates of the specified week.

    Raises:
    None

    The dates are calculated based on the ISO week numbering system.
    """
    # Find the first day of the year
    first_day_of_year = datetime.datetime(year-1, 12, 31)
    first_monday_of_year = first_day_of_year + datetime.timedelta(days=(7-first_day_of_year.weekday()))
    week_start_date = first_monday_of_year + datetime.timedelta(weeks=week_number-1)
    week_end_date = week_start_date + datetime.timedelta(days=4)
    return week_start_date, week_end_date

# ========================================================================================================================================
# CREATION AND MODIFICATION
def check_create_weekly_file(arc, year, week):
    """
    Checks the existence of a weekly file for a given ARC. If the file does not exist, creates a new DataFrame with the specified columns and saves it to S3.

    Parameters:
    - arc (str): The ARC identifier.
    - year (int): The relevant year.
    - week (int): The week number.

    Returns:
    - str or None: The name of the created or modified file on S3, or None if no studies are assigned to the ARC.

    Raises:
    - Exception: Raises an exception if an error occurs during the creation or modification of the file.
    """
    file_name = f"Ongoing_{arc}.csv"

    try:
        df_existing = load_csv_from_s3(BUCKET_NAME, file_name, sep=';', encoding='utf-8')
    except Exception as e:
        # If the file does not exist or another error occurs, create a new DataFrame
        df_existing = pd.DataFrame(columns=CATEGORIES)
        
    # Load assigned studies
    assigned_studies = load_assigned_studies(arc)
    if assigned_studies:
        # Filter to keep only studies not present for this week and year
        existing_studies = df_existing[(df_existing['YEAR'] == year) & (df_existing['WEEK'] == week)]['STUDY']
        new_studies = [study for study in assigned_studies if study not in existing_studies.tolist()]
        
        # Prepare new rows to add only for new studies
        rows = [{'YEAR': year, 'WEEK': week, 'STUDY': study, 'TOTAL':0,'MISE EN PLACE': False, 'TRAINING': False, 'VISITES': False, 'SAISIE CRF': False, 'QUERIES': False, 
             'MONITORING': False, 'REMOTE': False, 'REUNIONS': False, 'ARCHIVAGE EMAIL': False, 'MAJ DOC': False, 'AUDIT & INSPECTION': False, 'CLOTURE': False, 
             'NB_VISITE': 0, 'NB_PAT_SCR':0, 'NB_PAT_RAN':0, 'NB_EOS':0, 'COMMENTAIRE': "Aucun"} for study in new_studies]
        if rows:  # If there are new studies to add
            df_existing = pd.concat([df_existing, pd.DataFrame(rows)], ignore_index=True, sort=False)
            # Save the updated DataFrame to S3
            save_csv_to_s3(df_existing, BUCKET_NAME, file_name, sep=';', encoding='utf-8')
    else:
        st.error("Aucune étude n'a été affectée. Merci de voir avec vos managers.")
        return None

    return file_name


def delete_ongoing_file(arc):
    """
    Deletes a specific "ongoing" file for an ARC on S3, identified by its constructed name.

    Parameters:
    - arc (str): The ARC identifier whose ongoing file needs to be deleted.

    Returns:
    None

    Raises:
    - Exception: Raises an exception if deletion fails for any reason.
    """
    file_name = f"Ongoing_{arc}.csv"
    
    # Deleting the file from the S3 bucket
    try:
        response = s3_client.delete_object(Bucket=BUCKET_NAME, Key=file_name)
        if response['ResponseMetadata']['HTTPStatusCode'] == 204:
            print(f"Le fichier {file_name} a été supprimé avec succès.")
        else:
            print(f"Erreur lors de la suppression du fichier {file_name}.")
    except Exception as e:
        # Handling potential errors during deletion
        print(f"Erreur lors de la tentative de suppression du fichier {file_name} : {e}")


# Validation et ajustement des valeurs pour s'assurer qu'elles n'ont que deux décimales
def validate_and_format(df, columns):
    """
    Validates and formats the specified columns of a DataFrame by rounding their values to two decimal places.

    Parameters:
    - df (pandas.DataFrame): The DataFrame containing the columns to be validated and formatted.
    - columns (list): A list of column names from the DataFrame that need to be validated and formatted.

    Returns:
    - pandas.DataFrame: The DataFrame with the specified columns' values rounded to two decimal places.

    Raises:
    None
    """
    for col in columns:
        df[col] = df[col].apply(lambda x: round(float(x), 2))
    return df


# ========================================================================================================================================
# SAVE AUTOMATIC

def main_auto_save_all():
    """
    Automates the process of saving data for all ARCs by updating weekly and time data for each ARC, 
    and ensuring that the data is properly saved to S3.

    Parameters:
    None

    Returns:
    None

    Raises:
    None, but logs errors and exceptions during the execution of the saving process.

    Process:
    1. Iterates over all ARCs from the ARC_PASSWORDS dictionary.
    2. For each ARC, loads the data, calculates the current and surrounding weeks.
    3. Checks for existing time data for the current week and updates it with relevant study information.
    4. Filters the data for "Principal" and "Backup" roles, updates the corresponding time and quantity data.
    5. Ensures that old data for the selected week is removed and new data is saved back to S3.
    6. Logs progress and completion of the save process for each ARC.
    """
    for arc in ARC_PASSWORDS.keys():
        st.write(f"Sauvegarde automatique pour l'ARC : {arc}")

        df_data = load_data(arc)
        two_weeks_ago, previous_week, current_week, next_week, current_year = calculate_weeks()

        selected_week = current_week

        time_df = load_time_data(arc, selected_week)
        weekly_file_path = check_create_weekly_file(arc, current_year, current_week)
        filtered_df2 = load_weekly_data(arc, selected_week)

        assigned_studies_df = load_assigned_studies_with_roles(arc)
        filtered_df2['YEAR'] = filtered_df2['YEAR'].astype(str)
        filtered_df2['WEEK'] = filtered_df2['WEEK'].astype(str)
        filtered_df2 = pd.merge(filtered_df2, assigned_studies_df[['STUDY', 'ROLE']], on='STUDY', how='left')

        df_principal = filtered_df2[filtered_df2['ROLE'] == 'Principal']
        df_time_principal = df_principal[keys_df_time]
        df_quantity_principal = df_principal[keys_df_quantity]

        df_backup = filtered_df2[filtered_df2['ROLE'] == 'Backup']
        df_time_backup = df_backup[keys_df_time]
        df_quantity_backup = df_backup[keys_df_quantity]

        df_data = df_data[df_data['WEEK'] != int(selected_week)]

        df_time_principal = df_time_principal.set_index(['YEAR', 'WEEK', 'STUDY'])
        df_quantity_principal = df_quantity_principal.set_index(['YEAR', 'WEEK', 'STUDY'])
        df_time_backup = df_time_backup.set_index(['YEAR', 'WEEK', 'STUDY'])
        df_quantity_backup = df_quantity_backup.set_index(['YEAR', 'WEEK', 'STUDY'])

        df_principal = pd.concat([df_time_principal, df_quantity_principal], axis=1)
        df_principal.reset_index(inplace=True)

        df_backup = pd.concat([df_time_backup, df_quantity_backup], axis=1)
        df_backup.reset_index(inplace=True)

        updated_df = pd.concat([df_data, df_principal, df_backup]).sort_index()

        save_data(updated_df, arc)

        st.write(f"Sauvegarde terminée pour l'ARC : {arc}")

#####################################################################
# ========================= MAIN FUNCTION ========================= #
#####################################################################

def main():
    """
    Main function running the Streamlit application. It configures the page, handles user authentication,
    data display and modification, as well as saving the changes.

    Parameters:
    None

    Returns:
    None

    Raises:
    None
    
    This function orchestrates user interactions with the Streamlit interface, including loading and
    modifying data, and calls other functions to perform these tasks.
    """
    try:
        st.set_page_config(layout="wide", page_icon=":microscope:", page_title="I-Motion Adulte - Espace ARCs")
    except:
        pass
    st.title("I-Motion Adulte - Espace ARCs")
    st.write("---")

    # User authentication
    arc = st.sidebar.selectbox("Choisissez votre ARC", list(ARC_PASSWORDS.keys()))
    arc_password_entered = st.sidebar.text_input(f"Entrez le mot de passe", type="password")
    
    if not authenticate_user(arc, arc_password_entered):
        st.sidebar.error("Mot de passe incorrect pour l'ARC sélectionné.")
        return

    # I. Data loading
    df_data = load_data(arc)
    two_weeks_ago, previous_week, current_week, next_week, current_year = calculate_weeks()

    # II. Section for data modification
    st.subheader("Entrée d'heures")
    
    week_choice2 = st.radio(
        "Choisissez une semaine",
        [f"Deux semaines avant (Semaine {two_weeks_ago})", 
         f"Semaine précédente (Semaine {previous_week})",
         f"Semaine en cours (Semaine {current_week})"],
        index=2)

    # Get the selected value (week number)
    selected_week = int(week_choice2.split()[-1].strip(')'))
    time_df = load_time_data(arc, selected_week)


    if "en cours" in week_choice2:
        # Load data for the current week from Ongoing_arc.csv
        weekly_file_path = check_create_weekly_file(arc, current_year, current_week)
        filtered_df2 = load_weekly_data(arc, selected_week)

        if not time_df.empty:
            if not time_df[(time_df['YEAR'] == current_year) & (time_df['WEEK'] == current_week)].empty:
                # There is data in time_df for the current year and week
                # Merge the data
                merged_df = pd.merge(filtered_df2, time_df, on=['YEAR', 'WEEK', 'STUDY'], suffixes=('_ongoing', '_time'), how='outer')
                # Retrieve studies currently assigned to this ARC
                assigned_studies = set(load_assigned_studies(arc))
                merged_df = merged_df[merged_df['STUDY'].isin(assigned_studies)]
                # Replace values in Ongoing with those from Time if they are not 0
                columns_to_update = CATEGORIES[3:]
                for col in columns_to_update:
                    merged_df[col + '_ongoing'] = merged_df.apply(
                        lambda row: row[col + '_time'] if not pd.isna(row[col + '_time']) and row[col + '_ongoing'] == 0 else row[col + '_ongoing'], axis=1)
                # Add rows for missing newly assigned studies
                for study in assigned_studies:
                    if study not in merged_df['STUDY'].tolist():
                        new_row_data = {'YEAR': current_year, 'WEEK': current_week, 'STUDY': study}
                        new_row_data.update({col + '_ongoing': 0 for col in columns_to_update[:]})
                        new_row_data['COMMENTAIRE_ongoing'] = "Aucun"
                        new_row = pd.DataFrame([new_row_data])
                        merged_df = pd.concat([merged_df, new_row], ignore_index=True)


                # Filter columns to eliminate those with '_time'
                filtered_columns = [col for col in merged_df.columns if '_time' not in col]

                # Create the final DataFrame with filtered columns
                final_df = merged_df[filtered_columns]
                filtered_df2 = final_df.rename(columns={col + '_ongoing': col for col in columns_to_update})

            else:
                # There is data in time_df, but not for the current year and week
                filtered_df2 = time_df
        else:
            # time_df is completely empty
            assigned_studies = set(load_assigned_studies(arc))
            rows = [{'YEAR': current_year, 'WEEK': current_week, 'STUDY': study, 'TOTAL':0, 'MISE EN PLACE': False, 'TRAINING': False, 'VISITES': False, 'SAISIE CRF': False, 'QUERIES': False, 
             'MONITORING': False, 'REMOTE': False, 'REUNIONS': False, 'ARCHIVAGE EMAIL': False, 'MAJ DOC': False, 'AUDIT & INSPECTION': False, 'CLOTURE': False, 
             'NB_VISITE': 0, 'NB_PAT_SCR':0, 'NB_PAT_RAN':0, 'NB_EOS':0, 'COMMENTAIRE': "Aucun"} for study in assigned_studies]
            filtered_df2 = pd.DataFrame(rows)
            
    else:
        # Charger les données de la semaine précédente à partir de Time_arc.csv
        filtered_df2 = time_df            

    # Charger les études assignées avec les rôles
    assigned_studies_df = load_assigned_studies_with_roles(arc)

    if not filtered_df2.empty:
        filtered_df2['YEAR'] = filtered_df2['YEAR'].astype(str)
        filtered_df2['WEEK'] = filtered_df2['WEEK'].astype(str)

        # Convertir les colonnes de temps en float pour accepter les décimales
        for col in keys_df_time[3:]:  # Exclude 'YEAR', 'WEEK', and 'STUDY'
            filtered_df2[col] = filtered_df2[col].astype(float)

        columns_to_convert_to_bool = [
		    'MISE EN PLACE', 'TRAINING', 'VISITES', 'SAISIE CRF', 'QUERIES', 
		    'MONITORING', 'REMOTE', 'REUNIONS', 'ARCHIVAGE EMAIL', 
		    'MAJ DOC', 'AUDIT & INSPECTION', 'CLOTURE']

        for col in columns_to_convert_to_bool:
            filtered_df2[col] = filtered_df2[col].astype(bool)  # Conversion en booléen

		# Fusionner les données filtrées avec les rôles d'études
        filtered_df2 = pd.merge(filtered_df2, assigned_studies_df[['STUDY', 'ROLE']], on='STUDY', how='left')
        
        # Filtrer les données pour le rôle "Principal"
        df_principal = filtered_df2[filtered_df2['ROLE'] == 'Principal']
        df_time_principal = df_principal[keys_df_time]
        df_quantity_principal = df_principal[keys_df_quantity]
        
        # Filtrer les données pour le rôle "Backup"
        df_backup = filtered_df2[filtered_df2['ROLE'] == 'Backup']
        df_time_backup = df_backup[keys_df_time]
        df_quantity_backup = df_backup[keys_df_quantity]

        # Afficher les tableaux pour le rôle "Principal"
        st.markdown('**Partie "Temps" - Etudes Principales**')
        df1_edited_principal = st.data_editor(
            data=df_time_principal,
            hide_index=True,
            disabled=["YEAR", "WEEK", "STUDY"],
            column_config=column_config_df_time
        )

        st.markdown('**Partie "Quantité" - Etudes Principales**')
        df2_edited_principal = st.data_editor(
            data=df_quantity_principal,
            hide_index=True,
            disabled=["YEAR", "WEEK", "STUDY"],
            column_config=column_config_df_quantity
        )

        with st.expander("Voir les Etudes Backup"):
          # Afficher les tableaux pour le rôle "Backup"
          st.markdown('**Partie "Temps" - Etudes Backup**')
          df1_edited_backup = st.data_editor(
              data=df_time_backup,
              hide_index=True,
              disabled=["YEAR", "WEEK", "STUDY"],
              column_config=column_config_df_time
          )
  
          st.markdown('**Partie "Quantité" - Etudes Backup**')
          df2_edited_backup = st.data_editor(
              data=df_quantity_backup,
              hide_index=True,
              disabled=["YEAR", "WEEK", "STUDY"],
              column_config=column_config_df_quantity
          )

    else:
        st.write("Aucune donnée disponible pour la semaine sélectionnée.")
    
    
    # III. Save button
    if st.button("Sauvegarder"):

        # Remove old data for the selected week
        df_data = df_data[df_data['WEEK'] != int(selected_week)]

        # Convertir les colonnes de temps en float pour assurer la bonne sauvegarde des valeurs décimales
        for col in keys_df_time[3:]:  # Exclude 'YEAR', 'WEEK', and 'STUDY'
            df1_edited_principal[col] = df1_edited_principal[col].astype(float)
            df1_edited_backup[col] = df1_edited_backup[col].astype(float)

        # Ensure 'YEAR', 'WEEK', 'STUDY' are present in both DataFrames for alignment
        df1_edited_principal = df1_edited_principal.set_index(['YEAR', 'WEEK', 'STUDY'])
        df1_edited_principal = validate_and_format(df1_edited_principal, keys_df_time[3:])
        df2_edited_principal = df2_edited_principal.set_index(['YEAR', 'WEEK', 'STUDY'])
        df1_edited_backup = df1_edited_backup.set_index(['YEAR', 'WEEK', 'STUDY'])
        df1_edited_backup = validate_and_format(df1_edited_backup, keys_df_time[3:])
        df2_edited_backup = df2_edited_backup.set_index(['YEAR', 'WEEK', 'STUDY'])

        # Concaténation des DataFrames "Principal" sur l'axe des colonnes
        df_principal = pd.concat([df1_edited_principal, df2_edited_principal], axis=1)
        df_principal.reset_index(inplace=True)

        # Concaténation des DataFrames "Backup" sur l'axe des colonnes
        df_backup = pd.concat([df1_edited_backup, df2_edited_backup], axis=1)
        df_backup.reset_index(inplace=True)

        # Concaténer les nouvelles données principales et backup avec les anciennes données
        updated_df = pd.concat([df_data, df_principal, df_backup]).sort_index()

        # Save the updated DataFrame
        save_data(updated_df, arc)

        # Delete the Ongoing_ARC.csv file
        delete_ongoing_file(arc)

        st.success("Les données ont été sauvegardées et le fichier temporaire a été supprimé.")

        # Reload the page
        st.rerun()
        
    # IV. User interface for year and week selection
    st.write("---")
    st.subheader("Visualisation de l'historique")
    col1, col2 = st.columns([1, 3])
    with col1:
        year_choice = st.selectbox("Year", YEARS, index=YEARS.index(datetime.datetime.now().year))
    with col2:
        week_choice = st.slider("Week", 1, 52, current_week)

    # Data filtering and manipulation
    filtered_df1 = df_data[(df_data['YEAR'] == year_choice) & (df_data['WEEK'] == week_choice)]

    # Convert certain columns to integers
    int_columns = INT_CATEGORIES
    filtered_df1[int_columns] = filtered_df1[int_columns].astype(int)

    df_time = filtered_df1[keys_df_time]
    df_quantity = filtered_df1[keys_df_quantity]
    
    # Apply styling
    styled_df_time = df_time.style.format({
        "YEAR": "{:.0f}",
        "WEEK": "{:.0f}",
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
# ========================== ALGO LAUNCH ========================== #
#####################################################################

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "auto_save_all":
        main_auto_save_all()
    else:
        main()