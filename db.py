"""
db.py — Couche d'accès à la base de données SQLite pour l'agent de préparation
de plaidoirie.

Tables :
  - dossiers      : les affaires suivies
  - analyses      : les analyses d'arguments adverses générées par l'IA
  - trames        : bibliothèque de plans réutilisables par domaine
  - jurisprudence : références validées manuellement par l'avocat
"""

import os
import sqlite3
import json
from pathlib import Path
import paths
from datetime import datetime

# PLAIDIA_DB_PATH permet de sortir la base du système de fichiers éphémère
# d'un conteneur (Render/Railway...) en la faisant pointer vers un disque
# persistant monté (ex. /data/plaidoirie.db) -- voir DEPLOIEMENT.md, section
# "Persistance". Sans cette variable, comportement inchangé : la base vit à
# côté de ce fichier (paths.base_dir()), exactement comme avant.
DB_PATH = Path(os.environ["PLAIDIA_DB_PATH"]) if os.environ.get("PLAIDIA_DB_PATH") else paths.base_dir() / "plaidoirie.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS dossiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    numero_dossier TEXT,
    domaine TEXT,
    parties TEXT,
    faits TEXT,
    statut TEXT DEFAULT 'en cours',
    date_creation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    arguments_json TEXT NOT NULL,
    points_attention_json TEXT,
    FOREIGN KEY (dossier_id) REFERENCES dossiers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS trames (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domaine TEXT NOT NULL,
    nom TEXT NOT NULL,
    structure_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jurisprudence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference TEXT NOT NULL,
    resume TEXT,
    domaine TEXT,
    source TEXT,
    validee INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    note_brute TEXT NOT NULL,
    note_structuree TEXT,
    actions_json TEXT,
    points_json TEXT,
    date_creation TEXT NOT NULL,
    FOREIGN KEY (dossier_id) REFERENCES dossiers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS corpus_juridique (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    pays TEXT,
    type_texte TEXT,
    domaine TEXT,
    reference TEXT,
    date_texte TEXT,
    statut TEXT DEFAULT 'en vigueur',
    contenu TEXT NOT NULL,
    validee INTEGER DEFAULT 0,
    date_import TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations_chat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    contenu_json TEXT NOT NULL,
    date_creation TEXT NOT NULL,
    date_modification TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS parametres (
    cle TEXT PRIMARY KEY,
    valeur TEXT
);
"""


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    _migrer_colonnes_manquantes(conn)
    conn.close()
    print(f"Base de données initialisée : {DB_PATH}")


def _migrer_colonnes_manquantes(conn):
    """Ajoute les colonnes ajoutées après la création initiale de bases
    existantes (SQLite ne les crée pas via CREATE TABLE IF NOT EXISTS
    si la table existe déjà). Sans effet sur une base neuve."""
    cur = conn.execute("PRAGMA table_info(dossiers)")
    colonnes_existantes = {row["name"] for row in cur.fetchall()}
    if "numero_dossier" not in colonnes_existantes:
        conn.execute("ALTER TABLE dossiers ADD COLUMN numero_dossier TEXT")
        conn.commit()


TABLES = (
    "parametres",
    "conversations_chat",
    "corpus_juridique",
    "notes",
    "jurisprudence",
    "trames",
    "analyses",
    "dossiers",
)


def reinitialiser_donnees_demo():
    """Vide entièrement la base puis la reconstruit -- réservé au mode démo
    (voir backend/app/demo.py), jamais appelé autrement. Garantit qu'aucune
    donnée saisie par un visiteur ne survit à un redémarrage du serveur de
    démonstration, conformément à l'avertissement affiché dans l'app."""
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = OFF;")
    for table in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()
    conn.close()
    init_db()


def _assurer_migration():
    """Vérifie et applique les migrations nécessaires, silencieusement,
    à chaque connexion — pour que les fonctions marchent même si
    init-db n'a pas été relancé après une mise à jour du programme."""
    conn = get_connection()
    _migrer_colonnes_manquantes(conn)
    conn.close()


# --- Dossiers ---------------------------------------------------------

def create_dossier(nom, domaine="", parties="", faits="", numero_dossier=""):
    _assurer_migration()
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO dossiers (nom, numero_dossier, domaine, parties, faits, date_creation) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (nom, numero_dossier, domaine, parties, faits, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    dossier_id = cur.lastrowid
    conn.close()
    return dossier_id


def list_dossiers():
    _assurer_migration()
    conn = get_connection()
    rows = conn.execute("SELECT * FROM dossiers ORDER BY date_creation DESC").fetchall()
    conn.close()
    return rows


def get_dossier(dossier_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM dossiers WHERE id = ?", (dossier_id,)).fetchone()
    conn.close()
    return row


def update_statut(dossier_id, statut):
    conn = get_connection()
    conn.execute("UPDATE dossiers SET statut = ? WHERE id = ?", (statut, dossier_id))
    conn.commit()
    conn.close()


def delete_dossier(dossier_id):
    """Supprime un dossier et, grâce à ON DELETE CASCADE, toutes ses
    analyses liées. Irréversible."""
    conn = get_connection()
    conn.execute("DELETE FROM dossiers WHERE id = ?", (dossier_id,))
    conn.commit()
    conn.close()


def update_domaine(dossier_id, nouveau_domaine):
    conn = get_connection()
    conn.execute("UPDATE dossiers SET domaine = ? WHERE id = ?", (nouveau_domaine, dossier_id))
    conn.commit()
    conn.close()


def ajouter_aux_faits(dossier_id, texte_supplementaire, source=""):
    """Ajoute du texte (extrait d'un document importé) aux faits existants
    d'un dossier, sans écraser ce qui était déjà là. Utilisé pour construire
    un dossier progressivement à partir de plusieurs documents."""
    conn = get_connection()
    row = conn.execute("SELECT faits FROM dossiers WHERE id = ?", (dossier_id,)).fetchone()
    faits_actuels = row["faits"] or ""

    horodatage = datetime.now().strftime("%d/%m/%Y %H:%M")
    entete = f"--- Document importé le {horodatage}" + (f" ({source})" if source else "") + " ---"
    nouveau_bloc = f"{entete}\n{texte_supplementaire}"

    faits_mis_a_jour = f"{faits_actuels}\n\n{nouveau_bloc}" if faits_actuels else nouveau_bloc

    conn.execute("UPDATE dossiers SET faits = ? WHERE id = ?", (faits_mis_a_jour, dossier_id))
    conn.commit()
    conn.close()


def rechercher_dans_dossiers(mot_cle: str) -> list:
    """Recherche un mot-clé dans les faits, parties, nom et domaine de tous
    les dossiers, ainsi que dans le contenu de leurs analyses enregistrées.
    Retourne une liste de dicts {dossier, extraits} pour chaque dossier
    correspondant, avec un court extrait de contexte autour du terme trouvé."""
    conn = get_connection()
    mot_cle_lower = mot_cle.lower()
    resultats = []

    dossiers = conn.execute("SELECT * FROM dossiers").fetchall()
    for d in dossiers:
        extraits = []

        for champ in ("faits", "parties", "nom", "domaine"):
            valeur = d[champ] or ""
            if mot_cle_lower in valeur.lower():
                idx = valeur.lower().index(mot_cle_lower)
                debut = max(0, idx - 50)
                fin = min(len(valeur), idx + len(mot_cle) + 50)
                extrait = ("…" if debut > 0 else "") + valeur[debut:fin] + ("…" if fin < len(valeur) else "")
                extraits.append((champ, extrait))

        analyses = conn.execute(
            "SELECT * FROM analyses WHERE dossier_id = ? ORDER BY date DESC", (d["id"],)
        ).fetchall()
        for a in analyses:
            contenu = (a["arguments_json"] or "") + " " + (a["points_attention_json"] or "")
            if mot_cle_lower in contenu.lower():
                extraits.append(("analyse du " + a["date"][:10], "correspondance trouvée dans les arguments analysés"))
                break

        if extraits:
            resultats.append({"dossier": dict(d), "extraits": extraits})

    conn.close()
    return resultats


# --- Analyses -----------------------------------------------------------

def save_analyse(dossier_id, arguments, points_attention):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO analyses (dossier_id, date, arguments_json, points_attention_json) "
        "VALUES (?, ?, ?, ?)",
        (
            dossier_id,
            datetime.now().isoformat(timespec="seconds"),
            json.dumps(arguments, ensure_ascii=False),
            json.dumps(points_attention, ensure_ascii=False),
        ),
    )
    conn.commit()
    analyse_id = cur.lastrowid
    conn.close()
    return analyse_id


def get_analyses_for_dossier(dossier_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM analyses WHERE dossier_id = ? ORDER BY date DESC", (dossier_id,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "date": r["date"],
            "arguments": json.loads(r["arguments_json"]),
            "points_attention": json.loads(r["points_attention_json"] or "[]"),
        })
    return result


# --- Trames ---------------------------------------------------------------

def save_trame(domaine, nom, structure):
    conn = get_connection()
    conn.execute(
        "INSERT INTO trames (domaine, nom, structure_json) VALUES (?, ?, ?)",
        (domaine, nom, json.dumps(structure, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def get_trames(domaine=None):
    conn = get_connection()
    if domaine:
        rows = conn.execute("SELECT * FROM trames WHERE domaine = ?", (domaine,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM trames").fetchall()
    conn.close()
    return [{"id": r["id"], "domaine": r["domaine"], "nom": r["nom"],
              "structure": json.loads(r["structure_json"])} for r in rows]


# --- Jurisprudence (validée manuellement uniquement) ------------------

def add_jurisprudence(reference, resume, domaine, source, validee=False):
    conn = get_connection()
    conn.execute(
        "INSERT INTO jurisprudence (reference, resume, domaine, source, validee) "
        "VALUES (?, ?, ?, ?, ?)",
        (reference, resume, domaine, source, int(validee)),
    )
    conn.commit()
    conn.close()


def get_jurisprudence_validee(domaine=None):
    conn = get_connection()
    if domaine:
        rows = conn.execute(
            "SELECT * FROM jurisprudence WHERE validee = 1 AND domaine = ?", (domaine,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM jurisprudence WHERE validee = 1").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_jurisprudence_en_attente(domaine=None):
    """Références collectées automatiquement mais pas encore validées manuellement."""
    conn = get_connection()
    if domaine:
        rows = conn.execute(
            "SELECT * FROM jurisprudence WHERE validee = 0 AND domaine = ?", (domaine,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM jurisprudence WHERE validee = 0").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def valider_jurisprudence(jurisprudence_id):
    conn = get_connection()
    conn.execute("UPDATE jurisprudence SET validee = 1 WHERE id = ?", (jurisprudence_id,))
    conn.commit()
    conn.close()


def rejeter_jurisprudence(jurisprudence_id):
    """Supprime une entrée non pertinente collectée automatiquement."""
    conn = get_connection()
    conn.execute("DELETE FROM jurisprudence WHERE id = ? AND validee = 0", (jurisprudence_id,))
    conn.commit()
    conn.close()


# --- Notes -----------------------------------------------------------

def ajouter_note(dossier_id, note_brute, note_structuree="", actions=None, points=None):
    """Enregistre une note de travail rattachée à un dossier, avec sa
    version brute et sa version structurée par l'IA (si disponible)."""
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO notes (dossier_id, note_brute, note_structuree, actions_json, points_json, date_creation) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            dossier_id, note_brute, note_structuree,
            json.dumps(actions or [], ensure_ascii=False),
            json.dumps(points or [], ensure_ascii=False),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    note_id = cur.lastrowid
    conn.close()
    return note_id


def get_notes_dossier(dossier_id):
    """Récupère toutes les notes d'un dossier, les plus récentes en premier."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM notes WHERE dossier_id = ? ORDER BY date_creation DESC", (dossier_id,)
    ).fetchall()
    conn.close()
    resultat = []
    for r in rows:
        resultat.append({
            "id": r["id"],
            "note_brute": r["note_brute"],
            "note_structuree": r["note_structuree"],
            "actions": json.loads(r["actions_json"] or "[]"),
            "points": json.loads(r["points_json"] or "[]"),
            "date_creation": r["date_creation"],
        })
    return resultat


def delete_note(note_id):
    conn = get_connection()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()


# --- Corpus juridique multi-source (OHADA, UE, Sénégal...) ----------

def ajouter_texte_corpus(source, contenu, pays="", type_texte="", domaine="", reference="", date_texte="", validee=False):
    """Ajoute un texte juridique à la base multi-source (OHADA, UE,
    droit sénégalais...). Non validé par défaut — doit être relu avant
    d'être utilisable en contexte par l'agent."""
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO corpus_juridique (source, pays, type_texte, domaine, reference, date_texte, contenu, validee, date_import) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (source, pays, type_texte, domaine, reference, date_texte, contenu, int(validee), datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    texte_id = cur.lastrowid
    conn.close()
    return texte_id


def get_corpus_valide(source=None, pays=None, domaine=None):
    """Récupère les textes validés du corpus multi-source, filtrables par
    source, pays et/ou domaine."""
    conn = get_connection()
    query = "SELECT * FROM corpus_juridique WHERE validee = 1"
    params = []
    if source:
        query += " AND source = ?"
        params.append(source)
    if pays:
        query += " AND pays = ?"
        params.append(pays)
    if domaine:
        query += " AND domaine = ?"
        params.append(domaine)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_corpus_en_attente():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM corpus_juridique WHERE validee = 0").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def lister_sources_corpus():
    """Retourne la liste des sources distinctes déjà présentes dans le
    corpus (validées ou non), pour construire le sélecteur de sources."""
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT source FROM corpus_juridique ORDER BY source").fetchall()
    conn.close()
    return [r["source"] for r in rows]


def valider_texte_corpus(texte_id):
    conn = get_connection()
    conn.execute("UPDATE corpus_juridique SET validee = 1 WHERE id = ?", (texte_id,))
    conn.commit()
    conn.close()


def rejeter_texte_corpus(texte_id):
    conn = get_connection()
    conn.execute("DELETE FROM corpus_juridique WHERE id = ? AND validee = 0", (texte_id,))
    conn.commit()
    conn.close()


# --- Conversations du chat (« Poser une question ») -------------------
# Sauvegarde automatique à chaque message, sur le modèle de Claude.ai :
# l'avocat n'a jamais à cliquer sur « Enregistrer » — chaque conversation
# est retrouvable plus tard dans la liste, et supprimable pour libérer
# de l'espace si la base grossit trop avec le temps.

def creer_conversation_chat(titre, historique):
    """Crée une nouvelle conversation enregistrée et retourne son id.
    `historique` est la liste [{"role": ..., "content": ...}, ...]."""
    conn = get_connection()
    maintenant = datetime.now().isoformat()
    cur = conn.execute(
        "INSERT INTO conversations_chat (titre, contenu_json, date_creation, date_modification) VALUES (?, ?, ?, ?)",
        (titre, json.dumps(historique, ensure_ascii=False), maintenant, maintenant),
    )
    conn.commit()
    nouvel_id = cur.lastrowid
    conn.close()
    return nouvel_id


def mettre_a_jour_conversation_chat(conversation_id, historique):
    """Réenregistre le contenu complet d'une conversation existante —
    appelé après chaque nouvel échange, silencieusement."""
    conn = get_connection()
    conn.execute(
        "UPDATE conversations_chat SET contenu_json = ?, date_modification = ? WHERE id = ?",
        (json.dumps(historique, ensure_ascii=False), datetime.now().isoformat(), conversation_id),
    )
    conn.commit()
    conn.close()


def lister_conversations_chat():
    """Liste toutes les conversations enregistrées, les plus récemment
    modifiées en premier — pour l'affichage façon « historique des
    discussions » de Claude.ai."""
    conn = get_connection()
    cur = conn.execute(
        "SELECT id, titre, date_creation, date_modification FROM conversations_chat ORDER BY date_modification DESC"
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_conversation_chat(conversation_id):
    """Récupère une conversation enregistrée, avec son historique déjà
    décodé (liste de messages), prête à être rechargée dans le chat."""
    conn = get_connection()
    cur = conn.execute("SELECT * FROM conversations_chat WHERE id = ?", (conversation_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["historique"] = json.loads(d["contenu_json"])
    return d


def supprimer_conversation_chat(conversation_id):
    """Supprime une conversation enregistrée — pour libérer de l'espace."""
    conn = get_connection()
    conn.execute("DELETE FROM conversations_chat WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()


def taille_base_octets():
    """Taille actuelle du fichier de base de données, en octets — pour
    donner à l'avocat une idée concrète de l'espace utilisé."""
    try:
        return DB_PATH.stat().st_size
    except FileNotFoundError:
        return 0


# --- Paramètres persistants (petit stockage clé/valeur) ---------------
# Sert par exemple à mémoriser la juridiction choisie d'un lancement de
# l'application à l'autre — comme n'importe quelle appli moderne se
# souvient de vos derniers réglages, sans avoir à les redéfinir à chaque
# ouverture.

def get_parametre(cle, defaut=None):
    conn = get_connection()
    cur = conn.execute("SELECT valeur FROM parametres WHERE cle = ?", (cle,))
    row = cur.fetchone()
    conn.close()
    return row["valeur"] if row else defaut


def set_parametre(cle, valeur):
    conn = get_connection()
    conn.execute(
        "INSERT INTO parametres (cle, valeur) VALUES (?, ?) "
        "ON CONFLICT(cle) DO UPDATE SET valeur = excluded.valeur",
        (cle, valeur),
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
