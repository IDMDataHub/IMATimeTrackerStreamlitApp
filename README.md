
# **IMATimeTrackerStreamlitApp**

## *Brève Description*
**IMATimeTrackerStreamlitApp** est une suite d'applications Streamlit conçue pour améliorer le suivi et la gestion du temps dans un environnement professionnel. Cette suite comprend deux applications principales adaptées aux besoins spécifiques des employés et des managers : `time_entry_online.py` pour les employés et `time_entry_manager_online.py` pour les managers. Ces outils offrent une interface intuitive pour la saisie du temps, le suivi des projets et fournissent des fonctionnalités avancées de reporting et de gestion.

### Fonctionnalités de `time_entry_online.py`
- **Authentification des Utilisateurs** : Permet une connexion sécurisée pour les employés via une interface d'authentification intégrée.
- **Saisie et Modification du Temps** : Les employés peuvent facilement saisir et modifier le temps passé sur différents projets ou tâches.
- **Visualisation et Édition des Données** : Offre la possibilité d'afficher le temps passé par semaine ou par année, avec des options pour visualiser et éditer les entrées historiques.
- **Intégration avec le Stockage Cloud** : Utilise les services AWS S3 pour le stockage et la récupération sécurisée des données.

### Fonctionnalités de `time_entry_manager_online.py`
- **Gestion des Informations des ARCs et des Études** : Permet aux managers de gérer les informations relatives aux assistants de recherche clinique (ARCs) et aux études en cours.
- **Suivi Avancé et Visualisation des Données** : Propose une vue détaillée du temps alloué aux différents projets, avec des tableaux et des graphiques pour un suivi approfondi.
- **Tableaux de Bord Détaillés** : Inclut des tableaux de bord pour chaque ARC et un tableau de bord général offrant une vue d'ensemble complète.

## *Pour Commencer*
Pour lancer une application, naviguez vers le répertoire contenant le script correspondant et exécutez la commande appropriée dans votre terminal :

Pour les employés :
```bash
streamlit run time_entry_online.py
```

Pour les managers :
```bash
streamlit run time_entry_manager_online.py
```

## *Prérequis*
- Python 3.9 ou plus récent.
- Bibliothèques Python : `streamlit`, `pandas`, `datetime`, `locale`, `os`, `boto3`.

## *Installation*
1. Clonez le dépôt ou téléchargez les scripts.
2. Installez les dépendances nécessaires en utilisant la commande : `pip install streamlit pandas boto3`.
3. Lancez l'application en suivant les instructions de la section *Pour Commencer*.

## *Contribution*
Les contributions à **IMATimeTrackerStreamlitApp** sont bienvenues. Pour toute correction de bug, amélioration de fonctionnalités ou suggestion, n'hésitez pas à ouvrir une issue ou une pull request sur le dépôt GitHub.
