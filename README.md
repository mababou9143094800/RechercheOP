# Solveur de Problèmes de Transport

Ce projet est un petit solveur de problème de transport développé en Python avec une interface graphique `tkinter`.
Il permet de charger des fichiers de problème, de générer une proposition initiale par la méthode Nord-Ouest ou Balas-Hammer, puis d'optimiser la solution avec la méthode des potentiels (MODI / Stepping-Stone).

## Fonctionnalités

- Chargement dynamique d'un fichier `.txt` de problème de transport
- Choix entre deux méthodes d'initialisation :
  - `Nord-Ouest`
  - `Balas-Hammer`
- Affichage étape par étape de la résolution dans une console intégrée
- Sauvegarde du trace d'exécution au format texte
- Interface conviviale avec `tkinter`

## Structure du projet

- `main.py` : application principale et interface utilisateur
- `transport.py` : lecture du problème, algorithmes et affichages
- `problems/` : exemples de fichiers de problème

## Format des fichiers de problème

Chaque fichier `.txt` doit respecter la structure suivante :

1. Première ligne : `n m` où `n` est le nombre de fournisseurs et `m` le nombre de clients
2. Suivies de `n` lignes, chacune contenant `m` coûts puis la capacité du fournisseur
3. Dernière ligne : `m` demandes clients

### Exemple

```
3 4
8 6 10 9 35
9 12 13 7 50
14 9 16 5 40
20 25 30 10
```

Dans cet exemple :
- 3 fournisseurs
- 4 clients
- Coûts de transport pour chaque paire fournisseur-client
- Capacités des fournisseurs : `35`, `50`, `40`
- Demandes des clients : `20`, `25`, `30`, `10`

## Prérequis

- Python 3.x
- `tkinter` (généralement inclus avec les distributions Python standard)

## Exécution

1. Ouvrir un terminal dans le dossier du projet
2. Lancer :

```bash
python main.py
```

3. Dans l'interface, cliquer sur `Charger fichier .txt`
4. Sélectionner un fichier de `problems/`
5. Choisir l'algorithme initial puis cliquer sur `Résoudre`
6. Sauvegarder la trace si nécessaire avec `Sauvegarder`

## Remarques

- Le programme vérifie si le problème est équilibré (total des capacités = total des demandes)
- Les étapes de calcul, la construction du cycle et la recherche d'arêtes améliorantes sont affichées dans la console
- Les fichiers de trace peuvent être enregistrés pour analyse ultérieure

## Exemple de fichiers

Le dossier `problems/` contient plusieurs exemples de problèmes (`problem1.txt`, `problem2.txt`, ..., `problem12.txt`).

---

Bonne utilisation du solveur de transport !