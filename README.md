
# **IMATimeTrackerStreamlitApp**

## *Description Brève*
**IMATimeTrackerStreamlitApp** est une suite d'applications Streamlit conçues pour faciliter le suivi et la gestion du temps dans un contexte professionnel. Cette suite se compose de deux applications principales : une pour les employés (`time_entry.py`) et une pour les managers (`time_entry_manager.py`). Ces outils permettent une saisie intuitive du temps, un suivi des projets, et offrent des fonctionnalités de reporting et de gestion.

### Fonctionnalités de `time_entry.py`
- **Authentification des Utilisateurs** : Connexion sécurisée pour les employés.
- **Saisie et Modification du Temps** : Permet aux employés de saisir et de modifier le temps consacré à différents projets ou tâches.
- **Visualisation et Édition des Données** : Affiche le temps passé par semaine ou par année, avec possibilité de visualiser et d'éditer les données historiques.

### Fonctionnalités de `time_entry_manager.py`
- **Gestion des ARCs et des Études** : Permet de gérer les informations des assistants de projet (ARCs) et des études.
- **Suivi et Visualisation des Données** : Offre une visualisation détaillée du temps passé sur différents projets, à la fois sous forme de tableaux et de graphiques.
- **Tableaux de Bord Compréhensifs** : Inclut des dashboards pour chaque ARC et un tableau de bord général pour une vue d'ensemble.

## *Commencer*
Pour lancer une application, naviguez vers le répertoire contenant le script et exécutez l'une des commandes suivantes dans votre terminal :

Pour les employés :
```bash
streamlit run time_entry.py
```

Pour les managers :
```bash
streamlit run time_entry_manager.py
```

## *Prérequis*
- Python 3.6 ou plus récent.
- Bibliothèques Python : `streamlit`, `pandas`, `datetime`, `locale`, `os`.

## *Installation*
1. Clonez le dépôt ou téléchargez les scripts.
2. Installez les dépendances nécessaires : `pip install streamlit pandas`.
3. Exécutez l'application comme indiqué dans la section *Commencer*.

## *Contribution*
Les contributions à **IMATimeTrackerStreamlitApp** sont toujours les bienvenues. Que ce soit pour des corrections de bugs, des améliorations de fonctionnalités ou des suggestions, n'hésitez pas à créer une issue ou une pull request sur le dépôt GitHub.
