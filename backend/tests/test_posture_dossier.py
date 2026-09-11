"""Tests de posture, objectif et structure stratégique des générations."""

import sqlite3

import analyse as legacy_analyse
import app.quality_pipeline as quality_pipeline
import db
from app.deps import construire_contexte_dossier, structurer_sortie_strategique
from fastapi.testclient import TestClient


def test_migration_posture_conserve_une_base_ancienne(tmp_path, monkeypatch):
    database_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(database_path)
    conn.execute("CREATE TABLE dossiers (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT NOT NULL, date_creation TEXT NOT NULL)")
    conn.execute("INSERT INTO dossiers (nom, date_creation) VALUES ('Ancien dossier', '2026-01-01')")
    conn.commit()
    conn.close()

    monkeypatch.setattr(db, "DB_PATH", database_path)
    db.init_db()
    dossier = dict(db.get_dossier(1))

    assert dossier["partie_representee"] is None
    assert dossier["stade_procedure"] is None
    assert dossier["objectif"] is None


def test_posture_et_objectif_sont_injectes_dans_le_contexte(client: TestClient):
    dossier = client.post(
        "/api/dossiers/",
        json={
            "nom": "Dossier posture",
            "domaine": "Pénal",
            "partie_representee": "Mis en examen",
            "stade_procedure": "Première instance",
            "objectif": "Obtenir la relaxe",
        },
    ).json()
    contexte = construire_contexte_dossier(dossier)

    assert "Partie représentée : Mis en examen" in contexte
    assert "Stade de la procédure : Première instance" in contexte
    assert "Objectif du client : Obtenir la relaxe" in contexte


def test_sortie_separe_diagnostic_et_strategie():
    dossier = {
        "id": 1,
        "nom": "Dossier",
        "faits": "Un fait défavorable",
        "parties": "A contre B",
        "partie_representee": "Défendeur",
        "objectif": "Rejeter la demande",
    }
    sortie = structurer_sortie_strategique({"arguments": [{"risque": "Élevé", "resume": "Moyen adverse"}]}, dossier, "plan")
    neutre = structurer_sortie_strategique({"arguments": []}, {**dossier, "partie_representee": ""}, "plan")

    assert "Diagnostic" in sortie["diagnostic"]
    assert "Défendeur" in sortie["strategie"]
    assert "Objectif déclaré" in sortie["strategie"]
    assert "Aucune partie n'est renseignée" in neutre["strategie"]


# --- Complément posture/stratégie : couche stratégique combative et exhaustive ---


def _dossier_avec_posture(objectif: str = "Rejeter la demande") -> dict:
    return {
        "id": 1,
        "nom": "Dossier",
        "faits": "Un fait défavorable",
        "parties": "A contre B",
        "partie_representee": "Défendeur",
        "objectif": objectif,
    }


def _strategie_combative_type() -> dict:
    return {
        "moyens": [
            {
                "axe": "Procédure",
                "moyen": "Prescription de l'action",
                "developpement": "L'action est prescrite depuis le 1er janvier.",
                "probabilite_succes": "Forte",
                "cout_risque": "Faible -- moyen de pur droit, aucune réaction hostile attendue.",
            },
            {
                "axe": "Preuve",
                "moyen": "Irrecevabilité de la pièce 4 (copie non certifiée)",
                "developpement": "La pièce 4 n'est produite qu'en copie, sans force probante suffisante.",
                "probabilite_succes": "Moyenne",
                "cout_risque": "Moyen -- suppose de convaincre le juge sur un point technique.",
            },
            {
                "axe": "Fond",
                "moyen": "Absence de préjudice démontré",
                "developpement": "Aucune pièce n'établit la réalité du préjudice allégué.",
                "probabilite_succes": "Moyenne",
                "cout_risque": "Faible.",
            },
            {
                "axe": "Quantum",
                "moyen": "Contestation du montant du préjudice moral",
                "developpement": "Le montant demandé est disproportionné au regard des précédents comparables.",
                "probabilite_succes": "Faible",
                "cout_risque": "Faible -- moyen subsidiaire habituel.",
            },
            {
                "axe": "Fond",
                "moyen": "Exception d'inconstitutionnalité du texte invoqué",
                "developpement": "Un moyen très rarement retenu en pratique, à ne soulever qu'en dernier recours.",
                "probabilite_succes": "Improbable",
                "cout_risque": "Élevé -- risque de décrédibiliser le reste de la plaidoirie.",
            },
        ],
        "reponses_arguments_adverses": [
            {"argument_adverse": "Moyen adverse", "reponse": "Ce moyen se heurte à la prescription soulevée ci-dessus."}
        ],
    }


def test_strategie_combative_balaye_les_quatre_axes():
    dossier = _dossier_avec_posture()
    sortie = structurer_sortie_strategique({"arguments": []}, dossier, "conclusions", strategie_combative=_strategie_combative_type())

    for axe in ("Procédure", "Preuve", "Fond", "Quantum"):
        assert axe in sortie["strategie"]
    assert "Prescription de l'action" in sortie["strategie"]
    assert "probabilité de succès : Forte" in sortie["strategie"]
    assert "coût/risque" in sortie["strategie"]


def test_strategie_combative_ne_supprime_jamais_un_moyen_improbable():
    dossier = _dossier_avec_posture()
    sortie = structurer_sortie_strategique({"arguments": []}, dossier, "conclusions", strategie_combative=_strategie_combative_type())

    assert "Moyens improbables" in sortie["strategie"]
    assert "Exception d'inconstitutionnalité du texte invoqué" in sortie["strategie"]


def test_strategie_combative_repond_a_chaque_argument_adverse():
    dossier = _dossier_avec_posture()
    sortie = structurer_sortie_strategique({"arguments": []}, dossier, "conclusions", strategie_combative=_strategie_combative_type())

    assert "Réponses aux arguments adverses" in sortie["strategie"]
    assert "Moyen adverse" in sortie["strategie"]
    assert "Ce moyen se heurte à la prescription" in sortie["strategie"]


def test_strategie_combative_absente_ou_vide_retombe_sur_le_texte_generique():
    dossier = _dossier_avec_posture()
    sans_combative = structurer_sortie_strategique({"arguments": []}, dossier, "conclusions", strategie_combative=None)
    combative_vide = structurer_sortie_strategique(
        {"arguments": []}, dossier, "conclusions", strategie_combative={"moyens": [], "reponses_arguments_adverses": []}
    )

    for sortie in (sans_combative, combative_vide):
        assert "Moyens à soulever en priorité" in sortie["strategie"]
        assert "Procédure" not in sortie["strategie"]


class _FakeContenu:
    def __init__(self, text: str):
        self.text = text


class _FakeResponse:
    def __init__(self, text: str):
        self.content = [_FakeContenu(text)]


class _FakeClient:
    def __init__(self, text: str):
        self.messages = self
        self._text = text

    def create(self, **kwargs):
        return _FakeResponse(self._text)


def test_generer_strategie_combative_couvre_le_dossier_transmis(monkeypatch):
    """Vérifie la construction du message envoyé au modèle -- le jugement
    réel de l'agent (comme pour les autres agents LLM du fichier) a été
    vérifié manuellement avec une clé API réelle pendant le développement."""
    capture = {}

    class _ClientEspion(_FakeClient):
        def create(self, **kwargs):
            capture["system"] = kwargs["system"]
            capture["message"] = kwargs["messages"][0]["content"]
            return super().create(**kwargs)

    monkeypatch.setattr(legacy_analyse, "_client", lambda: _ClientEspion("{}"))
    resultat = legacy_analyse.generer_strategie_combative(
        "Faits du dossier.",
        "Défendeur",
        "Obtenir la relaxe",
        [{"resume": "Moyen adverse principal"}],
    )

    assert resultat == {"moyens": [], "reponses_arguments_adverses": []}
    assert "Défendeur" in capture["message"]
    assert "Obtenir la relaxe" in capture["message"]
    assert "Moyen adverse principal" in capture["message"]
    assert "altérer, cacher ou fabriquer" in capture["system"]


def test_executer_strategie_combative_degrade_proprement_en_cas_d_echec():
    """Même idiome de protection que le trio qualité (_appel_protege) : un
    agent en échec ne casse jamais l'appelant, il retombe sur une valeur
    neutre plutôt que de laisser remonter l'exception."""

    def _en_echec():
        raise RuntimeError("panne réseau simulée")

    resultat = quality_pipeline.executer_strategie_combative(_en_echec)
    assert resultat == {"moyens": [], "reponses_arguments_adverses": []}
