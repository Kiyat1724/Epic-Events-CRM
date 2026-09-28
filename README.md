# Epic Events CRM

Epic Events CRM est une application sécurisée en ligne de commande destinée à
la gestion des collaborateurs, clients, contrats et événements d’Epic Events.

Le projet utilise Python, Click, SQLAlchemy, PostgreSQL, Alembic, Argon2 et JWT.

## Fonctionnalités

L’application permet notamment de :

- authentifier les collaborateurs ;
- gérer une session locale avec un JWT expirant ;
- gérer les collaborateurs ;
- créer et modifier les clients ;
- créer, modifier et filtrer les contrats ;
- créer les événements associés aux contrats signés ;
- affecter un collaborateur support à un événement ;
- filtrer les événements sans support ou affectés au support connecté ;
- contrôler les opérations selon le rôle et la propriété de la ressource ;
- transmettre les erreurs inattendues à Sentry lorsqu’un DSN est configuré.

## Architecture

Le projet utilise une architecture en couches :

```text
CLI Click
    ↓
Services métier et permissions
    ↓
Repositories
    ↓
Modèles SQLAlchemy
    ↓
PostgreSQL
```

### Couche CLI

Le dossier `epic_events/cli` contient les commandes Click. Cette couche gère :

- les saisies de l’utilisateur ;
- les arguments des commandes ;
- l’affichage des résultats ;
- la conversion des erreurs métier en messages lisibles.

### Couche service

Le dossier `epic_events/services` contient :

- les règles métier ;
- les validations ;
- le hashage et la vérification des mots de passe ;
- la création et la vérification des JWT ;
- la gestion de la session locale ;
- le contrôle des permissions.

### Couche repository

Le dossier `epic_events/repositories` centralise les opérations de lecture et
d’écriture réalisées avec SQLAlchemy.

### Modèles

Le dossier `epic_events/models` contient les modèles SQLAlchemy :

- `Role` ;
- `Employee` ;
- `Client` ;
- `Contract` ;
- `Event`.

## Diagramme de données

Le diagramme entité-relation est disponible dans :

```text
diagrams/epic_events_erd.png
```

La source DBML est disponible dans :

```text
diagrams/epic_events_erd.dbml
```

## Prérequis

- Python 3.13 ou supérieur ;
- PostgreSQL ;
- `uv`.

Vérification :

```powershell
python --version
uv --version
psql --version
```

## Installation

Depuis le dossier du projet :

```powershell
uv sync --dev
```

Cette commande crée l’environnement virtuel et installe les dépendances de
production et de développement à partir de `pyproject.toml` et `uv.lock`.

## Configuration PostgreSQL

Se connecter à PostgreSQL avec un compte administrateur :

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -p 5432
```

Créer un rôle applicatif sans privilèges administrateur :

```sql
CREATE ROLE epic_events_app
WITH LOGIN
NOSUPERUSER
NOCREATEDB
NOCREATEROLE
NOREPLICATION
NOBYPASSRLS;
```

Définir son mot de passe :

```text
\password epic_events_app
```

Créer la base :

```sql
CREATE DATABASE epic_events OWNER epic_events_app;
```

Quitter PostgreSQL :

```text
\q
```

## Variables d’environnement

Copier le fichier d’exemple :

```powershell
Copy-Item .env.example .env
```

Compléter `.env` :

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=epic_events
DB_USER=epic_events_app
DB_PASSWORD=mot_de_passe_postgresql
JWT_SECRET=secret_jwt_aleatoire
SENTRY_DSN=
```

Générer une clé JWT aléatoire :

```powershell
uv run python -c "import secrets; print(secrets.token_urlsafe(64))"
```

La valeur obtenue doit être copiée dans `JWT_SECRET`.

Le fichier `.env` contient des secrets et ne doit jamais être ajouté à Git.

## Migrations Alembic

Créer ou mettre à jour le schéma de base de données :

```powershell
uv run alembic upgrade head
```

La commande suivante fournit le même résultat et vérifie la présence des cinq
tables métier :

```powershell
uv run python -m epic_events.init_db
```

Afficher la migration actuellement appliquée :

```powershell
uv run alembic current
```

Vérifier que les modèles et la base sont synchronisés :

```powershell
uv run alembic check
```

### Créer une future migration

Après une modification des modèles :

```powershell
uv run alembic revision --autogenerate -m "Description de la modification"
```

Le fichier généré doit toujours être relu avant son application :

```powershell
uv run alembic upgrade head
```

## Données initiales

Créer les rôles `management`, `sales` et `support` :

```powershell
uv run python -m epic_events.seed_data
```

La commande est idempotente : elle ne crée pas de doublons si les rôles
existent déjà.

## Premier compte management

Créer le premier compte management :

```powershell
uv run python main.py bootstrap-admin
```

Cette commande est refusée dès qu’un compte management existe déjà.

## Commandes principales

Afficher toutes les commandes :

```powershell
uv run python main.py --help
```

### Authentification

```powershell
uv run python main.py login
uv run python main.py status
uv run python main.py logout
```

### Collaborateurs

```powershell
uv run python main.py employees --help
uv run python main.py employees list
uv run python main.py employees show <EMPLOYEE_ID>
uv run python main.py employees create
uv run python main.py employees update <EMPLOYEE_ID>
uv run python main.py employees delete <EMPLOYEE_ID>
```

### Clients

```powershell
uv run python main.py clients --help
uv run python main.py clients list
uv run python main.py clients show <CLIENT_ID>
uv run python main.py clients create
uv run python main.py clients update <CLIENT_ID>
```

### Contrats

```powershell
uv run python main.py contracts --help
uv run python main.py contracts list
uv run python main.py contracts show <CONTRACT_ID>
uv run python main.py contracts unsigned
uv run python main.py contracts unpaid
uv run python main.py contracts create
uv run python main.py contracts update <CONTRACT_ID>
```

### Événements

```powershell
uv run python main.py events --help
uv run python main.py events list
uv run python main.py events show <EVENT_ID>
uv run python main.py events without-support
uv run python main.py events assigned
uv run python main.py events create
uv run python main.py events assign-support <EVENT_ID> <SUPPORT_EMPLOYEE_ID>
uv run python main.py events update <EVENT_ID>
```

Les dates d’événement doivent utiliser un format ISO 8601 avec fuseau horaire :

```text
2026-10-10T14:00:00+02:00
```

## Permissions

| Action | Management | Sales | Support |
|---|:---:|:---:|:---:|
| Lire les clients, contrats et événements | Oui | Oui | Oui |
| Gérer les collaborateurs | Oui | Non | Non |
| Créer un client | Non | Oui | Non |
| Modifier ses propres clients | Non | Oui | Non |
| Créer un contrat | Oui | Non | Non |
| Modifier tous les contrats | Oui | Non | Non |
| Modifier les contrats de ses clients | Non | Oui | Non |
| Filtrer les contrats non signés ou impayés | Oui | Oui | Oui |
| Créer un événement pour son contrat signé | Non | Oui | Non |
| Voir les événements sans support | Oui | Non | Non |
| Affecter un support | Oui | Non | Non |
| Voir ses événements affectés | Non | Non | Oui |
| Modifier ses événements affectés | Non | Non | Oui |

Les permissions sont centralisées dans
`epic_events/services/permission_service.py`.

## Sécurité

### Mots de passe

Les mots de passe sont hachés avec Argon2id et ne sont jamais enregistrés en
clair.

Argon2 génère automatiquement un salt aléatoire pour chaque hash. Deux
hashages successifs du même mot de passe produisent donc deux chaînes
différentes, tout en restant vérifiables.

### JWT

Après une authentification réussie, l’application crée un JSON Web Token signé
contenant notamment :

- l’identifiant du collaborateur ;
- son email ;
- son rôle ;
- une date d’expiration ;
- un identifiant unique de token.

Le JWT ne contient jamais le mot de passe.

### Secrets

Les identifiants PostgreSQL, le secret JWT et le DSN Sentry sont chargés depuis
les variables d’environnement.

Le fichier `.env` est exclu de Git.

### Base de données

L’application utilise un compte PostgreSQL dédié sans privilèges
administrateur.

Les requêtes sont construites avec SQLAlchemy et utilisent des paramètres
plutôt que de concaténer directement les valeurs saisies à du SQL.

### Sentry

Sentry est initialisé uniquement si `SENTRY_DSN` contient une valeur.

L’application utilise :

```python
send_default_pii=False
```

afin de ne pas transmettre automatiquement des données personnelles.

## Tests

Exécuter tous les tests :

```powershell
uv run python -m pytest -q
```

Le projet contient :

- des tests unitaires des services ;
- des tests unitaires des repositories ;
- des tests des commandes CLI ;
- des tests d’intégration utilisant une base SQL temporaire.

Mesurer la couverture :

```powershell
uv run python -m pytest --cov=epic_events --cov-report=term-missing
```

Au dernier contrôle, le projet comportait 137 tests réussis et une couverture
globale d’environ 73 %. Les services métier sensibles sont couverts entre 81 %
et 96 %.

## Qualité du code

Vérifier le formatage Black :

```powershell
uv run black --check migrations epic_events tests main.py
```

Vérifier la conformité Flake8 :

```powershell
uv run flake8 migrations epic_events tests main.py
```

## Structure principale

```text
Epic_Events_CRM/
├── diagrams/
├── epic_events/
│   ├── cli/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── config.py
│   ├── database.py
│   ├── init_db.py
│   ├── monitoring.py
│   └── seed_data.py
├── migrations/
│   ├── versions/
│   └── env.py
├── tests/
│   ├── integration/
│   └── unit/
├── .env.example
├── .flake8
├── .gitignore
├── alembic.ini
├── main.py
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

## Technologies

- Python 3.13 ;
- Click ;
- SQLAlchemy ;
- PostgreSQL et Psycopg ;
- Alembic ;
- Argon2-cffi ;
- PyJWT ;
- python-dotenv ;
- Sentry SDK ;
- Pytest et pytest-cov ;
- Black ;
- Flake8.
