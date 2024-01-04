import streamlit as st
import pandas as pd
import os

# Chemin vers le dossier contenant les fichiers de données
DATA_FOLDER = "C:/Users/m.jacoupy/OneDrive - Institut/Documents/3 - Developpements informatiques/IMATimeTrackerStreamlitApp/Data/"

# Fichier contenant les informations des ARC et des études
ARC_INFO_FILE = "ARC_MDP.csv"
STUDY_INFO_FILE = "STUDY.csv"

# Chargement des données des ARC
def load_arc_info():
    file_path = os.path.join(DATA_FOLDER, ARC_INFO_FILE)
    return pd.read_csv(file_path, sep=';', dtype=str)

# Chargement des données des études
def load_study_info():
    file_path = os.path.join(DATA_FOLDER, STUDY_INFO_FILE)
    return pd.read_csv(file_path, sep=';', dtype=str)

# Sauvegarde des données modifiées
def save_data(file_name, df):
    file_path = os.path.join(DATA_FOLDER, file_name)
    df.to_csv(file_path, index=False, sep=';', encoding='utf-8')

# Vérifie et crée un fichier pour chaque ARC dans le DataFrame
def create_time_files_for_arcs(df):
    for arc_name in df['ARC']:
        if pd.notna(arc_name):  # Vérifier si le nom de l'ARC n'est pas vide
            time_file_path = os.path.join(DATA_FOLDER, f"Time_{arc_name}.csv")
            if not os.path.exists(time_file_path):
                columns = ['YEAR', 'WEEK', 'STUDY', 'GENERAL', 'MEETING', 'TRAINING', 'MONITORING', 'REMOTE', 'COMMENT']
                new_df = pd.DataFrame(columns=columns)
                new_df.to_csv(time_file_path, index=False, sep=';', encoding='utf-8')

def create_ongoing_files_for_arcs(df):
    for arc_name in df['ARC']:
        if pd.notna(arc_name):  # Vérifier si le nom de l'ARC n'est pas vide
            ongoing_file_path = os.path.join(DATA_FOLDER, f"Ongoing_{arc_name}.csv")
            if not os.path.exists(ongoing_file_path):
                columns = ['YEAR', 'WEEK', 'STUDY', 'GENERAL', 'MEETING', 'TRAINING', 'MONITORING', 'REMOTE', 'COMMENT']
                new_df = pd.DataFrame(columns=columns)
                new_df.to_csv(ongoing_file_path, index=False, sep=';', encoding='utf-8')

# Fonction pour ajouter une ligne à un DataFrame
def add_row_to_df(df, file_name):
    new_row = pd.DataFrame([["" for _ in df.columns]], columns=df.columns)
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(file_name, df)
    return df

# Fonction pour supprimer une ligne d'un DataFrame
def delete_row(df, row_to_delete, file_name):
    df = df.drop(row_to_delete)
    save_data(file_name, df)
    return df

# Fonction principale de l'application Streamlit
def main():
    st.set_page_config(layout="wide")
    st.title("Configuration des ARC et Études")

    # Onglet de sélection
    tab1, tab2 = st.tabs(["ARC", "Études"])

    with tab1:
        st.subheader("Configuration des ARC")
        arc_df = load_arc_info()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Gestion des ARC")
            arc_to_delete = st.selectbox("Choisir un ARC à supprimer", arc_df['ARC'])
            if st.button("Supprimer l'ARC sélectionné"):
                arc_df = delete_row(arc_df, arc_df[arc_df['ARC'] == arc_to_delete].index, ARC_INFO_FILE)
                st.success(f"ARC '{arc_to_delete}' supprimé avec succès.")
            if st.button("Ajouter un ARC"):
                arc_df = add_row_to_df(arc_df, ARC_INFO_FILE)
                st.success("Nouvel ARC ajouté.")

        with col2:
            st.markdown("#### Modification des ARC")
            updated_arc_df = st.data_editor(data=arc_df)
            if st.button("Sauvegarder les modifications des ARC"):
                save_data(ARC_INFO_FILE, updated_arc_df)
                create_time_files_for_arcs(updated_arc_df)
                create_ongoing_files_for_arcs(updated_arc_df) 
                st.success("Informations ARC sauvegardées avec succès.")

    with tab2:
        st.subheader("Configuration des Études")
        study_df = load_study_info()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Gestion des Études")
            study_to_delete = st.selectbox("Choisir une étude à supprimer", study_df['STUDY'])
            if st.button("Supprimer l'étude sélectionnée"):
                study_df = delete_row(study_df, study_df[study_df['STUDY'] == study_to_delete].index, STUDY_INFO_FILE)
                st.success(f"L'étude '{study_to_delete}' supprimée avec succès.")
            if st.button("Ajouter une Étude"):
                study_df = add_row_to_df(study_df, STUDY_INFO_FILE)
                st.success("Nouvelle Étude ajoutée.")

        with col2:
            st.markdown("#### Modification des Études")
            updated_study_df = st.data_editor(data=study_df)
            if st.button("Sauvegarder les modifications des Études"):
                save_data(STUDY_INFO_FILE, updated_study_df)
                st.success("Informations des Études sauvegardées avec succès.")

if __name__ == "__main__":
    main()
