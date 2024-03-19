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

#####################################################################
# =========================== CONSTANTES ========================== #
#####################################################################


# Chemin vers le dossier contenant les fichiers de données
DATA_FOLDER = "C:/Users/m.jacoupy/OneDrive - Institut/Documents/3 - Developpements informatiques/IMATimeTrackerStreamlitApp/Data/"

# Fichier contenant les informations des ARC et des études
ARC_INFO_FILE = "ARC_MDP.csv"
STUDY_INFO_FILE = "STUDY.csv"
ANNEES = list(range(2024, 2030))
CATEGORIES = ['YEAR', 'WEEK', 'STUDY', 'VISITES PATIENT', 'QUERIES', 'SAISIE CRF', 'REUNIONS', 'REMOTE', 'MONITORING', 'TRAINING', 'ARCHIVAGE EMAIL', 'COMMENTAIRE', 'NB_VISITE']
INT_CATEGORIES = CATEGORIES[3:-2]
MONTHS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

# Création d'une palette "viridis" avec le nombre approprié de couleurs
viridis_palette = sns.color_palette("viridis", len(INT_CATEGORIES))

# Mapping des catégories aux couleurs de la palette "viridis"
category_colors = {category: color for category, color in zip(INT_CATEGORIES, viridis_palette)}

# Chargement des mots de passe ARC
def load_arc_passwords():
    file_path = os.path.join(DATA_FOLDER, ARC_INFO_FILE)
    df = pd.read_csv(file_path, sep=';')
    return dict(zip(df['ARC'], df['MDP']))

ARC_PASSWORDS = load_arc_passwords()


#####################################################################
# ==================== FONCTIONS D'ASSISTANCES ==================== #
#####################################################################


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
                columns = CATEGORIES
                new_df = pd.DataFrame(columns=columns)
                new_df.to_csv(time_file_path, index=False, sep=';', encoding='utf-8')

def create_ongoing_files_for_arcs(df):
    for arc_name in df['ARC']:
        if pd.notna(arc_name):  # Vérifier si le nom de l'ARC n'est pas vide
            ongoing_file_path = os.path.join(DATA_FOLDER, f"Ongoing_{arc_name}.csv")
            if not os.path.exists(ongoing_file_path):
                columns = CATEGORIES
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
    ax.set_ylabel('Heures')
    plt.xticks(rotation=45)
    st.pyplot(fig)

# VERSION MEME TAILLE
def plot_pie_chart_on_ax(df_study_sum, title, ax):
    colors = [category_colors[cat] for cat in df_study_sum.index if cat in category_colors]
    
    wedges, texts, autotexts = ax.pie(df_study_sum, labels=df_study_sum.index, autopct=lambda p: '{:.0f} h'.format(p * df_study_sum.sum() / 100), startangle=140, colors=colors)
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_size(10)
    
    ax.set_title(title)

# # VERSION DIFFERENTE TAILLE
# def plot_pie_chart_on_ax(df_study_sum, title, ax):
#     # Exemple de calcul d'un facteur basé sur le temps total
#     total_time = df_study_sum.sum()
#     scale_factor = max(1, total_time / 100)  # Ajustez ce calcul selon vos besoins

#     # Taille de la figure ajustée en fonction du scale_factor
#     fig_size = (6 * scale_factor, 6 * scale_factor)

#     # Ajustez la figure courante avant de tracer le camembert
#     ax.figure.set_size_inches(fig_size)

#     # Tracer le camembert
#     colors = [category_colors[cat] for cat in df_study_sum.index if cat in category_colors]
#     wedges, texts, autotexts = ax.pie(df_study_sum, labels=df_study_sum.index, autopct=lambda p: '{:.0f} h'.format(p * total_time / 100), startangle=140, colors=colors)
    
#     ax.set_title(title)



#####################################################################
# ====================== FONCTION PRINCIPALE ====================== #
#####################################################################

# Fonction principale de l'application Streamlit
def main():
    st.set_page_config(layout="wide")
    st.title("I-Motion Adulte - Espace Chefs de Projets")

    # Onglet de sélection
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Configuration des ARCs", "Configuration des études", "Tableaux de bord par ARC", "Tableau de bord général",  "Archives des études"])

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

    # with tab3:
    #     arc = st.selectbox("Choisissez votre ARC", list(ARC_PASSWORDS.keys()))

    #     # I. Chargement des données
    #     df_data = load_data(DATA_FOLDER, arc)
    #     previous_week, current_week, next_week, current_year, current_month = calculate_weeks()

    #     # II. Interface utilisateur pour la sélection de l'année et de la semaine
    #     st.subheader("Visualisation")
    #     col1, col2 = st.columns([1, 3])
    #     with col1:
    #         year_choice = st.selectbox("Année", ANNEES, index=ANNEES.index(datetime.datetime.now().year))
    #     with col2:
    #         week_choice = st.slider("Semaine", 1, 52, current_week)

    #     # Filtrage et manipulation des données
    #     filtered_df1 = df_data[(df_data['YEAR'] == year_choice) & (df_data['WEEK'] == week_choice)]

    #     # Convertir certaines colonnes en entiers
    #     int_columns = INT_CATEGORIES
    #     filtered_df1[int_columns] = filtered_df1[int_columns].astype(int)

    #     # Appliquer le style
    #     styled_df = filtered_df1.style.format({
    #         "YEAR": "{:.0f}",
    #         "WEEK": "{:.0f}"})

    #     # Utiliser styled_df pour l'affichage
    #     st.dataframe(styled_df, hide_index=True)


    with tab3:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            arc = st.selectbox("Choisissez votre ARC", list(ARC_PASSWORDS.keys()), key=2)

        # I. Chargement des données
        df_data = load_data(DATA_FOLDER, arc)
        previous_week, current_week, next_week, current_year, current_month = calculate_weeks()

        associated_studies = df_data['STUDY'].unique().tolist()
        # Liste des noms de mois
        month_names = MONTHS

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
        int_columns = INT_CATEGORIES
        filtered_week_df[int_columns] = filtered_week_df[int_columns].astype(int)
        filtered_month_df[int_columns] = filtered_month_df[int_columns].astype(int)


        with col1:
            df_activities_week = filtered_week_df.groupby('STUDY')[int_columns].sum()
            df_activities_week['Total Time'] = df_activities_week.sum(axis=1)
            df_activities_week_sorted = df_activities_week.sort_values('Total Time', ascending=False)
            create_bar_chart(df_activities_week_sorted, 'Heures Passées par Étude', f'semaine {week_choice}')
            # Calcul du temps total passé
            total_time_spent = df_activities_week_sorted['Total Time'].sum()
            # Affichage du temps total passé avec Markdown, de manière plus simple
            unit = "heure" if total_time_spent <= 1 else "heures"
            time, visit = st.columns(2)
            with time:
                st.metric(label="Temps total passé", value=f"{total_time_spent} {unit}")
            with visit:
                st.metric(label="Nombre total de visites", value=f"{int(sum(filtered_week_df['NB_VISITE']))}")

        with col3:
            df_activities_month = filtered_month_df.groupby('STUDY')[int_columns].sum()
            df_activities_month['Total Time'] = df_activities_month.sum(axis=1)
            df_activities_month_sorted = df_activities_month.sort_values('Total Time', ascending=False)
            create_bar_chart(df_activities_month_sorted, 'Heures Passées par Étude', selected_month_name)
            # Calcul du temps total passé
            total_time_spent = df_activities_month_sorted['Total Time'].sum()
            unit = "heure" if total_time_spent <= 1 else "heures"
            time, visit = st.columns(2)
            with time:
                st.metric(label="Temps total passé", value=f"{total_time_spent} {unit}")
            with visit:
                st.metric(label="Nombre total de visites", value=f"{int(sum(filtered_month_df['NB_VISITE']))}")

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
            st.write("Graphiques pour la semaine sélectionnée")
            
            # Initialiser la figure avec deux colonnes et un nombre adapté de lignes
            fig, axs = plt.subplots(nrows=nrows, ncols=2, figsize=(10, 5 * nrows))
            axs = axs.flatten()  # Aplatir le tableau d'axes pour un accès simplifié
            
            for i, sel_study in enumerate(sel_studies):
                df_study_week = filtered_week_df[filtered_week_df['STUDY'] == sel_study]
                df_study_week_sum = df_study_week[INT_CATEGORIES].fillna(0).sum()
                df_study_week_sum = df_study_week_sum[df_study_week_sum > 0]
                
                if df_study_week_sum.sum() > 0:
                    plot_pie_chart_on_ax(df_study_week_sum, f'Temps par Tâche pour {sel_study} (Semaine {week_choice})', axs[i])
                else:
                    # Ajouter le texte avec un cadre arrondi
                    axs[i].text(0.5, 0.5, f"Aucune donnée disponible\npour {sel_study}", 
                                ha='center', va='center', fontsize=12, color='darkorange',
                                bbox=dict(facecolor='none', edgecolor='darkorange', boxstyle='round,pad=0.5'))
                    axs[i].set_axis_off()  # Masquer les axes si pas de données
               
            # Masquer les axes supplémentaires s'ils ne sont pas utilisés
            for j in range(i + 1, len(axs)):
                axs[j].axis('off')
            
            plt.tight_layout()
            st.pyplot(fig)

        # Répéter la même structure pour le mois dans la colonne de droite
        with col_month:
            st.write("Graphiques pour le mois sélectionné")
            
            fig, axs = plt.subplots(nrows=nrows, ncols=2, figsize=(10, 5 * nrows))
            axs = axs.flatten()
            
            for i, sel_study in enumerate(sel_studies):
                df_study_month = filtered_month_df[filtered_month_df['STUDY'] == sel_study]
                df_study_month_sum = df_study_month[INT_CATEGORIES].fillna(0).sum()
                df_study_month_sum = df_study_month_sum[df_study_month_sum > 0]
                
                if df_study_month_sum.sum() > 0:
                    plot_pie_chart_on_ax(df_study_month_sum, f'Temps par Tâche pour {sel_study} ({selected_month_name})', axs[i])
                else:
                    # Ajouter le texte avec un cadre arrondi
                    axs[i].text(0.5, 0.5, f"Aucune donnée disponible\npour {sel_study}", 
                                ha='center', va='center', fontsize=12, color='darkorange',
                                bbox=dict(facecolor='none', edgecolor='darkorange', boxstyle='round,pad=0.5'))
                    axs[i].set_axis_off()  # Masquer les axes si pas de données
            
            
            for j in range(i + 1, len(axs)):
                axs[j].axis('off')
            
            plt.tight_layout()
            st.pyplot(fig)

    with tab4:
        arcs = list(ARC_PASSWORDS.keys())

        previous_week, current_week, next_week, current_year, current_month = calculate_weeks()

        # Utiliser current_year au lieu de 2024 directement
        last_5_weeks = [(current_week - i) % 52 or 52 for i in range(1, 6)]
        all_weeks_current_year = np.arange(1, 53)  # Toutes les semaines pour l'année courante
        dfs = {}  # Pour stocker les DataFrames

        for arc in arcs:
            df_arc = load_data(DATA_FOLDER, arc)
            if df_arc is not None:
                df_arc['Total Time'] = df_arc[INT_CATEGORIES].sum(axis=1)
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
            else:
                st.error(f"Le dataframe pour {arc} n'a pas pu être chargé.")

        col1, col2 = st.columns(2)
        
        # Graphique pour les 5 dernières semaines
        with col1:
            if dfs:
                fig, ax = plt.subplots(figsize=(12, 6))
                for arc, data in dfs.items():
                    sns.lineplot(ax=ax, x='WEEK', y='Total Time', data=data['last_5_weeks'], label=arc)

                plt.title(f'Évolution Hebdomadaire du Temps Total Passé par Chaque ARC pour les 5 dernières semaines')
                plt.xlabel('Semaines')
                plt.ylabel('Temps Total (Heures)')

                # Définir les ticks de l'axe des X pour utiliser uniquement des valeurs entières
                ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
                plt.legend()
                st.pyplot(fig)
            else:
                st.error("Aucune donnée disponible pour l'affichage du graphique.")
       
        # Pour le graphique de l'année en cours
        with col2:
            if dfs:
                fig, ax = plt.subplots(figsize=(12, 6))
                for arc, data in dfs.items():
                    sns.lineplot(ax=ax, x='WEEK', y='Total Time', data=data['current_year'], label=arc)

                plt.title(f'Évolution Hebdomadaire du Temps Total Passé par Chaque ARC en {current_year}')
                plt.xlabel('Semaines')
                plt.ylabel('Temps Total (Heures)')
                plt.xlim(1, 52)
                plt.legend()
                st.pyplot(fig)
            else:
                st.error("Aucune donnée disponible pour l'affichage du graphique.")


    with tab5:
        # Sélection d'une étude
        study_info_df = load_study_info()
        study_choice = st.selectbox("Choisissez votre étude", study_info_df['STUDY'].unique())

        # Chargement et combinaison des données de tous les ARCs
        all_arcs_df = pd.DataFrame()
        for arc in ARC_PASSWORDS.keys():
            df_arc = load_data(DATA_FOLDER, arc)
            if df_arc is not None:
                df_arc['ARC'] = arc
                all_arcs_df = pd.concat([all_arcs_df, df_arc], ignore_index=True)

        # Filtrage des données par étude sélectionnée
        filtered_df_by_study = all_arcs_df[all_arcs_df['STUDY'] == study_choice]

        # Assurez-vous que les colonnes d'intérêt sont de type numérique pour le calcul
        filtered_df_by_study[INT_CATEGORIES] = filtered_df_by_study[INT_CATEGORIES].apply(pd.to_numeric, errors='coerce')

        # Calculer le temps total passé par catégorie d'activité pour l'étude sélectionnée
        total_time_by_category = filtered_df_by_study[INT_CATEGORIES].sum()


        # Utilisation de st.columns pour diviser l'espace d'affichage
        col1, col2, col3, col4 = st.columns([1, 1, 0.2, 1])

        with col1:
            st.write(f"Temps passé sur l'étude {study_choice}, par catégorie d'activité :")
            
            # Commencer par un header de Markdown pour le tableau
            markdown_table = "Catégorie | Heures passées\n:- | -:\n"
            
            # Ajouter chaque catégorie et le temps correspondant dans le format Markdown
            for category, hours in total_time_by_category.items():
                markdown_table += f"{category} | {hours:}\n"
            
            # Afficher le tableau formaté en Markdown
            st.markdown(markdown_table)


        with col2:
            # Préparation et affichage du graphique en camembert dans la deuxième colonne
            fig, ax = plt.subplots()
            # Assurez-vous que total_time_by_category est défini avant cette ligne
            total_time_by_category = total_time_by_category[total_time_by_category > 0]
            if total_time_by_category.sum() > 0:
                plot_pie_chart_on_ax(total_time_by_category, f"Répartition du temps par catégorie pour l'étude {study_choice}", ax)
            else:
                ax.text(0.5, 0.5, "Aucune donnée disponible\npour cette catégorie", 
                        ha='center', va='center', fontsize=12, color='darkorange',
                        bbox=dict(facecolor='none', edgecolor='darkorange', boxstyle='round,pad=0.5'))
                ax.set_axis_off()  # Masquer les axes si pas de données
            st.pyplot(fig)

        with col4:
            st.write(f"Temps total passé par ARC sur l'étude {study_choice} :")
            
            # Grouper les données par ARC et calculer le total
            total_time_by_arc = filtered_df_by_study.groupby('ARC')[INT_CATEGORIES].sum().sum(axis=1)
            
            # Vérifier si le DataFrame n'est pas vide
            if not total_time_by_arc.empty:
                # Option 1: Afficher sous forme de tableau avec Markdown
                markdown_table = "ARC | Heures Totales\n:- | -:\n"
                for arc, total_hours in total_time_by_arc.items():
                    markdown_table += f"{arc} | {total_hours:.2f}\n"
                st.markdown(markdown_table)
            else:
                st.write("Aucune donnée disponible pour cette étude.")




#####################################################################
# ====================== LANCEMENT DE L'ALGO ====================== #
#####################################################################

if __name__ == "__main__":
    main()
