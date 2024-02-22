import streamlit as st
import pandas as pd
import os
import datetime
import locale
import seaborn as sns
import matplotlib.pyplot as plt

# Chemin vers le dossier contenant les fichiers de données
DATA_FOLDER = "C:/Users/m.jacoupy/OneDrive - Institut/Documents/3 - Developpements informatiques/IMATimeTrackerStreamlitApp/Data/"

# Fichier contenant les informations des ARC et des études
ARC_INFO_FILE = "ARC_MDP.csv"
STUDY_INFO_FILE = "STUDY.csv"
ANNEES = [2024, 2025, 2026]

# Chargement des mots de passe ARC
def load_arc_passwords():
    file_path = os.path.join(DATA_FOLDER, ARC_INFO_FILE)
    df = pd.read_csv(file_path, sep=';')
    return dict(zip(df['ARC'], df['MDP']))

ARC_PASSWORDS = load_arc_passwords()

# Nombre de catégories
num_categories = 8

# Création d'une palette "viridis" avec le nombre approprié de couleurs
viridis_palette = sns.color_palette("viridis", num_categories)

# Mapping des catégories aux couleurs de la palette "viridis"
category_colors = {
    'VISITES PATIENT': viridis_palette[0],
    'QUERIES': viridis_palette[1],
    'SAISIE CRF': viridis_palette[2],
    'REUNIONS': viridis_palette[3],
    'REMOTE': viridis_palette[4],
    'MONITORING': viridis_palette[5],
    'TRAINING': viridis_palette[6],
    'ARCHIVAGE EMAIL': viridis_palette[7]
}

# Fonction pour créer un camembert
def plot_pie_chart(df_study_sum, title):
    colors = [category_colors[cat] for cat in df_study_sum.index if cat in category_colors]
    
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(df_study_sum, labels=df_study_sum.index, autopct=lambda p: '{:.0f} h'.format(p * df_study_sum.sum() / 100), startangle=140, colors=colors)

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_size(10)

    ax.set_title(title)
    st.pyplot(fig)


def load_data(DATA_FOLDER, arc):
    # Chemin vers le fichier Excel en fonction de l'ARC sélectionné
    csv_file_path = os.path.join(DATA_FOLDER, f"Time_{arc}.csv")

    try:
        # Essayer de lire le fichier avec l'encodage utf-8
        return pd.read_csv(csv_file_path, encoding='utf-8', sep=";")
    except UnicodeDecodeError:
        # Si UnicodeDecodeError est levé, essayer avec l'encodage latin1
        return pd.read_csv(csv_file_path, encoding='latin1', sep=";")
    except FileNotFoundError:
        # Si le fichier n'existe pas, afficher un message d'erreur
        st.error(f"Le fichier {csv_file_path} n'existe pas.")
        return None

def calculate_weeks():
    current_date = datetime.datetime.now()
    current_week = current_date.isocalendar()[1]
    previous_week = current_week - 1 if current_week > 1 else 52
    next_week = current_week + 1 if current_week < 52 else 1
    current_year = current_date.year
    current_month = current_date.month
    return previous_week, current_week, next_week, current_year, current_month


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
                columns = ['YEAR', 'WEEK', 'STUDY', 'VISITES PATIENT', 'QUERIES', 'SAISIE CRF', 
                'REUNIONS', 'REMOTE', 'MONITORING', 'TRAINING', 'ARCHIVAGE EMAIL', 'COMMENTAIRE']
                new_df = pd.DataFrame(columns=columns)
                new_df.to_csv(time_file_path, index=False, sep=';', encoding='utf-8')

def create_ongoing_files_for_arcs(df):
    for arc_name in df['ARC']:
        if pd.notna(arc_name):  # Vérifier si le nom de l'ARC n'est pas vide
            ongoing_file_path = os.path.join(DATA_FOLDER, f"Ongoing_{arc_name}.csv")
            if not os.path.exists(ongoing_file_path):
                columns = ['YEAR', 'WEEK', 'STUDY', 'VISITES PATIENT', 'QUERIES', 'SAISIE CRF', 
                'REUNIONS', 'REMOTE', 'MONITORING', 'TRAINING', 'ARCHIVAGE EMAIL', 'COMMENTAIRE']
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

def create_bar_chart(data, title, week_or_month):
    """Crée un graphique en barres pour les données fournies avec des couleurs cohérentes."""
    fig, ax = plt.subplots(figsize=(10, 4))

    # Définition de l'ordre des catégories et des couleurs correspondantes
    category_order = data.index.tolist()
    color_palette = sns.color_palette("viridis", len(category_order))

    # Mapping des couleurs aux catégories
    color_mapping = dict(zip(category_order, color_palette))

    # Création du graphique en barres avec l'ordre des couleurs défini
    sns.barplot(x=data.index, y='Total Time', data=data, ax=ax, palette=color_mapping)
    ax.set_title(f'{title} pour {week_or_month}')
    ax.set_xlabel('')
    ax.set_ylabel('Jours')
    plt.xticks(rotation=45)
    st.pyplot(fig)

    
# Fonction principale de l'application Streamlit
def main():
    st.set_page_config(layout="wide")
    st.title("I-Motion Adulte - Espace Chefs de Projets")

    # Onglet de sélection
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Configuration des ARCs", "Configuration des études", "Tableaux de suivi", "Tableaux de bord par ARC", "Tableau de bord général"])

    with tab1:
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

    with tab3:
        arc = st.selectbox("Choisissez votre ARC", list(ARC_PASSWORDS.keys()))

        # I. Chargement des données
        df_data = load_data(DATA_FOLDER, arc)
        revious_week, current_week, next_week, current_year, current_month = calculate_weeks()

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
        int_columns = ['VISITES PATIENT', 'QUERIES', 'SAISIE CRF', 'REUNIONS', 'REMOTE', 'MONITORING', 'TRAINING', 'ARCHIVAGE EMAIL']
        filtered_df1[int_columns] = filtered_df1[int_columns].astype(int)

        # Appliquer le style
        styled_df = filtered_df1.style.format({
            "YEAR": "{:.0f}",
            "WEEK": "{:.0f}"
        })

        # Utiliser styled_df pour l'affichage

        st.dataframe(styled_df, hide_index=True)


    with tab4:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            arc = st.selectbox("Choisissez votre ARC", list(ARC_PASSWORDS.keys()), key=2)

        # I. Chargement des données
        df_data = load_data(DATA_FOLDER, arc)
        previous_week, current_week, next_week, current_year, current_month = calculate_weeks()

        # Liste des noms de mois
        month_names = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                       "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

        # II. Interface utilisateur pour la sélection de l'année, du mois et de la semaine
        with col2:
            year_choice = st.selectbox("Année", ANNEES, key=3, index=ANNEES.index(datetime.datetime.now().year))
        col1, col2, col3 = st.columns([1, 0.25, 1])
        with col1:
            week_choice = st.slider("Semaine", 1, 52, current_week, key=4)
        with col3:
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
        filtered_month_df = df_data[(df_data['YEAR'] == year_choice) & 
                                    (df_data['WEEK'] >= start_week) & 
                                    (df_data['WEEK'] <= end_week)]

        # Convertir certaines colonnes en entiers pour les deux tableaux
        int_columns = ['VISITES PATIENT', 'QUERIES', 'SAISIE CRF', 'REUNIONS', 'REMOTE', 'MONITORING', 'TRAINING', 'ARCHIVAGE EMAIL']
        filtered_week_df[int_columns] = filtered_week_df[int_columns].astype(int)
        filtered_month_df[int_columns] = filtered_month_df[int_columns].astype(int)


        with col1:
            df_activities_week = filtered_week_df.groupby('STUDY')[int_columns].sum()
            df_activities_week['Total Time'] = df_activities_week.sum(axis=1)
            df_activities_week_sorted = df_activities_week.sort_values('Total Time', ascending=False)
            create_bar_chart(df_activities_week_sorted, 'Jours Passés par Étude', f'semaine {week_choice}')

        with col3:
            df_activities_month = filtered_month_df.groupby('STUDY')[int_columns].sum()
            df_activities_month['Total Time'] = df_activities_month.sum(axis=1)
            df_activities_month_sorted = df_activities_month.sort_values('Total Time', ascending=False)
            create_bar_chart(df_activities_month_sorted, 'Jours Passés par Étude', selected_month_name)

        st.write("---")

        sel_study = st.selectbox("Choisir une étude", study_df['STUDY'], key=9)
        col1, col3, col4 = st.columns([1, 0.25, 1])
        with col1:
            # Filtrage des données pour une étude spécifique
            df_study = filtered_week_df[filtered_week_df['STUDY'] == sel_study]

            # Remplacement des NaN par 0 et calcul de la somme
            df_study_sum = df_study[['VISITES PATIENT', 'QUERIES', 'SAISIE CRF', 'REUNIONS', 'REMOTE', 'MONITORING', 'TRAINING', 'ARCHIVAGE EMAIL']].fillna(0).sum()
            
            # Filtrage pour ne garder que les tâches avec une somme non nulle
            df_study_sum = df_study_sum[df_study_sum > 0]
            
            # Vérification si la somme totale est non nulle pour éviter un graphique vide
            if df_study_sum.sum() > 0:
                plot_pie_chart(df_study_sum, 'Temps par Tâche pour ' + sel_study + " pour la semaine " + str(week_choice))
            else:
                st.error("Pas de données disponibles pour afficher le graphique.")

        with col4:
            # Filtrage des données pour une étude spécifique
            df_study = filtered_month_df[filtered_month_df['STUDY'] == sel_study]

            # Remplacement des NaN par 0 et calcul de la somme
            df_study_sum = df_study[['VISITES PATIENT', 'QUERIES', 'SAISIE CRF', 'REUNIONS', 'REMOTE', 'MONITORING', 'TRAINING', 'ARCHIVAGE EMAIL']].fillna(0).sum()

            # Filtrage pour ne garder que les tâches avec une somme non nulle
            df_study_sum = df_study_sum[df_study_sum > 0]

            if df_study_sum.sum() > 0:
                plot_pie_chart(df_study_sum, 'Temps par Tâche pour ' + sel_study + " en " + str(selected_month_name))
            else:
                st.error("Pas de données disponibles pour afficher le graphique.")


    with tab5:
        # Liste des ARCs
        arcs = list(ARC_PASSWORDS.keys())

        # Dictionnaire pour stocker les DataFrames
        dfs = {}

        for arc in arcs:
            df_arc = load_data(DATA_FOLDER, arc)
            if df_arc is not None:
                df_arc['Total Time'] = df_arc[['VISITES PATIENT', 'QUERIES', 'SAISIE CRF', 'REUNIONS', 'REMOTE', 'MONITORING', 'TRAINING', 'ARCHIVAGE EMAIL']].sum(axis=1)
                df_arc = df_arc.groupby('WEEK')['Total Time'].sum().reset_index()
                dfs[arc] = df_arc
            else:
                st.error(f"Le dataframe pour {arc} n'a pas pu être chargé.")

        # Vérifier si le dictionnaire dfs n'est pas vide
        if dfs:
            fig, ax = plt.subplots(figsize=(12, 6))
            for arc, df in dfs.items():
                sns.lineplot(ax=ax, x='WEEK', y='Total Time', data=df, label=arc)

            plt.title('Évolution Hebdomadaire du Temps Total Passé par Chaque ARC en 2024')
            plt.xlabel('Semaine')
            plt.ylabel('Temps Total (Heures)')
            plt.xlim(1, 52)
            plt.legend()

            st.pyplot(fig)
        else:
            st.error("Aucune donnée disponible pour l'affichage du graphique.")



if __name__ == "__main__":
    main()
