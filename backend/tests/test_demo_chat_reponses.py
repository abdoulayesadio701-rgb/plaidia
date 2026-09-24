"""
test_demo_chat_reponses.py — Choix de la réponse préenregistrée du chat en
mode démo (app.demo_data.reponse_demo_pour_question), par mots-clés.
"""

import analyse
import pytest
from app import demo_data


@pytest.fixture(autouse=True)
def _langue_par_defaut():
    jeton = analyse.definir_langue_requete("fr")
    yield
    analyse._langue_requete.reset(jeton)


@pytest.mark.parametrize(
    "question, attendue",
    [
        ("Que dit l'article 1240 du Code civil ?", demo_data.REPONSE_CHAT_RESPONSABILITE_FR),
        ("Explique-moi la responsabilité délictuelle", demo_data.REPONSE_CHAT_RESPONSABILITE_FR),
        ("Rédige une analyse très détaillée (au moins 900 mots) de l'article 1240 du Code civil.", demo_data.REPONSE_CHAT_RESPONSABILITE_FR),
        ("Comment structurer une plaidoirie de 10 minutes ?", demo_data.REPONSE_CHAT_PLAIDOIRIE_FR),
        # Ambigu : demande de structure sur un sujet de responsabilité -> plaidoirie d'abord.
        ("Fais-moi un plan de plaidoirie sur la responsabilité civile", demo_data.REPONSE_CHAT_PLAIDOIRIE_FR),
        # Les deux réponses existantes gardent la priorité.
        ("Le licenciement pour faute grave est-il justifié ?", demo_data.REPONSE_CHAT_FAUTE_GRAVE_FR),
        ("Quel est le délai de prescription ?", demo_data.REPONSE_CHAT_DELAI_FR),
        # Simple salutation -> accueil court ; un mot-clé juridique garde la priorité.
        ("Bonjour", demo_data.REPONSE_CHAT_ACCUEIL_FR),
        ("Salut !", demo_data.REPONSE_CHAT_ACCUEIL_FR),
        ("Bonjour, quel est le délai de prescription ?", demo_data.REPONSE_CHAT_DELAI_FR),
        # Aucun mot-clé et pas une salutation -> réponse par défaut.
        ("Parle-moi de quelque chose sans rapport", demo_data.REPONSE_CHAT_DEFAUT_FR),
        # Salutation noyée dans un long message : pas un simple bonjour.
        ("Bonjour, je voudrais que tu me racontes une longue histoire sans aucun rapport", demo_data.REPONSE_CHAT_DEFAUT_FR),
    ],
)
def test_choix_de_la_reponse_en_francais(question, attendue):
    assert demo_data.reponse_demo_pour_question(question) == attendue


@pytest.mark.parametrize(
    "question, attendue",
    [
        ("What does article 1240 say?", demo_data.REPONSE_CHAT_RESPONSABILITE_EN),
        ("How do I structure a closing argument?", demo_data.REPONSE_CHAT_PLAIDOIRIE_EN),
        ("Hello", demo_data.REPONSE_CHAT_ACCUEIL_EN),
    ],
)
def test_choix_de_la_reponse_en_anglais(question, attendue):
    analyse.definir_langue_requete("en")
    assert demo_data.reponse_demo_pour_question(question) == attendue


@pytest.mark.parametrize(
    "reponse",
    [
        demo_data.REPONSE_CHAT_RESPONSABILITE_FR,
        demo_data.REPONSE_CHAT_PLAIDOIRIE_FR,
        demo_data.REPONSE_CHAT_RESPONSABILITE_EN,
        demo_data.REPONSE_CHAT_PLAIDOIRIE_EN,
    ],
)
def test_les_reponses_gardent_le_balisage_et_l_avertissement_demo(reponse):
    assert "[ART:" in reponse
    assert "[VERIF:" in reponse
    # Jamais présentée comme une analyse réelle (voir README, "mode démo transparent").
    assert "mode démo" in reponse or "demo-mode" in reponse or "demo mode" in reponse


def test_le_message_par_defaut_ne_pretend_pas_qu_un_dossier_de_demo_existe():
    """Aucun dossier n'est préchargé en mode démo : le texte de repli ne doit
    pas en promettre un (bug constaté : il citait « Vasseur c/ Atlas Logistique »)."""
    for reponse in (demo_data.REPONSE_CHAT_DEFAUT_FR, demo_data.REPONSE_CHAT_DEFAUT_EN):
        assert "Vasseur" not in reponse


def test_l_accueil_signale_le_mode_demo():
    assert "mode démo" in demo_data.REPONSE_CHAT_ACCUEIL_FR
    assert "demo mode" in demo_data.REPONSE_CHAT_ACCUEIL_EN
