"""
test_quality_pipeline.py — Tests de l'orchestrateur et des agents de QUALITÉ
(app.quality_pipeline), voir ARCHITECTURE_MULTI_AGENTS.md §4-6, §9.

Portée : la mécanique déterministe (contrôle des citations, autorité du code
sur le LLM, dégradation propre) est testée directement, sans réseau. Le
jugement réel des agents LLM (verifier_juridiquement, critiquer_reponse,
valider_finalement) est mocké -- leur comportement réel a été vérifié
manuellement avec une clé API réelle pendant le développement, comme pour
traiter_message_edition (voir test_chat_contextuel.py)."""

import time

import analyse as legacy_analyse
import app.quality_pipeline as quality_pipeline
import pytest
from app.security_guard import DemandeRefusee


# --- Contrôle déterministe des citations -----------------------------------

def test_extraire_citations_detecte_article_et_jurisprudence():
    texte = "Selon l'article L. 1232-1 du Code du travail, confirmé par Cass. soc., 12 mars 2020, n° 18-12.345, ..."
    citations = quality_pipeline._extraire_citations(texte)
    assert any("1232-1" in c for c in citations)
    assert any(c.startswith("n°") for c in citations)


def test_verifier_citations_marque_verifie_si_presente_dans_les_sources():
    texte = "Voir l'article L. 1232-1 du Code du travail."
    resultats = quality_pipeline._verifier_citations(texte, ["Extrait : ... article L. 1232-1 dispose que ..."])
    assert resultats
    assert all(r["statut_deterministe"] == "VERIFIE" for r in resultats)


def test_verifier_citations_marque_non_verifie_si_absente_des_sources():
    texte = "Voir l'article L. 9999-9 du Code du travail, qui n'existe dans aucune source fournie."
    resultats = quality_pipeline._verifier_citations(texte, ["Ce texte source ne mentionne aucun article de ce type."])
    assert resultats
    assert all(r["statut_deterministe"] == "NON_VERIFIE" for r in resultats)


def test_verifier_citations_sans_aucune_source_disponible():
    texte = "Voir l'article L. 1232-1 du Code du travail."
    resultats = quality_pipeline._verifier_citations(texte, [])
    assert all(r["statut_deterministe"] == "AUCUNE_SOURCE" for r in resultats)


def test_citation_deja_signalee_a_verifier_par_le_modele_nest_pas_recontrolee():
    """Une citation que le modèle a lui-même honnêtement préfixée
    « À VÉRIFIER » ne doit pas ressortir comme une citation dissimulée --
    elle est ignorée par le contrôle déterministe, pas signalée en plus.
    Filet hérité (texte antérieur au chantier de balisage) : voir
    test_balise_verif_nest_jamais_recontrolee pour l'équivalent balisé."""
    texte = "À VÉRIFIER : article L. 9999-9 du Code du travail."
    resultats = quality_pipeline._verifier_citations(texte, [])
    assert resultats == []


# --- Balisage des références juridiques ([ART:...]/[JURISPRUDENCE:...]/[VERIF:...]) --
# Remplace le marqueur libre "À VÉRIFIER : " -- voir analyse.REGLE_BALISAGE_CITATIONS.

def test_extraire_citations_balisees_detecte_art_et_jurisprudence():
    texte = "Le principe [ART:132-24:CP] impose ... [JURISPRUDENCE:Cass. Crim., 12 mars 2023, n°22-84.123] le confirme."
    citations = quality_pipeline._extraire_citations_balisees(texte)
    assert {"type": "ART", "brut": "[ART:132-24:CP]", "cle_recherche": "132-24"} in citations
    assert any(c["type"] == "JURISPRUDENCE" and c["cle_recherche"].startswith("Cass. Crim.") for c in citations)


def test_extraire_verif_recupere_les_descriptions():
    texte = "Un point [VERIF:absence de rapport d'enquête de personnalité au dossier] reste à confirmer."
    assert quality_pipeline._extraire_verif(texte) == ["absence de rapport d'enquête de personnalité au dossier"]


def test_verifier_citations_balisee_marque_verifie_si_presente_dans_les_sources():
    texte = "Le principe d'individualisation de la peine [ART:132-24:CP] impose ..."
    resultats = quality_pipeline._verifier_citations(texte, ["Le Code pénal prévoit à son article 132-24 que ..."])
    assert resultats == [{"citation": "[ART:132-24:CP]", "statut_deterministe": "VERIFIE"}]


def test_verifier_citations_balisee_marque_non_verifie_si_absente_des_sources():
    texte = "Voir [ART:9999-9:CCIV], qui n'existe dans aucune source fournie."
    resultats = quality_pipeline._verifier_citations(texte, ["Ce texte source ne mentionne aucun article de ce type."])
    assert resultats == [{"citation": "[ART:9999-9:CCIV]", "statut_deterministe": "NON_VERIFIE"}]


def test_verifier_citations_jurisprudence_balisee_sans_aucune_source_disponible():
    texte = "Voir [JURISPRUDENCE:Cass. Crim., 12 mars 2023, n°22-84.123]."
    resultats = quality_pipeline._verifier_citations(texte, [])
    assert resultats == [{"citation": "[JURISPRUDENCE:Cass. Crim., 12 mars 2023, n°22-84.123]", "statut_deterministe": "AUCUNE_SOURCE"}]


def test_balise_verif_nest_jamais_recontrolee():
    """Équivalent balisé de test_citation_deja_signalee_a_verifier_par_le_modele_nest_pas_recontrolee
    -- [VERIF:...] est un aveu explicite d'incertitude, jamais une citation
    à confronter aux sources."""
    texte = "Un point [VERIF:article L. 9999-9 du Code du travail, référence à confirmer] reste incertain."
    resultats = quality_pipeline._verifier_citations(texte, [])
    assert resultats == []


def test_citation_balisee_et_heritee_ne_sont_pas_comptees_deux_fois():
    """Le contenu d'une balise [JURISPRUDENCE:...] ressemble aussi au regex
    hérité (Cass. Crim....) -- il ne doit être compté qu'une fois, via le
    chemin balisé, pas une seconde fois via le filet hérité."""
    texte = "Voir [JURISPRUDENCE:Cass. Crim., 12 mars 2023, n°22-84.123]."
    resultats = quality_pipeline._verifier_citations(texte, [])
    assert len(resultats) == 1


def test_filet_heritage_detecte_toujours_une_citation_non_balisee():
    """Une citation qui n'a pas été balisée (texte antérieur au chantier de
    balisage, ou oubli du modèle) reste détectée par le filet hérité."""
    texte = "Selon l'article L. 1232-1 du Code du travail (non balisé), ..."
    resultats = quality_pipeline._verifier_citations(texte, ["... article L. 1232-1 dispose que ..."])
    assert any("1232-1" in r["citation"] for r in resultats)
    assert all(r["statut_deterministe"] == "VERIFIE" for r in resultats)


# --- Autorité du code sur la couche LLM du vérificateur ---------------------

def test_le_code_corrige_une_citation_que_le_llm_declare_a_tort_verifiee():
    """Garantit EN CODE (pas seulement par instruction de prompt) que le
    contrôle déterministe fait autorité : même si la couche LLM du
    vérificateur "hallucine sa propre confirmation", le statut final ne
    peut jamais dépasser NON_VERIFIE pour une citation absente des sources."""
    citations = [{"citation": "article L. 9999-9", "statut_deterministe": "NON_VERIFIE"}]
    elements_llm_menteur = [{"affirmation": "article L. 9999-9", "statut": "VERIFIE", "commentaire": "Semble correct."}]
    corriges = quality_pipeline._appliquer_autorite_deterministe(elements_llm_menteur, citations)
    assert len(corriges) == 1
    assert corriges[0]["statut"] == "NON_VERIFIE"


def test_citation_non_verifiee_omise_par_le_llm_est_ajoutee_quand_meme():
    citations = [{"citation": "article L. 9999-9", "statut_deterministe": "NON_VERIFIE"}]
    corriges = quality_pipeline._appliquer_autorite_deterministe([], citations)
    assert len(corriges) == 1
    assert corriges[0]["statut"] == "NON_VERIFIE"


def test_statut_global_ne_peut_pas_rester_verifie_si_un_element_est_non_verifie():
    elements = [{"affirmation": "x", "statut": "NON_VERIFIE", "commentaire": ""}]
    assert quality_pipeline._recalculer_statut_global("VERIFIE", elements) == "NON_VERIFIE"
    assert quality_pipeline._recalculer_statut_global("VERIFIE", []) == "VERIFIE"


# --- Orchestrateur : pipeline complet ---------------------------------------

def _mocker_agents_qualite(monkeypatch, *, verif=None, critique=None, final=None):
    monkeypatch.setattr(legacy_analyse, "evaluer_garde_fou_entree", lambda texte: {"allowed": True, "risk_level": "low", "reason": "", "requires_clarification": False})
    monkeypatch.setattr(legacy_analyse, "verifier_juridiquement", verif or (lambda *a, **k: {"statut_global": "A_VERIFIER", "elements": []}))
    monkeypatch.setattr(legacy_analyse, "critiquer_reponse", critique or (lambda *a, **k: {"critiques": [], "synthese": ""}))
    monkeypatch.setattr(legacy_analyse, "valider_finalement", final or (lambda verif, crit: {"statut_global": "A_VERIFIER", "points_a_verifier": [], "points_forts": [], "synthese_utilisateur": "Synthèse."}))


def test_pipeline_complet_execute_agent_principal_et_renvoie_verification(monkeypatch):
    _mocker_agents_qualite(monkeypatch)
    resultat = quality_pipeline.executer_pipeline_complet(
        feature="conclusions",
        texte_a_screener="texte quelconque",
        fonction_principale=lambda: {"arguments": [], "points_attention": []},
        sources_textes=["texte quelconque"],
    )
    assert resultat.resultat_principal == {"arguments": [], "points_attention": []}
    assert resultat.verification is not None
    # La validation finale est désormais une fusion déterministe en code
    # (chantier "temps de traitement", §2b) -- valider_finalement (le
    # modèle) n'est PAS appelé ici puisque les verdicts par défaut ne se
    # contredisent pas (voir les tests dédiés ci-dessous pour les deux cas).
    assert resultat.verification["statut_global"] == "A_VERIFIER"
    agents_executes = [e.agent for e in resultat.trace]
    assert agents_executes == ["garde_fou_entree", "agent_principal", "legal_verifier", "critic_agent", "final_validator"]


def test_pipeline_complet_refuse_par_le_garde_fou_najamais_lagent_principal(monkeypatch):
    appels_agent_principal = []
    monkeypatch.setattr(
        legacy_analyse,
        "evaluer_garde_fou_entree",
        lambda texte: {"allowed": False, "risk_level": "high", "reason": "Refusé.", "requires_clarification": False},
    )
    with pytest.raises(DemandeRefusee):
        quality_pipeline.executer_pipeline_complet(
            feature="conclusions",
            texte_a_screener="texte suspect",
            fonction_principale=lambda: appels_agent_principal.append(1) or {},
        )
    assert appels_agent_principal == []


def test_pipeline_complet_degrade_proprement_si_un_agent_qualite_echoue(monkeypatch):
    """Un agent qualité en échec ne doit jamais faire échouer la requête ni
    perdre le résultat de l'agent principal -- voir §9/§14."""

    def _verifier_en_echec(*a, **k):
        raise RuntimeError("panne simulée de l'API")

    _mocker_agents_qualite(monkeypatch, verif=_verifier_en_echec)
    resultat = quality_pipeline.executer_pipeline_complet(
        feature="conclusions",
        texte_a_screener="texte",
        fonction_principale=lambda: {"arguments": ["ok"]},
        sources_textes=["texte"],
    )
    assert resultat.resultat_principal == {"arguments": ["ok"]}
    assert resultat.verification is not None  # dégradé, jamais absent silencieusement
    trace_verif = next(e for e in resultat.trace if e.agent == "legal_verifier")
    assert trace_verif.statut == "degrade"


def test_pipeline_complet_degrade_proprement_sur_timeout(monkeypatch):
    monkeypatch.setattr(quality_pipeline, "_TIMEOUT_AGENT_QUALITE", 0.05)

    def _critique_lente(*a, **k):
        time.sleep(0.3)
        return {"critiques": [], "synthese": "trop tard"}

    _mocker_agents_qualite(monkeypatch, critique=_critique_lente)
    resultat = quality_pipeline.executer_pipeline_complet(
        feature="conclusions",
        texte_a_screener="texte",
        fonction_principale=lambda: {"arguments": []},
        sources_textes=["texte"],
    )
    assert resultat.resultat_principal == {"arguments": []}
    trace_critique = next(e for e in resultat.trace if e.agent == "critic_agent")
    assert trace_critique.statut == "degrade"


# --- Pipeline conversationnel (profondeur dynamique, §9/§10) ---------------

def test_trio_qualite_non_execute_si_intention_ne_le_demande_pas(monkeypatch):
    appels = []
    monkeypatch.setattr(legacy_analyse, "verifier_juridiquement", lambda *a, **k: appels.append(1) or {})
    resultat = quality_pipeline.executer_trio_qualite_si_necessaire(
        "réponse quelconque", {"necessite_verification_approfondie": False}
    )
    assert resultat is None
    assert appels == []


def test_trio_qualite_execute_si_intention_le_demande(monkeypatch):
    _mocker_agents_qualite(monkeypatch)
    resultat = quality_pipeline.executer_trio_qualite_si_necessaire(
        "réponse quelconque avec une affirmation juridique", {"necessite_verification_approfondie": True}
    )
    assert resultat is not None
    assert "statut_global" in resultat


# --- Parallélisation et validation finale déterministe (chantier "temps de traitement", §2b) ---

def test_appels_proteges_en_parallele_degrade_independamment():
    def _ok():
        return {"v": 1}

    def _echoue():
        raise RuntimeError("panne simulée")

    resultats = quality_pipeline._appels_proteges_en_parallele([(_ok, {"repli": True}), (_echoue, {"repli": True})])
    assert resultats[0] == {"v": 1}
    assert resultats[1] == {"repli": True}


def test_verificateur_et_critique_sexecutent_en_parallele(monkeypatch):
    """Preuve mesurable de la parallélisation : deux agents qui dorment
    chacun 0.2s doivent se terminer en bien moins que 0.4s au total --
    l'attente devient le max des deux durées, jamais leur somme."""

    def _lent(valeur):
        def _appel(*a, **k):
            time.sleep(0.2)
            return valeur
        return _appel

    _mocker_agents_qualite(
        monkeypatch,
        verif=_lent({"statut_global": "A_VERIFIER", "elements": []}),
        critique=_lent({"critiques": [], "synthese": ""}),
    )
    t0 = time.monotonic()
    resultat = quality_pipeline.executer_pipeline_complet(
        feature="conclusions", texte_a_screener="texte", fonction_principale=lambda: {"arguments": []}, sources_textes=["texte"],
    )
    duree = time.monotonic() - t0
    assert duree < 0.35
    assert resultat.verification is not None


def test_validation_finale_deterministe_sans_appel_modele_si_verdicts_coherents(monkeypatch):
    appels_modele = []
    _mocker_agents_qualite(
        monkeypatch,
        verif=lambda *a, **k: {"statut_global": "VERIFIE", "elements": []},
        critique=lambda *a, **k: {"critiques": [], "synthese": ""},
        final=lambda *a, **k: appels_modele.append(1) or {},
    )
    resultat = quality_pipeline.executer_pipeline_complet(
        feature="conclusions", texte_a_screener="texte", fonction_principale=lambda: {"arguments": []}, sources_textes=["texte"],
    )
    assert appels_modele == []
    assert resultat.verification["statut_global"] == "VERIFIE"


def test_validation_finale_appelle_le_modele_si_verdicts_se_contredisent(monkeypatch):
    """Seul cas où le modèle est encore appelé pour la validation finale :
    le vérificateur juge les citations fiables (VERIFIE) alors que le
    critique a relevé une faiblesse de gravité Élevée -- désaccord réel que
    la fusion déterministe ne peut pas trancher seule."""
    appels_modele = []

    def _valider_finalement_espion(verif, crit):
        appels_modele.append(1)
        return {"statut_global": "INCERTAIN", "points_a_verifier": [], "points_forts": [], "synthese_utilisateur": "Tranché par le modèle."}

    _mocker_agents_qualite(
        monkeypatch,
        verif=lambda *a, **k: {"statut_global": "VERIFIE", "elements": []},
        critique=lambda *a, **k: {"critiques": [{"cible": "x", "type": "contradiction_interne", "commentaire": "y", "gravite": "Élevée"}], "synthese": "z"},
        final=_valider_finalement_espion,
    )
    resultat = quality_pipeline.executer_pipeline_complet(
        feature="conclusions", texte_a_screener="texte", fonction_principale=lambda: {"arguments": []}, sources_textes=["texte"],
    )
    assert appels_modele == [1]
    assert resultat.verification["synthese_utilisateur"] == "Tranché par le modèle."


def test_garde_fou_precalcule_evite_un_second_appel(monkeypatch):
    _mocker_agents_qualite(monkeypatch)
    appels = []
    monkeypatch.setattr(
        legacy_analyse,
        "evaluer_garde_fou_entree",
        lambda texte: appels.append(1) or {"allowed": True, "risk_level": "low", "reason": "", "requires_clarification": False},
    )
    quality_pipeline.executer_pipeline_complet(
        feature="conclusions",
        texte_a_screener="texte",
        fonction_principale=lambda: {"arguments": []},
        garde_fou_precalcule={"allowed": True, "risk_level": "low", "reason": "déjà fait", "requires_clarification": False},
    )
    assert appels == []


def test_executer_trio_qualite_public_sans_garde_fou_ni_agent_principal(monkeypatch):
    """executer_trio_qualite() (public) -- utilisé par les endpoints en
    streaming -- n'appelle ni le garde-fou ni un agent principal, seulement
    le trio qualité."""
    appels_garde_fou = []
    monkeypatch.setattr(legacy_analyse, "evaluer_garde_fou_entree", lambda texte: appels_garde_fou.append(1) or {})
    _mocker_agents_qualite(monkeypatch)
    verification, trace = quality_pipeline.executer_trio_qualite("texte à vérifier", ["texte à vérifier"])
    assert appels_garde_fou == []
    assert verification is not None
    assert [e.agent for e in trace] == ["legal_verifier", "critic_agent", "final_validator"]
