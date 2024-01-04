
# **IMATimeTrackerStreamlitApp**

## *Description Brève*
**IMATimeTrackerStreamlitApp** est une suite d'applications Streamlit conçues pour faciliter le suivi et la gestion du temps dans un contexte professionnel. Cette suite se compose de deux applications principales : une pour les employés (`time_entry.py`) et une pour les managers (`time_entry_manager.py`). Ces outils permettent une saisie intuitive du temps, un suivi des projets, et offrent des fonctionnalités de reporting et de gestion.

### Fonctionnalités de `time_entry.py`
- **Saisie du Temps** : Permet aux employés d'enregistrer le temps consacré à différents projets ou tâches.
- **Visualisation Hebdomadaire** : Affiche le temps passé par semaine pour faciliter le suivi et la planification.

### Fonctionnalités de `time_entry_manager.py`
- **Suivi du Temps des Employés** : Offre aux managers une vue d'ensemble du temps enregistré par les membres de l'équipe.
- **Analyse des Données** : Permet une analyse approfondie du temps passé sur différents projets pour une meilleure allocation des ressources.
- **Gestion des Projets et des Employés** : Les managers peuvent gérer les affectations de projets et surveiller la charge de travail des employés.

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
