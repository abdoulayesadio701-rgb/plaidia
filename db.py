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
    partie_representee TEXT,
    stade_procedure TEXT,
    objectif TEXT,
    statut TEXT DEFAULT 'en cours',
    date_creation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    arguments_json TEXT NOT NULL,
    points_attention_json TEXT,
    statut TEXT NOT NULL DEFAULT 'Brouillon',
    langue TEXT NOT NULL DEFAULT 'fr',
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
    date_modification TEXT NOT NULL,
    dossier_id INTEGER,
    FOREIGN KEY (dossier_id) REFERENCES dossiers(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS parametres (
    cle TEXT PRIMARY KEY,
    valeur TEXT
);

CREATE TABLE IF NOT EXISTS versions_document (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER,             -- NULL pour les fonctionnalités indépendantes d'un dossier (style, pv_audience...)
    document_id INTEGER,
    feature TEXT NOT NULL,          -- "conclusions" | "plan" | ... (même valeur que ChatContextuelPanel.feature)
    contenu_json TEXT NOT NULL,     -- le résultat complet après modification, tel quel
    resume_modification TEXT,       -- la reponse_agent de l'édition qui a produit cette version, ou une description de restauration
    auteur TEXT NOT NULL,           -- "ia" | "utilisateur" (voir db.py::enregistrer_version/restaurer_version)
    date_creation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents_generes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    feature TEXT NOT NULL,
    titre TEXT NOT NULL,
    parametres_json TEXT NOT NULL DEFAULT '{}',
    contenu_json TEXT NOT NULL,
    statut TEXT NOT NULL DEFAULT 'Brouillon',
    langue TEXT NOT NULL DEFAULT 'fr',
    date_creation TEXT NOT NULL,
    date_modification TEXT NOT NULL,
    FOREIGN KEY (dossier_id) REFERENCES dossiers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,            -- "analyser" | "plan" | "simulateur" | ... (feature -- voir gui.py::PlaidIAApp._lancer_generation)
    dossier_id INTEGER,            -- NULL pour les fonctionnalités indépendantes d'un dossier (besoin_dossier=False)
    libelle TEXT NOT NULL,         -- résumé lisible affiché dans l'historique (ex. "Plan de plaidoirie")
    contenu_json TEXT,             -- résultat complet en JSON -- NULL tant que statut='en_cours'
    statut TEXT NOT NULL DEFAULT 'en_cours',  -- "en_cours" | "terminee" | "erreur" -- jamais d'autre valeur, jamais réécrit hors de ce cycle
    erreur TEXT,                   -- message d'erreur si statut='erreur', sinon NULL
    date_creation TEXT NOT NULL,   -- lancement de la génération
    date_fin TEXT,                 -- fin (succès ou échec) -- NULL tant que statut='en_cours'
    FOREIGN KEY (dossier_id) REFERENCES dossiers(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS elements_veille_vus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    type TEXT NOT NULL,            -- "jurisprudence" | "loi"
    reference TEXT NOT NULL,       -- référence jurisprudence, ou "<code>:<numéro>" pour un article
    date_vue TEXT NOT NULL,
    UNIQUE(dossier_id, type, reference),
    FOREIGN KEY (dossier_id) REFERENCES dossiers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS articles_surveilles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,                  -- "CP" | "CCIV" | ... (voir analyse.REGLE_BALISAGE_CITATIONS)
    numero TEXT NOT NULL,
    dernier_id_version TEXT,             -- LEGIARTI... vu au dernier contrôle Légifrance
    dernier_etat TEXT,                   -- "VIGUEUR" | "ABROGE" | ... au dernier contrôle
    derniere_verification TEXT NOT NULL, -- pour ne pas réinterroger Légifrance plus d'une fois par jour (quota API)
    UNIQUE(code, numero)
);

CREATE TABLE IF NOT EXISTS articles_cites_dossier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    code TEXT NOT NULL,
    numero TEXT NOT NULL,
    derniere_extraction TEXT NOT NULL,   -- dernier passage de veille où ce lien a été confirmé présent
    UNIQUE(dossier_id, code, numero),
    FOREIGN KEY (dossier_id) REFERENCES dossiers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alertes_articles_dossier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    code TEXT NOT NULL,
    numero TEXT NOT NULL,
    ancien_etat TEXT,
    nouvel_etat TEXT,
    date_modification TEXT,              -- date d'effet du changement, si connue (dateDebut de la nouvelle version)
    lien_source TEXT,                    -- URL Légifrance vers l'article à jour
    date_detection TEXT NOT NULL,
    statut TEXT NOT NULL DEFAULT 'active',  -- "active" | "acquittee" -- jamais résolue autrement que par acquitter_alerte_article
    FOREIGN KEY (dossier_id) REFERENCES dossiers(id) ON DELETE CASCADE
);

-- Pendant de alertes_articles_dossier pour la jurisprudence, mais utilisée
-- UNIQUEMENT par l'orchestrateur de veille du backend web (backend/app/
-- veille.py) -- gui.py garde son propre badge de veille jurisprudence
-- éphémère (self.notifications_veille, en mémoire) tel quel, jamais
-- modifié. Nécessaire côté web car il n'existe pas de session unique où
-- garder un badge en mémoire : la persistance est la seule façon pour
-- plusieurs rechargements de page de voir la même notification tant
-- qu'elle n'est pas acquittée.
CREATE TABLE IF NOT EXISTS alertes_jurisprudence_dossier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER NOT NULL,
    reference TEXT NOT NULL,
    resume TEXT,
    source TEXT,
    date_detection TEXT NOT NULL,
    statut TEXT NOT NULL DEFAULT 'active',  -- "active" | "acquittee"
    FOREIGN KEY (dossier_id) REFERENCES dossiers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS elements_epingles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,            -- "dossier" | "analyse" (voir app/schemas/epingles.py pour la liste à jour)
    reference_id INTEGER NOT NULL, -- id du dossier ou de l'analyse épinglé
    dossier_id INTEGER,            -- dossier associé, pour le nettoyage en cascade et l'affichage groupé
    libelle TEXT NOT NULL,         -- capturé au moment de l'épinglage -- jamais recalculé depuis l'original,
                                    -- l'épinglage est un raccourci, pas une copie du contenu
    date_creation TEXT NOT NULL
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

    for colonne in ("partie_representee", "stade_procedure", "objectif"):
        if colonne not in colonnes_existantes:
            conn.execute(f"ALTER TABLE dossiers ADD COLUMN {colonne} TEXT")
    conn.commit()

    cur = conn.execute("PRAGMA table_info(analyses)")
    colonnes_existantes = {row["name"] for row in cur.fetchall()}
    if "statut" not in colonnes_existantes:
        conn.execute("ALTER TABLE analyses ADD COLUMN statut TEXT NOT NULL DEFAULT 'Brouillon'")
        conn.commit()
    if "langue" not in colonnes_existantes:
        conn.execute("ALTER TABLE analyses ADD COLUMN langue TEXT NOT NULL DEFAULT 'fr'")
        conn.commit()

    cur = conn.execute("PRAGMA table_info(documents_generes)")
    colonnes_existantes = {row["name"] for row in cur.fetchall()}
    if "langue" not in colonnes_existantes:
        conn.execute("ALTER TABLE documents_generes ADD COLUMN langue TEXT NOT NULL DEFAULT 'fr'")
        conn.commit()

    cur = conn.execute("PRAGMA table_info(conversations_chat)")
    colonnes_existantes = {row["name"] for row in cur.fetchall()}
    if "dossier_id" not in colonnes_existantes:
        conn.execute(
            "ALTER TABLE conversations_chat ADD COLUMN dossier_id INTEGER REFERENCES dossiers(id) ON DELETE SET NULL"
        )
        conn.commit()

    cur = conn.execute("PRAGMA table_info(versions_document)")
    colonnes_existantes = {row["name"] for row in cur.fetchall()}
    if "document_id" not in colonnes_existantes:
        conn.execute("ALTER TABLE versions_document ADD COLUMN document_id INTEGER")
        conn.commit()


TABLES = (
    "alertes_jurisprudence_dossier",
    "alertes_articles_dossier",
    "articles_cites_dossier",
    "articles_surveilles",
    "elements_veille_vus",
    "generations",
    "documents_generes",
    "versions_document",
    "elements_epingles",
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

def create_dossier(nom, domaine="", parties="", faits="", numero_dossier="", partie_representee="", stade_procedure="", objectif=""):
    _assurer_migration()
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO dossiers (nom, numero_dossier, domaine, parties, faits, partie_representee, stade_procedure, objectif, date_creation) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (nom, numero_dossier, domaine, parties, faits, partie_representee, stade_procedure, objectif, datetime.now().isoformat(timespec="seconds")),
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
    analyses liées. Irréversible.

    elements_epingles n'a pas de contrainte FK déclarée (son "type" pointe
    vers l'une ou l'autre table selon le cas, une seule FK ne conviendrait
    pas) -- son nettoyage est donc fait explicitement ici plutôt que par
    SQLite : tout pin (dossier ou analyse) rattaché à ce dossier_id doit
    disparaître avec lui, jamais l'inverse (désépingler ne supprime jamais
    l'original -- voir epingler() ci-dessous)."""
    conn = get_connection()
    conn.execute("DELETE FROM elements_epingles WHERE dossier_id = ?", (dossier_id,))
    conn.execute("DELETE FROM versions_document WHERE dossier_id = ?", (dossier_id,))
    conn.execute("DELETE FROM documents_generes WHERE dossier_id = ?", (dossier_id,))
    conn.execute("DELETE FROM dossiers WHERE id = ?", (dossier_id,))
    conn.commit()
    conn.close()


def update_domaine(dossier_id, nouveau_domaine):
    conn = get_connection()
    conn.execute("UPDATE dossiers SET domaine = ? WHERE id = ?", (nouveau_domaine, dossier_id))
    conn.commit()
    conn.close()


def update_posture(dossier_id, partie_representee, stade_procedure, objectif):
    conn = get_connection()
    conn.execute(
        "UPDATE dossiers SET partie_representee = ?, stade_procedure = ?, objectif = ? WHERE id = ?",
        (partie_representee, stade_procedure, objectif, dossier_id),
    )
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

def save_analyse(dossier_id, arguments, points_attention, langue="fr"):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO analyses (dossier_id, date, arguments_json, points_attention_json, langue) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            dossier_id,
            datetime.now().isoformat(timespec="seconds"),
            json.dumps(arguments, ensure_ascii=False),
            json.dumps(points_attention, ensure_ascii=False),
            langue,
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
            "statut": r["statut"],
            "langue": r["langue"],
        })
    return result


# --- Cycle de vie des documents ----------------------------------------

STATUTS_DOCUMENT = ("Brouillon", "En cours", "En révision", "Validé", "Final")
_TRANSITIONS_DOCUMENT = {
    statut: (
        {statut}
        if statut == "Final"
        else {statut}
        | ({STATUTS_DOCUMENT[index - 1]} if index > 0 else set())
        | ({STATUTS_DOCUMENT[index + 1]} if index < len(STATUTS_DOCUMENT) - 1 else set())
    )
    for index, statut in enumerate(STATUTS_DOCUMENT)
}


# Messages bilingues de ces deux exceptions -- str(e) est renvoyé tel quel
# comme HTTPException.detail par les routers (voir backend/app/routers/
# analyse.py, chat.py, documents.py), donc jamais traduit sinon. Ne peut pas
# réutiliser app.deps._l()/libelle() ici : app.deps importe déjà db, un
# import inverse créerait un cycle -- mini-mécanisme local à la place, même
# principe (langue lue via le même ContextVar que analyse._directive_langue(),
# posé par le middleware X-Langue de backend/app/main.py).
import analyse as legacy_analyse  # noqa: E402

_LIBELLES_CYCLE_VIE = {
    "statut_actuel_inconnu": {"fr": "Statut actuel inconnu : {statut}.", "en": "Unknown current status: {statut}."},
    "statut_cible_inconnu": {"fr": "Statut cible inconnu : {statut}.", "en": "Unknown target status: {statut}."},
    "transition_impossible": {
        "fr": "Transition impossible : {actuel} -> {cible}. Les transitions se font étape par étape et un document Final est définitif.",
        "en": "Impossible transition: {actuel} -> {cible}. Transitions happen step by step and a Final document is definitive.",
    },
    "analyse_finale": {
        "fr": "L'analyse {analyse_id} est Final et ne peut plus être modifiée.",
        "en": "Analysis {analyse_id} is Final and can no longer be modified.",
    },
    "document_final": {
        "fr": "Le document {document_id} est Final et ne peut plus être modifié.",
        "en": "Document {document_id} is Final and can no longer be modified.",
    },
}


def _l_cycle_vie(cle: str, **kwargs) -> str:
    entree = _LIBELLES_CYCLE_VIE.get(cle, {})
    texte = entree.get(legacy_analyse.langue_requete(), entree.get("fr", cle))
    return texte.format(**kwargs) if kwargs else texte


class TransitionStatutInvalide(ValueError):
    """Transition de cycle de vie non autorisée."""


class DocumentFinalError(ValueError):
    """Modification refusée sur un document finalisé."""


def valider_transition_statut(statut_actuel: str, nouveau_statut: str) -> str:
    """Valide une transition adjacente, partagée par tous les documents."""
    if statut_actuel not in STATUTS_DOCUMENT:
        raise TransitionStatutInvalide(_l_cycle_vie("statut_actuel_inconnu", statut=statut_actuel))
    if nouveau_statut not in STATUTS_DOCUMENT:
        raise TransitionStatutInvalide(_l_cycle_vie("statut_cible_inconnu", statut=nouveau_statut))
    if nouveau_statut not in _TRANSITIONS_DOCUMENT[statut_actuel]:
        raise TransitionStatutInvalide(_l_cycle_vie("transition_impossible", actuel=statut_actuel, cible=nouveau_statut))
    return nouveau_statut


def get_analyse(analyse_id):
    _assurer_migration()
    conn = get_connection()
    row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analyse_id,)).fetchone()
    conn.close()
    return row


def changer_statut_analyse(analyse_id, nouveau_statut):
    """Change le statut d'une analyse et trace ce changement dans l'historique."""
    analyse = get_analyse(analyse_id)
    if not analyse:
        return None
    statut = valider_transition_statut(analyse["statut"], nouveau_statut)
    if statut == analyse["statut"]:
        return dict(analyse)
    conn = get_connection()
    conn.execute("UPDATE analyses SET statut = ? WHERE id = ?", (statut, analyse_id))
    conn.commit()
    conn.close()
    enregistrer_version(
        analyse["dossier_id"],
        "conclusions",
        {"analyse_id": analyse_id, "statut": statut},
        resume_modification=f"Statut changé : {analyse['statut']} -> {statut}",
        auteur="utilisateur",
    )
    return dict(get_analyse(analyse_id))


def verifier_analyse_modifiable(analyse_id):
    """Refuse toute édition d'une analyse dont le cycle est arrivé à Final."""
    analyse = get_analyse(analyse_id)
    if analyse and analyse["statut"] == "Final":
        raise DocumentFinalError(_l_cycle_vie("analyse_finale", analyse_id=analyse_id))
    return analyse


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


def valider_texte_corpus_par_source(source, domaine=None):
    """Valide en une seule fois tous les textes en attente d'une même
    source -- pour les imports en masse (ex. un dataset structuré de
    plusieurs milliers d'articles) où une validation une par une serait
    irréaliste et, en pratique, ne serait jamais faite. L'avocat fait ainsi
    explicitement confiance à LA SOURCE dans son ensemble, en un geste
    conscient, plutôt qu'un import silencieusement pré-validé par le
    programme ou des milliers de clics individuels qui ne se produiront
    jamais.

    `domaine` (optionnel) restreint la validation en bloc à un sous-ensemble
    de la source (ex. un seul acte uniforme au sein d'une source "OHADA" qui
    en regroupe plusieurs) -- utile quand un import contient des lots de
    qualité inégale (ex. artefacts OCR sur certains actes seulement) : on
    peut alors valider les lots fiables sans devoir faire confiance à toute
    la source d'un bloc. Retourne le nombre de textes effectivement validés.
    """
    conn = get_connection()
    if domaine:
        cur = conn.execute(
            "UPDATE corpus_juridique SET validee = 1 WHERE source = ? AND domaine = ? AND validee = 0",
            (source, domaine),
        )
    else:
        cur = conn.execute("UPDATE corpus_juridique SET validee = 1 WHERE source = ? AND validee = 0", (source,))
    conn.commit()
    nombre = cur.rowcount
    conn.close()
    return nombre


# --- Conversations du chat (« Poser une question ») -------------------
# Sauvegarde automatique à chaque message, sur le modèle de Claude.ai :
# l'avocat n'a jamais à cliquer sur « Enregistrer » — chaque conversation
# est retrouvable plus tard dans la liste, et supprimable pour libérer
# de l'espace si la base grossit trop avec le temps.

def creer_conversation_chat(titre, historique, dossier_id=None):
    """Crée une nouvelle conversation enregistrée et retourne son id.
    `historique` est la liste [{"role": ..., "content": ...}, ...].
    Les conversations existantes ou indépendantes d'un dossier gardent
    `dossier_id` à NULL."""
    _assurer_migration()
    conn = get_connection()
    maintenant = datetime.now().isoformat()
    cur = conn.execute(
        "INSERT INTO conversations_chat (titre, contenu_json, date_creation, date_modification, dossier_id) VALUES (?, ?, ?, ?, ?)",
        (titre, json.dumps(historique, ensure_ascii=False), maintenant, maintenant, dossier_id),
    )
    conn.commit()
    nouvel_id = cur.lastrowid
    conn.close()
    return nouvel_id


def mettre_a_jour_conversation_chat(conversation_id, historique):
    """Réenregistre le contenu complet d'une conversation existante —
    appelé après chaque nouvel échange, silencieusement."""
    _assurer_migration()
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
    _assurer_migration()
    conn = get_connection()
    cur = conn.execute(
        "SELECT id, titre, date_creation, date_modification, dossier_id FROM conversations_chat ORDER BY date_modification DESC"
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def lister_conversations_chat_par_dossier(dossier_id):
    """Liste les conversations explicitement rattachées à un dossier."""
    _assurer_migration()
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, titre, date_creation, date_modification, dossier_id "
        "FROM conversations_chat WHERE dossier_id = ? ORDER BY date_modification DESC",
        (dossier_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_conversation_chat(conversation_id):
    """Récupère une conversation enregistrée, avec son historique déjà
    décodé (liste de messages), prête à être rechargée dans le chat."""
    _assurer_migration()
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
    _assurer_migration()
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


# --- Versions de document (voir AUDIT_TASKBAR.md, étape 4) --------------
# Branché sur le mécanisme d'édition contextuelle déjà existant
# (chat_actions.appliquer_patch, voir ARCHITECTURE_CHAT_CONTEXTUEL.md) :
# chaque patch appliqué avec succès devient une ligne ici -- c'est le point
# où une nouvelle version d'un résultat naît déjà dans le code actuel,
# jusqu'ici jamais conservée. Jamais de suppression automatique d'une
# ancienne version (voir §8 de la demande) : restaurer_version AJOUTE une
# nouvelle ligne identique à l'ancienne plutôt que de revenir en arrière.

def enregistrer_version(dossier_id, feature: str, contenu, resume_modification: str = "", auteur: str = "ia", document_id=None) -> int:
    _assurer_migration()
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO versions_document (dossier_id, document_id, feature, contenu_json, resume_modification, auteur, date_creation) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (dossier_id, document_id, feature, json.dumps(contenu, ensure_ascii=False), resume_modification, auteur, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    version_id = cur.lastrowid
    conn.close()
    return version_id


def lister_versions(feature: str, dossier_id=None, document_id=None) -> list:
    conn = get_connection()
    filtre_document = " AND document_id = ?" if document_id is not None else ""
    if dossier_id is None:
        rows = conn.execute(
            f"SELECT * FROM versions_document WHERE feature = ? AND dossier_id IS NULL{filtre_document} ORDER BY date_creation DESC, id DESC",
            (feature, document_id) if document_id is not None else (feature,),
        ).fetchall()
    else:
        rows = conn.execute(
            f"SELECT * FROM versions_document WHERE feature = ? AND dossier_id = ?{filtre_document} ORDER BY date_creation DESC, id DESC",
            (feature, dossier_id, document_id) if document_id is not None else (feature, dossier_id),
        ).fetchall()
    conn.close()
    return rows


def get_version(version_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM versions_document WHERE id = ?", (version_id,)).fetchone()
    conn.close()
    return row


def restaurer_version(version_id: int):
    """Ne supprime ni ne modifie aucune ligne existante -- ajoute une
    NOUVELLE version portant le même contenu que celle restaurée, avec
    auteur="utilisateur". L'historique complet reste donc lisible même
    après plusieurs restaurations successives. Retourne la nouvelle ligne,
    ou None si version_id est introuvable."""
    original = get_version(version_id)
    if not original:
        return None
    contenu = json.loads(original["contenu_json"])
    nouvel_id = enregistrer_version(
        original["dossier_id"],
        original["feature"],
        contenu,
        resume_modification=f"Restauration de la version du {original['date_creation']}",
        auteur="utilisateur",
        document_id=original["document_id"] if "document_id" in original.keys() else None,
    )
    return get_version(nouvel_id)


# --- Documents générés --------------------------------------------------

def creer_document_genere(dossier_id, feature, titre, parametres, contenu, langue="fr"):
    _assurer_migration()
    maintenant = datetime.now().isoformat(timespec="seconds")
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO documents_generes (dossier_id, feature, titre, parametres_json, contenu_json, statut, langue, date_creation, date_modification) "
        "VALUES (?, ?, ?, ?, ?, 'Brouillon', ?, ?, ?)",
        (dossier_id, feature, titre, json.dumps(parametres, ensure_ascii=False), json.dumps(contenu, ensure_ascii=False), langue, maintenant, maintenant),
    )
    conn.commit()
    document_id = cur.lastrowid
    conn.close()
    return get_document_genere(document_id)


def get_document_genere(document_id):
    _assurer_migration()
    conn = get_connection()
    row = conn.execute("SELECT * FROM documents_generes WHERE id = ?", (document_id,)).fetchone()
    conn.close()
    if not row:
        return None
    document = dict(row)
    document["parametres"] = json.loads(document.pop("parametres_json"))
    document["contenu"] = json.loads(document.pop("contenu_json"))
    return document


def lister_documents_generes(dossier_id, feature=None):
    _assurer_migration()
    conn = get_connection()
    if feature:
        rows = conn.execute(
            "SELECT id FROM documents_generes WHERE dossier_id = ? AND feature = ? ORDER BY date_modification DESC, id DESC",
            (dossier_id, feature),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id FROM documents_generes WHERE dossier_id = ? ORDER BY date_modification DESC, id DESC", (dossier_id,)
        ).fetchall()
    conn.close()
    return [get_document_genere(row["id"]) for row in rows]


def mettre_a_jour_document_genere(document_id, contenu, parametres=None):
    document = verifier_document_modifiable(document_id)
    if not document:
        return None
    conn = get_connection()
    conn.execute(
        "UPDATE documents_generes SET contenu_json = ?, parametres_json = ?, date_modification = ? WHERE id = ?",
        (json.dumps(contenu, ensure_ascii=False), json.dumps(parametres if parametres is not None else document["parametres"], ensure_ascii=False), datetime.now().isoformat(timespec="seconds"), document_id),
    )
    conn.commit()
    conn.close()
    return get_document_genere(document_id)


def changer_statut_document(document_id, nouveau_statut):
    document = get_document_genere(document_id)
    if not document:
        return None
    statut = valider_transition_statut(document["statut"], nouveau_statut)
    if statut == document["statut"]:
        return document
    conn = get_connection()
    conn.execute(
        "UPDATE documents_generes SET statut = ?, date_modification = ? WHERE id = ?",
        (statut, datetime.now().isoformat(timespec="seconds"), document_id),
    )
    conn.commit()
    conn.close()
    enregistrer_version(
        document["dossier_id"], document["feature"], {"document_id": document_id, "statut": statut},
        resume_modification=f"Statut changé : {document['statut']} -> {statut}", auteur="utilisateur", document_id=document_id,
    )
    return get_document_genere(document_id)


def verifier_document_modifiable(document_id):
    document = get_document_genere(document_id)
    if document and document["statut"] == "Final":
        raise DocumentFinalError(_l_cycle_vie("document_final", document_id=document_id))
    return document


# --- Épinglage ----------------------------------------------------------
# Un pin est un simple pointeur (type + reference_id), jamais une copie du
# contenu épinglé -- désépingler (supprimer_epingle) ne touche jamais
# l'original, et supprimer l'original (voir delete_dossier ci-dessus)
# nettoie le(s) pin(s) qui le référençaient.

def epingler(type_element: str, reference_id: int, dossier_id: int | None, libelle: str) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO elements_epingles (type, reference_id, dossier_id, libelle, date_creation) VALUES (?, ?, ?, ?, ?)",
        (type_element, reference_id, dossier_id, libelle, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    pin_id = cur.lastrowid
    conn.close()
    return pin_id


def desepingler(pin_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM elements_epingles WHERE id = ?", (pin_id,))
    conn.commit()
    conn.close()


def lister_epingles() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM elements_epingles ORDER BY date_creation DESC").fetchall()
    conn.close()
    return rows


def deja_epingle(type_element: str, reference_id: int):
    """Retourne la ligne du pin existant pour cet élément, ou None -- pour
    que le front sache s'il faut afficher 📌 (épingler) ou 📍 (désépingler)
    sans avoir à charger toute la liste à chaque bouton."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM elements_epingles WHERE type = ? AND reference_id = ?", (type_element, reference_id)
    ).fetchone()
    conn.close()
    return row


# --- Générations (historique persistant de tout contenu généré) --------
#
# Distinct de `documents_generes` : ce dernier suit le statut ÉDITORIAL
# d'un document (Brouillon -> ... -> Final, avec verrouillage à Final --
# voir changer_statut_document), utilisé par le backend web. `generations`
# suit le statut TECHNIQUE du traitement IA lui-même (en_cours -> terminee
# | erreur), pour gui.py::PlaidIAApp._lancer_generation -- un journal
# append-only de tout ce qui a été généré, y compris les fonctionnalités
# qui n'écrivent dans aucune autre table (résumé, chronologie...). Jamais
# de suppression ni d'expiration automatique : supprimer_generation()
# n'est appelée que depuis un bouton « Supprimer » confirmé par
# l'utilisateur (voir gui.py::DialogueGenerations).

def creer_generation(dossier_id, type_generation: str, libelle: str) -> int:
    """Enregistre le lancement d'une génération, statut 'en_cours', avant
    même de savoir si elle réussira -- ainsi, même un arrêt brutal de l'app
    en cours de traitement laisse une trace en base plutôt qu'aucune (voir
    marquer_generations_en_cours_comme_interrompues, appelée au prochain
    démarrage)."""
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO generations (type, dossier_id, libelle, statut, date_creation) VALUES (?, ?, ?, 'en_cours', ?)",
        (type_generation, dossier_id, libelle, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    generation_id = cur.lastrowid
    conn.close()
    return generation_id


def terminer_generation(generation_id: int, contenu) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE generations SET statut = 'terminee', contenu_json = ?, date_fin = ? WHERE id = ?",
        (json.dumps(contenu, ensure_ascii=False), datetime.now().isoformat(timespec="seconds"), generation_id),
    )
    conn.commit()
    conn.close()


def echouer_generation(generation_id: int, erreur: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE generations SET statut = 'erreur', erreur = ?, date_fin = ? WHERE id = ?",
        (str(erreur), datetime.now().isoformat(timespec="seconds"), generation_id),
    )
    conn.commit()
    conn.close()


def _generation_depuis_row(row) -> dict:
    d = dict(row)
    d["contenu"] = json.loads(d["contenu_json"]) if d["contenu_json"] else None
    del d["contenu_json"]
    return d


def list_generations(dossier_id=None) -> list:
    """Historique complet, le plus récent d'abord. Sans filtre, renvoie
    TOUTES les générations (y compris celles sans dossier) -- c'est la
    source de l'écran « Générations » (voir gui.py::DialogueGenerations),
    qui doit rester consultable après redémarrage de l'app."""
    conn = get_connection()
    if dossier_id is not None:
        rows = conn.execute(
            "SELECT * FROM generations WHERE dossier_id = ? ORDER BY date_creation DESC", (dossier_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM generations ORDER BY date_creation DESC").fetchall()
    conn.close()
    return [_generation_depuis_row(r) for r in rows]


def get_generation(generation_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM generations WHERE id = ?", (generation_id,)).fetchone()
    conn.close()
    return _generation_depuis_row(row) if row else None


def supprimer_generation(generation_id: int) -> None:
    """Suppression DÉFINITIVE et IRRÉVERSIBLE d'une entrée d'historique --
    à n'appeler que depuis une action explicite de l'utilisateur (bouton
    « Supprimer » avec confirmation). Jamais appelée automatiquement :
    aucune expiration, aucune purge périodique, aucune limite de nombre
    conservé en base."""
    conn = get_connection()
    conn.execute("DELETE FROM generations WHERE id = ?", (generation_id,))
    conn.commit()
    conn.close()


def marquer_generations_en_cours_comme_interrompues() -> None:
    """Appelée une seule fois, au démarrage de l'app (voir gui.py::main).
    Une génération encore à statut='en_cours' en base ne peut être que le
    reliquat d'un arrêt brutal (fermeture, crash) lors d'un lancement
    précédent : aucun thread ne peut légitimement y travailler encore
    puisque le processus vient de démarrer. La marquer 'erreur' reflète la
    réalité sans rien supprimer ni écraser -- contenu_json était déjà NULL
    pour une génération jamais allée à son terme."""
    conn = get_connection()
    conn.execute(
        "UPDATE generations SET statut = 'erreur', erreur = 'Application fermée pendant le traitement.', date_fin = ? "
        "WHERE statut = 'en_cours'",
        (datetime.now().isoformat(timespec="seconds"),),
    )
    conn.commit()
    conn.close()


# --- Veille (jurisprudence ET lois) -------------------------------------
#
# Table de dédup PARTAGÉE entre les deux veilles (voir gui.py::
# _lancer_verification_veille pour la jurisprudence, ::
# _lancer_verification_veille_lois pour les lois -- deux threads
# indépendants, même mécanique de "déjà vu"). Remplace get_references_vues/
# marquer_references_vues qu'appelait déjà _lancer_verification_veille sans
# qu'elles n'aient jamais été définies (AttributeError silencieux dans le
# thread dès qu'un dossier obtenait un résultat Judilibre -- jamais remarqué
# faute de clé Judilibre configurée en dev, qui fait échouer l'appel avant
# d'atteindre ce point).

def get_references_vues(dossier_id: int, type_: str = "jurisprudence") -> set:
    conn = get_connection()
    rows = conn.execute(
        "SELECT reference FROM elements_veille_vus WHERE dossier_id = ? AND type = ?", (dossier_id, type_)
    ).fetchall()
    conn.close()
    return {r["reference"] for r in rows}


def marquer_references_vues(dossier_id: int, references, type_: str = "jurisprudence") -> None:
    conn = get_connection()
    horodatage = datetime.now().isoformat(timespec="seconds")
    for reference in references:
        conn.execute(
            "INSERT INTO elements_veille_vus (dossier_id, type, reference, date_vue) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(dossier_id, type, reference) DO NOTHING",
            (dossier_id, type_, reference, horodatage),
        )
    conn.commit()
    conn.close()


# --- Veille des lois : articles cités par dossier -----------------------
#
# Recalculé à chaque passage de veille (voir gui.py::
# _lancer_verification_veille_lois) à partir des balises [ART:<numéro>:<code>]
# déjà présentes dans le contenu généré (analyses, generations, notes) et
# les faits bruts du dossier -- aucune extraction dédiée n'existait avant
# ce chantier, ces balises ne servaient jusqu'ici qu'à l'affichage
# (gui.py::_afficher). Seuls les 6 codes de REGLE_BALISAGE_CITATIONS
# (analyse.py) sont balisés -- l'OHADA n'a pas de format de balise et n'est
# donc pas couvert par ce lien (voir la section OHADA plus bas).

def remplacer_articles_cites_dossier(dossier_id: int, articles) -> None:
    """Remplace entièrement la liste des articles liés à ce dossier par
    `articles` (itérable de (code, numero)) -- reflète l'état du contenu
    généré à l'instant de l'extraction, pas un ajout cumulatif (un article
    retiré d'une nouvelle version d'une analyse ne doit pas rester lié
    indéfiniment)."""
    conn = get_connection()
    horodatage = datetime.now().isoformat(timespec="seconds")
    conn.execute("DELETE FROM articles_cites_dossier WHERE dossier_id = ?", (dossier_id,))
    for code, numero in articles:
        conn.execute(
            "INSERT INTO articles_cites_dossier (dossier_id, code, numero, derniere_extraction) VALUES (?, ?, ?, ?)",
            (dossier_id, code, numero, horodatage),
        )
    conn.commit()
    conn.close()


def get_articles_cites_dossier(dossier_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT code, numero FROM articles_cites_dossier WHERE dossier_id = ?", (dossier_id,)
    ).fetchall()
    conn.close()
    return [(r["code"], r["numero"]) for r in rows]


def lister_dossiers_citant_article(code: str, numero: str) -> list:
    """Dossiers (id, nom) citant cet article -- pour savoir qui prévenir
    quand une modification est détectée."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT d.id, d.nom FROM articles_cites_dossier a "
        "JOIN dossiers d ON d.id = a.dossier_id WHERE a.code = ? AND a.numero = ?",
        (code, numero),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def tous_articles_cites() -> list:
    """Ensemble des (code, numero) distincts actuellement liés à au moins
    un dossier -- c'est la liste à vérifier auprès de Légifrance à chaque
    passage de veille."""
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT code, numero FROM articles_cites_dossier").fetchall()
    conn.close()
    return [(r["code"], r["numero"]) for r in rows]


# --- Veille des lois : cache de dernier état connu par article ----------

def get_article_surveille(code: str, numero: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM articles_surveilles WHERE code = ? AND numero = ?", (code, numero)).fetchone()
    conn.close()
    return dict(row) if row else None


def upsert_article_surveille(code: str, numero: str, id_version, etat) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO articles_surveilles (code, numero, dernier_id_version, dernier_etat, derniere_verification) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(code, numero) DO UPDATE SET dernier_id_version = excluded.dernier_id_version, "
        "dernier_etat = excluded.dernier_etat, derniere_verification = excluded.derniere_verification",
        (code, numero, id_version, etat, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


# --- Veille des lois : alertes persistantes sur la fiche dossier --------
#
# Ne sont JAMAIS résolues automatiquement -- seul acquitter_alerte_article,
# appelé depuis un bouton explicite de gui.py, change leur statut. Aucune
# alerte ne modifie quoi que ce soit d'autre (analyse, plan, dossier) :
# c'est strictement une information affichée, jamais une action.

def creer_alerte_article(dossier_id: int, code: str, numero: str, ancien_etat, nouvel_etat, date_modification, lien_source) -> None:
    conn = get_connection()
    deja_active = conn.execute(
        "SELECT id FROM alertes_articles_dossier WHERE dossier_id = ? AND code = ? AND numero = ? AND statut = 'active'",
        (dossier_id, code, numero),
    ).fetchone()
    if deja_active is None:  # jamais deux alertes actives identiques pour le même dossier/article
        conn.execute(
            "INSERT INTO alertes_articles_dossier "
            "(dossier_id, code, numero, ancien_etat, nouvel_etat, date_modification, lien_source, date_detection, statut) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')",
            (dossier_id, code, numero, ancien_etat, nouvel_etat, date_modification, lien_source, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
    conn.close()


def get_alertes_actives_dossier(dossier_id: int | None = None) -> list:
    """Sans dossier_id, renvoie TOUTES les alertes actives (utilisé par le
    badge global du backend web, voir backend/app/routers/veille.py) --
    gui.py continue d'appeler cette fonction avec un dossier_id précis,
    comportement inchangé."""
    conn = get_connection()
    if dossier_id is not None:
        rows = conn.execute(
            "SELECT * FROM alertes_articles_dossier WHERE dossier_id = ? AND statut = 'active' ORDER BY date_detection DESC",
            (dossier_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM alertes_articles_dossier WHERE statut = 'active' ORDER BY date_detection DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def acquitter_alerte_article(alerte_id: int) -> None:
    """Marque une alerte comme vue/traitée -- jamais une suppression : la
    ligne reste en base, seul son statut change, pour garder une trace de
    ce qui a été signalé et acquitté."""
    conn = get_connection()
    conn.execute("UPDATE alertes_articles_dossier SET statut = 'acquittee' WHERE id = ?", (alerte_id,))
    conn.commit()
    conn.close()


# --- Alertes de veille jurisprudence (backend web uniquement) -----------
# Voir le commentaire sur CREATE TABLE alertes_jurisprudence_dossier plus
# haut : pendant persistant de alertes_articles_dossier, pour le backend
# web seulement -- gui.py garde son propre badge éphémère en mémoire.

def creer_alerte_jurisprudence(dossier_id: int, reference: str, resume: str, source: str) -> None:
    conn = get_connection()
    deja_active = conn.execute(
        "SELECT id FROM alertes_jurisprudence_dossier WHERE dossier_id = ? AND reference = ? AND statut = 'active'",
        (dossier_id, reference),
    ).fetchone()
    if deja_active is None:
        conn.execute(
            "INSERT INTO alertes_jurisprudence_dossier (dossier_id, reference, resume, source, date_detection, statut) "
            "VALUES (?, ?, ?, ?, ?, 'active')",
            (dossier_id, reference, resume, source, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
    conn.close()


def get_alertes_jurisprudence_actives(dossier_id: int | None = None) -> list:
    conn = get_connection()
    if dossier_id is not None:
        rows = conn.execute(
            "SELECT * FROM alertes_jurisprudence_dossier WHERE dossier_id = ? AND statut = 'active' ORDER BY date_detection DESC",
            (dossier_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM alertes_jurisprudence_dossier WHERE statut = 'active' ORDER BY date_detection DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def acquitter_alerte_jurisprudence(alerte_id: int) -> None:
    conn = get_connection()
    conn.execute("UPDATE alertes_jurisprudence_dossier SET statut = 'acquittee' WHERE id = ?", (alerte_id,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
