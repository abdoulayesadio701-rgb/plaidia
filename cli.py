"""
cli.py — Interface en ligne de commande de l'agent de préparation de plaidoirie.

Commandes :
  python cli.py init-db
  python cli.py add-dossier --nom "Nom" --domaine "prud'hommes" [--parties ...] [--faits ...]
  python cli.py list-dossiers
  python cli.py analyse --dossier-id 1 --fichier conclusions.pdf
  python cli.py analyse --dossier-id 1 --texte "..."
  python cli.py show-analyses --dossier-id 1
"""

import argparse
import sys
import subprocess
import tempfile
import os
import re
import concurrent.futures
from pathlib import Path

# Force l'UTF-8 en sortie sur Windows, même quand la sortie est redirigée
# vers un fichier (sinon Python utilise cp1252 et plante sur les caractères
# spéciaux comme →, é, «, etc.)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import db
import extract
import export
import judilibre
import recherche_juridique
from analyse import analyser_conclusions, repondre_question, repondre_conversation, generer_plan_plaidoirie, simuler_objections, resumer_dossier, rediger_note_client, construire_chronologie, extraire_elements_cles, classifier_document, rediger_pv, reviser_texte, verifier_procedure, controler_coherence, consulter_jurisprudence, traiter_notes, consulter_position_jurisprudence, interpreter_intention, analyser_style_adverse, identifier_notions_juridiques

RISK_ORDER = {"Élevé": 0, "Moyen": 1, "Faible": 2}

DOMAINES_STANDARDS = [
    "Prud'hommes",
    "Pénal",
    "Civil",
    "Commercial",
    "Bail commercial",
    "Famille / Divorce",
    "Administratif",
    "Social",
    "Immobilier",
    "Autre",
]


def _choisir_domaine() -> str:
    """Affiche une liste de domaines standards pour éviter les doublons
    de saisie libre (ex. « prud'hommes » vs « prudhommes »)."""
    print("Domaine du dossier :")
    for i, d in enumerate(DOMAINES_STANDARDS, 1):
        print(f"  {i}. {d}")
    choix = input(f"Votre choix (1-{len(DOMAINES_STANDARDS)}, Entrée pour ignorer) : ").strip()

    if not choix:
        return ""
    try:
        index = int(choix) - 1
        if 0 <= index < len(DOMAINES_STANDARDS):
            domaine = DOMAINES_STANDARDS[index]
            if domaine == "Autre":
                return input("Précisez le domaine : ").strip()
            return domaine
    except ValueError:
        pass
    print("Choix non reconnu, domaine laissé vide.")
    return ""


def cmd_init_db(args):
    db.init_db()


def cmd_add_dossier(args):
    dossier_id = db.create_dossier(
        nom=args.nom, domaine=args.domaine or "", parties=args.parties or "", faits=args.faits or ""
    )
    print(f"Dossier créé (id={dossier_id}) : {args.nom}")


def cmd_list_dossiers(args):
    dossiers = db.list_dossiers()
    if not dossiers:
        print("Aucun dossier enregistré. Utilisez 'add-dossier' pour en créer un.")
        return
    for d in dossiers:
        print(f"[{d['id']}] {d['nom']} — {d['domaine'] or 'domaine non précisé'} — statut : {d['statut']}")


def cmd_analyse(args):
    dossier = db.get_dossier(args.dossier_id)
    if not dossier:
        print(f"Erreur : aucun dossier avec l'id {args.dossier_id}.", file=sys.stderr)
        sys.exit(1)

    if args.fichier:
        print(f"Extraction du texte depuis {args.fichier} ...")
        texte = extract.extract_text(args.fichier)
    elif args.texte:
        texte = args.texte
    else:
        print("Erreur : fournissez --fichier ou --texte.", file=sys.stderr)
        sys.exit(1)

    if not texte.strip():
        print("Erreur : aucun texte extrait ou fourni.", file=sys.stderr)
        sys.exit(1)

    jurisprudence = db.get_jurisprudence_validee(domaine=dossier["domaine"])

    contexte_recherche = None
    if args.recherche_live:
        print("Recherche en direct sur Légifrance et Judilibre...")
        mots_cles = args.recherche_live if isinstance(args.recherche_live, str) else dossier["domaine"] or dossier["nom"]
        contexte = recherche_juridique.rechercher_contexte_juridique(mots_cles)
        contexte_recherche = recherche_juridique.formater_contexte_pour_prompt(contexte)
        if contexte_recherche:
            print(f"  → {len(contexte['articles_loi'])} article(s) de loi, {len(contexte['jurisprudence'])} décision(s) trouvés.")
        else:
            print("  → Aucun résultat pertinent trouvé en ligne.")

    print("Analyse en cours (appel à Claude)...")
    result = analyser_conclusions(texte, contexte_recherche=contexte_recherche, jurisprudence_validee=jurisprudence)

    analyse_id = db.save_analyse(args.dossier_id, result["arguments"], result["points_attention"])
    print(f"Analyse enregistrée (id={analyse_id}).\n")

    _print_analyse(result)
    _proposer_export(dossier, result)


def cmd_show_analyses(args):
    analyses = db.get_analyses_for_dossier(args.dossier_id)
    if not analyses:
        print("Aucune analyse enregistrée pour ce dossier.")
        return
    for a in analyses:
        print(f"\n=== Analyse du {a['date']} (id={a['id']}) ===")
        _print_analyse(a)


def _print_analyse(result):
    args_sorted = sorted(
        result["arguments"], key=lambda a: RISK_ORDER.get(a.get("risque", "Moyen"), 1)
    )
    for i, arg in enumerate(args_sorted, 1):
        print(f"\n{i}. [{arg.get('risque', '?')}] {arg.get('resume', '')}")
        print(f"   Fondement : {arg.get('fondement', '')}")
        print(f"   Justification du risque : {arg.get('justification_risque', '')}")
        for r in arg.get("refutations", []):
            print(f"   → ({r.get('angle', '')}) {r.get('piste', '')}")

    if result.get("points_attention"):
        print("\n⚠ Points d'attention :")
        for p in result["points_attention"]:
            print(f"   - {p}")


def cmd_collecte_jurisprudence(args):
    print(f"Recherche Judilibre : « {args.query} » ...")
    collectees = judilibre.collecter_jurisprudence(
        query=args.query, domaine=args.domaine or "", max_results=args.max
    )
    if not collectees:
        print("Aucun résultat.")
        return
    for c in collectees:
        db.add_jurisprudence(
            reference=c["reference"], resume=c["resume"],
            domaine=c["domaine"], source=c["source"], validee=False
        )
    print(f"{len(collectees)} décision(s) collectée(s), en attente de validation.")
    print("Utilisez 'list-jurisprudence --statut attente' puis 'valider-jurisprudence --id N' pour les valider.")


def cmd_list_jurisprudence(args):
    if args.statut == "validee":
        rows = db.get_jurisprudence_validee(domaine=args.domaine)
    else:
        rows = db.get_jurisprudence_en_attente(domaine=args.domaine)
    if not rows:
        print("Aucune entrée.")
        return
    for r in rows:
        print(f"\n[{r['id']}] {r['reference']} ({r['domaine'] or 'domaine non précisé'})")
        print(f"    {r['resume'][:200]}{'…' if len(r['resume']) > 200 else ''}")
        print(f"    Source : {r['source']}")


def cmd_valider_jurisprudence(args):
    db.valider_jurisprudence(args.id)
    print(f"Référence [{args.id}] validée. L'agent peut désormais s'y référer.")


def cmd_rejeter_jurisprudence(args):
    db.rejeter_jurisprudence(args.id)
    print(f"Référence [{args.id}] rejetée et supprimée.")


def _proposer_export(dossier: dict, result: dict):
    choix = input("\nExporter cette analyse ? (w=Word, p=PDF, n=non) : ").strip().lower()
    if choix == "w":
        try:
            chemin = export.exporter_word(dossier, result)
            print(f"✅ Document Word créé : {chemin}")
        except Exception as e:
            print(f"Erreur lors de l'export Word : {e}")
    elif choix == "p":
        try:
            chemin = export.exporter_pdf(dossier, result)
            print(f"✅ Document PDF créé : {chemin}")
        except Exception as e:
            print(f"Erreur lors de l'export PDF : {e}")


def _editer_directement(texte: str) -> str:
    """Ouvre le texte dans le Bloc-notes (ou l'éditeur système) pour une
    modification manuelle directe. Retourne le contenu mis à jour une fois
    l'éditeur fermé par l'utilisateur."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(texte)
        chemin_temp = f.name

    print("\nOuverture dans le Bloc-notes pour modification directe...")
    print("Fermez le Bloc-notes une fois vos modifications terminées pour continuer.\n")

    try:
        if sys.platform == "win32":
            subprocess.run(["notepad.exe", chemin_temp])
        else:
            editeur = os.environ.get("EDITOR", "nano")
            subprocess.run([editeur, chemin_temp])
    except Exception as e:
        print(f"⚠ Impossible d'ouvrir l'éditeur : {e}")
        print("Le texte n'a pas été modifié.\n")
        return texte

    try:
        with open(chemin_temp, "r", encoding="utf-8") as f:
            nouveau_texte = f.read()
    except Exception as e:
        print(f"⚠ Erreur de lecture après édition : {e}")
        print("Le texte n'a pas été modifié.\n")
        return texte
    finally:
        try:
            os.unlink(chemin_temp)
        except Exception:
            pass

    return nouveau_texte


def _boucle_revision(texte: str, label: str = "document") -> str:
    """Affiche un texte généré et propose de le réviser en boucle, soit en
    décrivant un changement pour que l'IA l'applique, soit en éditant le
    texte directement dans le Bloc-notes — jusqu'à ce que le résultat
    convienne. Retourne la version finale."""
    while True:
        print("=" * 60)
        print(texte)
        print("=" * 60)
        print()
        print(f"Que voulez-vous faire avec ce {label} ?")
        print("  - Décrivez un changement pour que l'IA l'applique")
        print("  - Tapez 'e' pour l'éditer vous-même directement (Bloc-notes)")
        print("  - Appuyez sur Entrée pour valider")

        demande = input("Votre choix : ").strip()

        if not demande:
            return texte

        if demande.lower() == "e":
            texte = _editer_directement(texte)
            continue

        print("\nRévision en cours...\n")
        try:
            texte = reviser_texte(texte, demande)
        except Exception as e:
            print(f"⚠ Erreur lors de la révision : {e}")
            print("Le texte n'a pas été modifié — vous pouvez réessayer.\n")


def _saisir_texte_ou_fichier(consigne: str) -> str:
    """Demande à l'utilisateur de fournir du texte (collé/tapé) ou un
    fichier PDF/Word/Excel/Image/TXT, et retourne le texte extrait dans les deux cas.
    Gère les erreurs de fichier proprement (chemin invalide, format non
    supporté) sans jamais planter l'appelant."""
    choix = input("Fournir le texte comment ? (t = taper/coller, f = fichier PDF/Word/Excel/Image, Entrée = taper) : ").strip().lower()

    if choix == "f":
        chemin = input("Chemin complet du fichier (ex. C:\\Users\\...\\document.pdf) : ").strip().strip('"')
        if not chemin:
            print("Aucun chemin fourni.")
            return ""
        try:
            print(f"Extraction du texte depuis {chemin} ...")
            texte = extract.extract_text(chemin)
            print(f"✓ {len(texte)} caractères extraits.\n")
            return texte
        except FileNotFoundError:
            print(f"Erreur : fichier introuvable à « {chemin} ». Vérifiez le chemin (glissez-déposez le fichier dans le terminal pour obtenir le chemin exact).")
            return ""
        except ValueError as e:
            print(f"Erreur : {e}")
            return ""
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier : {e}")
            return ""

    print(consigne)
    print("Terminez en tapant FIN sur une ligne seule, puis Entrée :\n")
    lines = []
    while True:
        line = input()
        if line.strip() == "FIN":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def cmd_analyse_interactif(args, dossier=None):
    if dossier is None:
        dossiers = db.list_dossiers()
        if not dossiers:
            print("Aucun dossier enregistré. Créez-en un d'abord :")
            print('  python cli.py add-dossier --nom "Nom" --domaine "domaine"')
            return

        print("Dossiers disponibles :")
        for d in dossiers:
            print(f"  {d['nom']} — {d['domaine'] or 'domaine non précisé'}")

        saisie = input("\nNom du dossier à analyser (ou une partie du nom) : ").strip().lower()
        correspondances = [d for d in dossiers if saisie in d["nom"].lower() or (d["numero_dossier"] and saisie in d["numero_dossier"].lower())]

        if not correspondances:
            print(f"Aucun dossier ne correspond à « {saisie} ».")
            return
        if len(correspondances) > 1:
            print("Plusieurs dossiers correspondent, soyez plus précis :")
            for d in correspondances:
                print(f"  {d['nom']}")
            return

        dossier = correspondances[0]
    dossier_id = dossier["id"]
    print(f"→ Dossier sélectionné : {dossier['nom']}")

    print("\nConclusions adverses à analyser.")
    texte = _saisir_texte_ou_fichier("Collez ou tapez le texte des conclusions adverses.")
    if not texte:
        print("Aucun texte disponible pour l'analyse.")
        return

    if not texte:
        print("Aucun texte saisi.")
        return

    recherche = input("\nMots-clés pour la recherche live (Entrée pour ignorer) : ").strip()

    contexte_recherche = None
    if recherche:
        print("\nRecherche en direct sur Légifrance et Judilibre...")
        contexte = recherche_juridique.rechercher_contexte_juridique(recherche)
        contexte_recherche = recherche_juridique.formater_contexte_pour_prompt(contexte)
        print(f"  → {len(contexte['articles_loi'])} article(s) de loi, {len(contexte['jurisprudence'])} décision(s) trouvés.")

    jurisprudence = db.get_jurisprudence_validee(domaine=dossier["domaine"])

    print("\nAnalyse en cours (appel à Claude)...")
    result = analyser_conclusions(texte, contexte_recherche=contexte_recherche, jurisprudence_validee=jurisprudence)

    analyse_id = db.save_analyse(dossier_id, result["arguments"], result["points_attention"])
    print(f"Analyse enregistrée (id={analyse_id}).\n")

    _print_analyse(result)
    _proposer_export(dossier, result)
    _proposer_consultation_jurisprudence(_extraire_a_verifier_analyse(result), contexte_dossier=dossier["nom"])


def cmd_poser_question(args):
    print("Décrivez votre cas et posez votre question (situation, ce que vous cherchez à savoir).")
    question = _saisir_texte_ou_fichier("Décrivez votre cas et posez votre question.")

    if not question:
        print("Aucune question saisie.")
        return

    recherche_active = input("\nActiver la recherche live Légifrance/Judilibre ? (o/n, Entrée = oui) : ").strip().lower()

    contexte_recherche = None
    if recherche_active != "n":
        print("\nRecherche en direct sur Légifrance et Judilibre (max 12s par source)...")
        contexte = recherche_juridique.rechercher_contexte_juridique(question)
        contexte_recherche = recherche_juridique.formater_contexte_pour_prompt(contexte)
        print(f"  → {len(contexte['articles_loi'])} article(s) de loi, {len(contexte['jurisprudence'])} décision(s) trouvés.\n")
    else:
        print("\nRecherche live ignorée — réponse basée sur les connaissances générales du modèle.\n")

    # Historique de la conversation, pour que l'agent comprenne les questions
    # de suivi ("elle", "et sinon ?"...) sans que tout soit reformulé à chaque fois.
    historique = [{"role": "user", "content": question}]

    print("Réflexion en cours...\n")
    reponse = repondre_conversation(historique, contexte_recherche=contexte_recherche)
    print(reponse)
    print()
    historique.append({"role": "assistant", "content": reponse})
    _proposer_consultation_jurisprudence(_extraire_a_verifier_texte(reponse))

    # Boucle de suivi : la conversation continue tant que l'avocat a des
    # questions complémentaires, avec mémoire de tout ce qui a été dit.
    while True:
        suite = input("Question de suivi (Entrée pour terminer la conversation) : ").strip()
        if not suite:
            break
        historique.append({"role": "user", "content": suite})
        print("\nRéflexion en cours...\n")
        reponse = repondre_conversation(historique, contexte_recherche=contexte_recherche)
        print(reponse)
        print()
        historique.append({"role": "assistant", "content": reponse})
        _proposer_consultation_jurisprudence(_extraire_a_verifier_texte(reponse))


def cmd_generer_plan(args, dossier=None, duree_minutes=None):
    if dossier is None:
        dossiers = db.list_dossiers()
        if not dossiers:
            print("Aucun dossier enregistré. Créez-en un d'abord.")
            return

        print("Dossiers disponibles :")
        for d in dossiers:
            print(f"  {d['nom']} — {d['domaine'] or 'domaine non précisé'}")

        saisie = input("\nNom du dossier : ").strip().lower()
        correspondances = [d for d in dossiers if saisie in d["nom"].lower() or (d["numero_dossier"] and saisie in d["numero_dossier"].lower())]
        if not correspondances:
            print(f"Aucun dossier ne correspond à « {saisie} ».")
            return
        if len(correspondances) > 1:
            print("Plusieurs dossiers correspondent, soyez plus précis.")
            return

        dossier = correspondances[0]
    print(f"→ Dossier sélectionné : {dossier['nom']}")

    if duree_minutes is None:
        temps_str = input("Temps de parole imparti, en minutes : ").strip()
        try:
            duree_minutes = int(temps_str)
        except ValueError:
            print("Durée invalide.")
            return
    temps_minutes = duree_minutes

    analyses = db.get_analyses_for_dossier(dossier["id"])
    parts = []
    if dossier["faits"]:
        parts.append(f"Faits : {dossier['faits']}")
    if dossier["parties"]:
        parts.append(f"Parties : {dossier['parties']}")
    if analyses:
        derniere = analyses[0]
        parts.append("Arguments adverses déjà analysés :")
        for arg in derniere["arguments"]:
            parts.append(f"- [{arg.get('risque', '?')}] {arg.get('resume', '')}")
    contexte_dossier = "\n".join(parts) if parts else f"Dossier « {dossier['nom']} », domaine : {dossier['domaine']}. Peu d'informations détaillées disponibles."

    jurisprudence = db.get_jurisprudence_validee(domaine=dossier["domaine"])
    contexte_recherche = None
    if jurisprudence:
        refs = "\n".join(f"- {j['reference']} : {j.get('resume', '')}" for j in jurisprudence)
        contexte_recherche = f"\n\nRéférences validées disponibles :\n{refs}"

    print("\nGénération du plan en cours...\n")
    plan = generer_plan_plaidoirie(contexte_dossier, temps_minutes, contexte_recherche=contexte_recherche)

    print(f"🎤 ACCROCHE\n   {plan.get('accroche', '')}\n")
    for i, point in enumerate(plan.get("plan", []), 1):
        print(f"{i}. {point.get('point', '')} ({point.get('duree_minutes', '?')} min)")
        print(f"   Argument clé : {point.get('argument_cle', '')}")
        print(f"   Notes : {point.get('notes', '')}\n")
    print(f"🎤 CONCLUSION\n   {plan.get('conclusion', '')}\n")

    if plan.get("points_attention"):
        print("⚠ Points d'attention :")
        for p in plan["points_attention"]:
            print(f"   - {p}")
    print()

    _proposer_consultation_jurisprudence(_extraire_a_verifier_plan(plan), contexte_dossier=dossier["nom"])


def _construire_contexte_dossier(dossier):
    """Construit un résumé textuel d'un dossier à partir de ses champs et
    de sa dernière analyse, pour l'envoyer en contexte à Claude."""
    analyses = db.get_analyses_for_dossier(dossier["id"])
    parts = []
    if dossier["faits"]:
        parts.append(f"Faits : {dossier['faits']}")
    if dossier["parties"]:
        parts.append(f"Parties : {dossier['parties']}")
    if analyses:
        derniere = analyses[0]
        parts.append("Arguments adverses déjà analysés :")
        for arg in derniere["arguments"]:
            parts.append(f"- [{arg.get('risque', '?')}] {arg.get('resume', '')}")
    if parts:
        return "\n".join(parts)
    return f"Dossier « {dossier['nom']} », domaine : {dossier['domaine']}. Peu d'informations détaillées disponibles."


def cmd_simuler_objections(args, dossier=None):
    if dossier is None:
        dossiers = db.list_dossiers()
        if not dossiers:
            print("Aucun dossier enregistré. Créez-en un d'abord.")
            return

        print("Dossiers disponibles :")
        for d in dossiers:
            print(f"  {d['nom']} — {d['domaine'] or 'domaine non précisé'}")

        saisie = input("\nNom du dossier : ").strip().lower()
        correspondances = [d for d in dossiers if saisie in d["nom"].lower() or (d["numero_dossier"] and saisie in d["numero_dossier"].lower())]
        if not correspondances:
            print(f"Aucun dossier ne correspond à « {saisie} ».")
            return
        if len(correspondances) > 1:
            print("Plusieurs dossiers correspondent, soyez plus précis.")
            return

        dossier = correspondances[0]
    print(f"→ Dossier sélectionné : {dossier['nom']}")

    contexte_dossier = _construire_contexte_dossier(dossier)

    jurisprudence = db.get_jurisprudence_validee(domaine=dossier["domaine"])
    contexte_recherche = None
    if jurisprudence:
        refs = "\n".join(f"- {j['reference']} : {j.get('resume', '')}" for j in jurisprudence)
        contexte_recherche = f"\n\nRéférences validées disponibles :\n{refs}"

    print("\nGénération des questions probables en cours...\n")
    result = simuler_objections(contexte_dossier, contexte_recherche=contexte_recherche)

    for i, obj in enumerate(result.get("objections", []), 1):
        print(f"{i}. [{obj.get('origine', '?')}] {obj.get('question', '')}")
        print(f"   Piège : {obj.get('piege', '')}")
        print(f"   Piste de réponse : {obj.get('piste_reponse', '')}\n")

    if result.get("point_le_plus_faible"):
        print(f"⚠ Point le plus faible du dossier :\n   {result['point_le_plus_faible']}")
    print()

    _proposer_consultation_jurisprudence(_extraire_a_verifier_simulateur(result), contexte_dossier=dossier["nom"])


def cmd_rapport_complet(args, dossier=None):
    if dossier is None:
        dossiers = db.list_dossiers()
        if not dossiers:
            print("Aucun dossier enregistré. Créez-en un d'abord.")
            return

        print("Dossiers disponibles :")
        for d in dossiers:
            print(f"  {d['nom']} — {d['domaine'] or 'domaine non précisé'}")

        saisie = input("\nNom du dossier : ").strip().lower()
        correspondances = [d for d in dossiers if saisie in d["nom"].lower() or (d["numero_dossier"] and saisie in d["numero_dossier"].lower())]
        if not correspondances:
            print(f"Aucun dossier ne correspond à « {saisie} ».")
            return
        if len(correspondances) > 1:
            print("Plusieurs dossiers correspondent, soyez plus précis.")
            return

        dossier = correspondances[0]
    print(f"→ Dossier sélectionné : {dossier['nom']}")

    contexte_dossier = _construire_contexte_dossier(dossier)
    jurisprudence = db.get_jurisprudence_validee(domaine=dossier["domaine"])
    contexte_recherche = None
    if jurisprudence:
        refs = "\n".join(f"- {j['reference']} : {j.get('resume', '')}" for j in jurisprudence)
        contexte_recherche = f"\n\nRéférences validées disponibles :\n{refs}"

    analyses_existantes = db.get_analyses_for_dossier(dossier["id"])
    analyse_result = None
    if analyses_existantes:
        derniere = analyses_existantes[0]
        analyse_result = {"arguments": derniere["arguments"], "points_attention": derniere["points_attention"]}
        print("✓ Analyse existante récupérée depuis l'historique.")
    else:
        print("ℹ Aucune analyse préalable trouvée pour ce dossier — le rapport n'inclura pas cette section.")

    temps_str = input("\nTemps de parole pour le plan de plaidoirie, en minutes : ").strip()
    plan_result = None
    temps_minutes = None
    try:
        temps_minutes = int(temps_str)
    except ValueError:
        print("Durée invalide — le rapport n'inclura pas de plan.")

    print("\nGénération du plan et du simulateur d'objections en parallèle...")
    simulateur_result = None
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    try:
        future_plan = None
        if temps_minutes is not None:
            future_plan = executor.submit(generer_plan_plaidoirie, contexte_dossier, temps_minutes, contexte_recherche=contexte_recherche)
        future_simulateur = executor.submit(simuler_objections, contexte_dossier, contexte_recherche=contexte_recherche)

        if future_plan is not None:
            try:
                plan_result = future_plan.result()
            except Exception as e:
                print(f"⚠ Erreur lors de la génération du plan : {e}")
        try:
            simulateur_result = future_simulateur.result()
        except Exception as e:
            print(f"⚠ Erreur lors de la génération du simulateur : {e}")
    finally:
        executor.shutdown(wait=False)

    print("\n✅ Rapport complet prêt.\n")

    if plan_result:
        print("=== PLAN DE PLAIDOIRIE ===")
        print(f"Accroche : {plan_result.get('accroche', '')}\n")
    if analyse_result:
        print(f"=== ANALYSE === ({len(analyse_result.get('arguments', []))} argument(s) adverse(s))")
    print(f"=== SIMULATEUR === ({len(simulateur_result.get('objections', []))} question(s)/objection(s))\n")

    choix_export = input("Exporter ce rapport complet en Word ? (o/n) : ").strip().lower()
    if choix_export == "o":
        try:
            chemin = export.exporter_dossier_complet_word(dossier, analyse_result, plan_result, simulateur_result)
            print(f"✅ Rapport complet créé : {chemin}")
        except Exception as e:
            print(f"Erreur lors de l'export : {e}")
    print()


AVERTISSEMENT_CONFIDENTIALITE = """
════════════════════════════════════════════════════════════════════
  ⚠  CONFIDENTIALITÉ DES DONNÉES — À LIRE AVANT UTILISATION
════════════════════════════════════════════════════════════════════

Les informations que vous saisissez dans cet outil (faits d'un dossier,
questions, texte de conclusions...) sont envoyées à l'API d'Anthropic
(Claude) pour être traitées, ainsi qu'aux API publiques Légifrance et
Judilibre si la recherche live est activée.

Ces services sont extérieurs à votre cabinet. Avant d'utiliser cet
outil sur un dossier réel, assurez-vous que :

  • Vous êtes autorisé à transmettre ces informations à un tiers au
    regard du secret professionnel de l'avocat.
  • Vous avez, si nécessaire, anonymisé ou limité les données
    personnelles identifiantes de vos clients (noms complets,
    coordonnées précises...) avant de les saisir.
  • Vous avez informé votre client si votre politique de cabinet
    l'exige.

Cet outil est un prototype d'aide à la réflexion — il ne remplace pas
votre propre jugement professionnel, et toute référence juridique
balisée [VERIF:...] doit être contrôlée avant toute utilisation.
════════════════════════════════════════════════════════════════════
"""


def _demander_consentement_confidentialite() -> bool:
    print(AVERTISSEMENT_CONFIDENTIALITE)
    reponse = input("J'ai lu et je comprends ces informations — continuer ? (o/n) : ").strip().lower()
    return reponse == "o"


def cmd_preparer_dossier(args, dossier_preselectionne=None):
    """Construit progressivement un dossier en important plusieurs
    documents à la suite (Word, Excel, PDF, image, texte) — chaque
    document extrait vient s'ajouter aux faits du dossier."""
    if dossier_preselectionne is not None:
        dossier_id = dossier_preselectionne["id"]
        print(f"→ Dossier sélectionné : {dossier_preselectionne['nom']}\n")
    else:
        dossiers = db.list_dossiers()

        if dossiers:
            print("Dossiers disponibles :")
            for d in dossiers:
                print(f"  {d['nom']} — {d['domaine'] or 'domaine non précisé'}")
            saisie = input("\nNom (ou numéro) du dossier à préparer, ou 'nouveau' pour en créer un : ").strip()
        else:
            print("Aucun dossier enregistré.")
            saisie = "nouveau"

        if saisie.lower() == "nouveau":
            nom = input("Nom du nouveau dossier : ").strip()
            if not nom:
                print("Nom vide, opération annulée.")
                return
            numero_dossier = input("Numéro de référence (Entrée pour ignorer) : ").strip()
            domaine = _choisir_domaine()
            dossier_id = db.create_dossier(nom=nom, domaine=domaine, numero_dossier=numero_dossier)
            print(f"✅ Dossier « {nom} » créé.\n")
        else:
            saisie_lower = saisie.lower()
            correspondances = [d for d in dossiers if saisie_lower in d["nom"].lower() or (d["numero_dossier"] and saisie_lower in d["numero_dossier"].lower())]
            if not correspondances:
                print(f"Aucun dossier ne correspond à « {saisie} ».")
                return
            if len(correspondances) > 1:
                print("Plusieurs dossiers correspondent, soyez plus précis.")
                return
            dossier_id = correspondances[0]["id"]
            print(f"→ Dossier sélectionné : {correspondances[0]['nom']}\n")

    documents_importes = 0
    while True:
        mode = input("Ajouter : (t) texte collé, (f) fichier, ou Entrée pour terminer : ").strip().lower()
        if not mode:
            break

        if mode == "t":
            print("Collez ou tapez le texte. Terminez en tapant FIN sur une ligne seule, puis Entrée :")
            lignes = []
            while True:
                ligne = input()
                if ligne.strip() == "FIN":
                    break
                lignes.append(ligne)
            texte = "\n".join(lignes).strip()
            if not texte:
                print("Aucun texte saisi — ignoré.\n")
                continue
            db.ajouter_aux_faits(dossier_id, texte, source="texte collé")
            documents_importes += 1
            print(f"✓ {len(texte)} caractères ajoutés au dossier.\n")
            continue

        if mode == "f":
            chemin = input("Chemin du fichier (Word/Excel/PDF/Image/Texte) : ").strip().strip('"')
            if not chemin:
                print("Aucun chemin fourni — ignoré.\n")
                continue
            try:
                print(f"Extraction en cours depuis {chemin} ...")
                texte = extract.extract_text(chemin)
                if not texte.strip():
                    print("Aucun texte extrait de ce document — ignoré.\n")
                    continue
                nom_fichier = Path(chemin).name
                db.ajouter_aux_faits(dossier_id, texte, source=nom_fichier)
                documents_importes += 1
                print(f"✓ {len(texte)} caractères ajoutés au dossier depuis « {nom_fichier} ».\n")
            except FileNotFoundError:
                print(f"Erreur : fichier introuvable à « {chemin} ». Vérifiez le chemin (glissez-déposez le fichier dans le terminal).\n")
            except Exception as e:
                print(f"Erreur lors de l'import : {e}\n")
            continue

        print("Choix non reconnu — tapez 't', 'f', ou Entrée pour terminer.\n")

    if documents_importes:
        print(f"✅ {documents_importes} document(s) importé(s) dans le dossier.")
    else:
        print("Aucun document importé.")
    print()


def cmd_resumer_dossier(args, dossier=None):
    if dossier is None:
        dossiers = db.list_dossiers()
        if not dossiers:
            print("Aucun dossier enregistré.")
            return

        print("Dossiers disponibles :")
        for d in dossiers:
            print(f"  {d['nom']} — {d['domaine'] or 'domaine non précisé'}")

        saisie = input("\nNom (ou numéro) du dossier à résumer : ").strip().lower()
        correspondances = [d for d in dossiers if saisie in d["nom"].lower() or (d["numero_dossier"] and saisie in d["numero_dossier"].lower())]
        if not correspondances:
            print(f"Aucun dossier ne correspond à « {saisie} ».")
            return
        if len(correspondances) > 1:
            print("Plusieurs dossiers correspondent, soyez plus précis.")
            return

        dossier = correspondances[0]
    print(f"→ Dossier sélectionné : {dossier['nom']}\n")

    contexte_dossier = _construire_contexte_dossier(dossier)

    print("Génération du résumé en cours...\n")
    resume = resumer_dossier(contexte_dossier)

    print(f"📋 RÉSUMÉ\n   {resume.get('resume_court', '')}\n")

    if resume.get("points_cles"):
        print("Points clés :")
        for p in resume["points_cles"]:
            print(f"   • {p}")
        print()

    if resume.get("elements_manquants"):
        print("⚠ Éléments manquants ou à vérifier :")
        for e in resume["elements_manquants"]:
            print(f"   - {e}")
    print()


def cmd_rechercher_transversal_avec_terme(mot_cle: str):
    """Logique de recherche transversale, réutilisable sans redemander
    le terme (utilisée aussi par 'Parcourir mes dossiers')."""
    resultats = db.rechercher_dans_dossiers(mot_cle)

    if not resultats:
        print(f"\nAucun dossier ne contient « {mot_cle} ».\n")
        return

    print(f"\n{len(resultats)} dossier(s) trouvé(s) pour « {mot_cle} » :\n")
    for r in resultats:
        d = r["dossier"]
        print(f"📁 {d['nom']} — {d['domaine'] or 'domaine non précisé'}")
        for champ, extrait in r["extraits"]:
            print(f"   [{champ}] {extrait}")
        print()


def cmd_rechercher_transversal(args):
    mot_cle = input("Terme à rechercher dans tous vos dossiers : ").strip()
    if not mot_cle:
        print("Aucun terme saisi.")
        return
    cmd_rechercher_transversal_avec_terme(mot_cle)


def cmd_note_client(args, dossier=None):
    if dossier is None:
        dossiers = db.list_dossiers()
        if not dossiers:
            print("Aucun dossier enregistré.")
            return

        print("Dossiers disponibles :")
        for d in dossiers:
            print(f"  {d['nom']} — {d['domaine'] or 'domaine non précisé'}")

        saisie = input("\nNom (ou numéro) du dossier : ").strip().lower()
        correspondances = [d for d in dossiers if saisie in d["nom"].lower() or (d["numero_dossier"] and saisie in d["numero_dossier"].lower())]
        if not correspondances:
            print(f"Aucun dossier ne correspond à « {saisie} ».")
            return
        if len(correspondances) > 1:
            print("Plusieurs dossiers correspondent, soyez plus précis.")
            return

        dossier = correspondances[0]
    print(f"→ Dossier sélectionné : {dossier['nom']}\n")

    contexte_dossier = _construire_contexte_dossier(dossier)

    print("Rédaction de la note client en cours...\n")
    note = rediger_note_client(contexte_dossier)

    note = _boucle_revision(note, label="note client")

    choix_export = input("Exporter cette note en Word ? (o/n) : ").strip().lower()
    if choix_export == "o":
        try:
            chemin = export.exporter_note_client_word(dossier, note)
            print(f"✅ Note client créée : {chemin}")
        except Exception as e:
            print(f"Erreur lors de l'export : {e}")
    print()


def cmd_export_faits_bruts(args, dossier=None):
    if dossier is None:
        dossiers = db.list_dossiers()
        if not dossiers:
            print("Aucun dossier enregistré.")
            return

        print("Dossiers disponibles :")
        for d in dossiers:
            print(f"  {d['nom']} — {d['domaine'] or 'domaine non précisé'}")

        saisie = input("\nNom (ou numéro) du dossier : ").strip().lower()
        correspondances = [d for d in dossiers if saisie in d["nom"].lower() or (d["numero_dossier"] and saisie in d["numero_dossier"].lower())]
        if not correspondances:
            print(f"Aucun dossier ne correspond à « {saisie} ».")
            return
        if len(correspondances) > 1:
            print("Plusieurs dossiers correspondent, soyez plus précis.")
            return

        dossier = correspondances[0]

    try:
        chemin = export.exporter_faits_bruts_word(dossier)
        print(f"✅ Faits bruts exportés : {chemin}")
    except Exception as e:
        print(f"Erreur lors de l'export : {e}")
    print()


def cmd_collecter_jurisprudence(args):
    query = input("Mots-clés de recherche (ex. « licenciement faute grave ») : ").strip()
    if not query:
        print("Aucun terme saisi.")
        return
    domaine = _choisir_domaine()
    max_str = input("Nombre maximum de décisions à collecter (Entrée = 10) : ").strip()
    try:
        max_results = int(max_str) if max_str else 10
    except ValueError:
        max_results = 10

    print(f"\nRecherche Judilibre : « {query} » ...\n")
    collectees = judilibre.collecter_jurisprudence(query=query, domaine=domaine, max_results=max_results)
    if not collectees:
        print("Aucun résultat.\n")
        return

    for c in collectees:
        db.add_jurisprudence(reference=c["reference"], resume=c["resume"], domaine=c["domaine"], source=c["source"], validee=False)

    print(f"✓ {len(collectees)} décision(s) collectée(s), en attente de validation.")
    print("Utilisez « Valider/rejeter la jurisprudence en attente » pour les relire avant qu'elles ne soient utilisables.\n")


def cmd_gerer_jurisprudence(args):
    """Fusionne 'Voir la jurisprudence' et 'Valider/rejeter' : affiche
    d'abord la liste en attente, puis propose immédiatement de traiter
    une référence."""
    rows = db.get_jurisprudence_en_attente()
    if not rows:
        print("\nAucune référence en attente. Voici les références déjà validées :\n")
        validees = db.get_jurisprudence_validee()
        if not validees:
            print("Aucune référence validée non plus.\n")
            return
        for r in validees:
            print(f"[{r['id']}] {r['reference']} ({r['domaine'] or 'domaine non précisé'})")
        print()
        return

    print(f"\n{len(rows)} référence(s) en attente de validation :\n")
    for r in rows:
        print(f"[{r['id']}] {r['reference']} ({r['domaine'] or 'domaine non précisé'})")
        resume = r['resume'][:200] + ("…" if len(r['resume']) > 200 else "")
        print(f"    {resume}")
        print(f"    Source : {r['source']}\n")

    id_str = input("ID de la référence à traiter (Entrée pour ignorer) : ").strip()
    if not id_str:
        return
    try:
        ref_id = int(id_str)
    except ValueError:
        print("ID invalide.\n")
        return

    decision = input("Valider ou rejeter cette référence ? (v/r) : ").strip().lower()
    if decision == "v":
        db.valider_jurisprudence(ref_id)
        print(f"✅ Référence [{ref_id}] validée.\n")
    elif decision == "r":
        db.rejeter_jurisprudence(ref_id)
        print(f"🗑 Référence [{ref_id}] rejetée et supprimée.\n")
    else:
        print("Choix non reconnu, aucune action effectuée.\n")


def cmd_lister_jurisprudence(args):
    statut = input("Voir les références (v = validées, a = en attente, Entrée = en attente) : ").strip().lower()
    domaine = input("Filtrer par domaine (Entrée pour tout voir) : ").strip() or None

    if statut == "v":
        rows = db.get_jurisprudence_validee(domaine=domaine)
        titre = "validées"
    else:
        rows = db.get_jurisprudence_en_attente(domaine=domaine)
        titre = "en attente de validation"

    if not rows:
        print(f"\nAucune référence {titre}.\n")
        return

    print(f"\n{len(rows)} référence(s) {titre} :\n")
    for r in rows:
        print(f"[{r['id']}] {r['reference']} ({r['domaine'] or 'domaine non précisé'})")
        resume = r['resume'][:200] + ("…" if len(r['resume']) > 200 else "")
        print(f"    {resume}")
        print(f"    Source : {r['source']}\n")


# Balisage des références juridiques (voir analyse.REGLE_BALISAGE_CITATIONS)
# -- [VERIF:<description>] remplace l'ancien marqueur libre "À VÉRIFIER : "
# pour un point sans référence formelle identifiable, exactement le cas
# d'usage des fonctions ci-dessous (proposer une recherche de jurisprudence
# sur ce qui reste incertain). Le filet hérité ("À VÉRIFIER" en texte
# libre) reste détecté pour ne pas perdre les résultats déjà stockés avant
# ce chantier.
_RE_TAG_VERIF_CLI = re.compile(r"\[VERIF:([^\]]*)\]")


def _contient_point_a_verifier(texte: str) -> bool:
    return bool(_RE_TAG_VERIF_CLI.search(texte or "")) or "À VÉRIFIER" in (texte or "")


def _extraire_a_verifier_texte(texte: str) -> list:
    """Repère les fragments contenant un point à vérifier ([VERIF:...] ou,
    pour du texte antérieur à ce chantier, l'ancien marqueur "À VÉRIFIER")
    dans une réponse en texte libre (utilisé pour le chat, dont les
    réponses ne sont pas structurées en JSON)."""
    phrases = re.split(r'(?<=[.!?])\s+', texte)
    return [p.strip() for p in phrases if _contient_point_a_verifier(p)]


def _extraire_a_verifier_analyse(result: dict) -> list:
    """Récupère tous les points à vérifier présents dans les pistes de
    réfutation d'une analyse d'arguments adverses."""
    items = []
    for arg in result.get("arguments", []):
        for r in arg.get("refutations", []):
            piste = r.get("piste", "")
            if _contient_point_a_verifier(piste):
                items.append(piste)
    return items


def _extraire_a_verifier_plan(plan: dict) -> list:
    """Récupère tous les points à vérifier présents dans les notes d'un
    plan de plaidoirie."""
    items = []
    for point in plan.get("plan", []):
        notes = point.get("notes", "")
        if _contient_point_a_verifier(notes):
            items.append(notes)
    return items


def _extraire_a_verifier_simulateur(result: dict) -> list:
    """Récupère tous les points à vérifier présents dans les pistes de
    réponse du simulateur d'objections."""
    items = []
    for obj in result.get("objections", []):
        piste = obj.get("piste_reponse", "")
        if _contient_point_a_verifier(piste):
            items.append(piste)
    return items


def _proposer_consultation_jurisprudence(items_a_verifier: list, contexte_dossier: str = ""):
    """Propose de consulter la jurisprudence en direct sur les points
    balisés [VERIF:...] identifiés dans un résultat (analyse, plan,
    simulateur). N'agit que si l'utilisateur le demande explicitement."""
    if not items_a_verifier:
        return

    print("\nPoints « À VÉRIFIER » identifiés :")
    for i, item in enumerate(items_a_verifier, 1):
        print(f"  {i}. {item}")

    choix = input("\nConsulter la jurisprudence en direct sur ces points ? (o/n) : ").strip().lower()
    if choix != "o":
        return

    question = "Points à vérifier dans ce dossier :\n" + "\n".join(f"- {it}" for it in items_a_verifier)
    if contexte_dossier:
        question = f"Contexte du dossier : {contexte_dossier}\n\n{question}"

    print("\nRecherche de jurisprudence en direct sur Judilibre (max 12s)...")
    try:
        contexte = recherche_juridique.rechercher_contexte_juridique(question)
        contexte_recherche = recherche_juridique.formater_contexte_pour_prompt(contexte)
        print(f"  → {len(contexte['jurisprudence'])} décision(s) trouvée(s).\n")

        print("Analyse de la jurisprudence en cours...\n")
        reponse = consulter_jurisprudence(question, contexte_recherche)

        print("=" * 60)
        print(reponse)
        print("=" * 60)
        print()
    except Exception as e:
        print(f"⚠ Erreur lors de la consultation de jurisprudence : {e}\n")


def cmd_prendre_note(args, dossier=None):
    if dossier is None:
        dossiers = db.list_dossiers()
        if not dossiers:
            print("Aucun dossier enregistré. Créez-en un d'abord.")
            return
        print("Dossiers disponibles :")
        for d in dossiers:
            print(f"  {d['nom']} — {d['domaine'] or 'domaine non précisé'}")
        saisie = input("\nNom (ou numéro) du dossier : ").strip().lower()
        correspondances = [d for d in dossiers if saisie in d["nom"].lower() or (d["numero_dossier"] and saisie in d["numero_dossier"].lower())]
        if not correspondances:
            print(f"Aucun dossier ne correspond à « {saisie} ».")
            return
        if len(correspondances) > 1:
            print("Plusieurs dossiers correspondent, soyez plus précis.")
            return
        dossier = correspondances[0]
    print(f"→ Dossier sélectionné : {dossier['nom']}\n")

    print("Tapez votre note en vrac — pas besoin de la structurer, l'agent s'en charge.")
    lignes = []
    print("Terminez en tapant FIN sur une ligne seule, puis Entrée :\n")
    while True:
        ligne = input()
        if ligne.strip() == "FIN":
            break
        lignes.append(ligne)
    note_brute = "\n".join(lignes).strip()

    if not note_brute:
        print("Aucune note saisie.")
        return

    print("\nStructuration de la note en cours...\n")
    resultat = traiter_notes(note_brute)

    print("📝 NOTE STRUCTURÉE")
    print(resultat.get("note_structuree", ""))
    print()

    if resultat.get("actions_a_faire"):
        print("✅ Actions à faire :")
        for a in resultat["actions_a_faire"]:
            print(f"   ☐ {a}")
        print()

    if resultat.get("points_a_retenir"):
        print("📌 Points à retenir :")
        for p in resultat["points_a_retenir"]:
            print(f"   • {p}")
        print()

    db.ajouter_note(
        dossier["id"], note_brute,
        note_structuree=resultat.get("note_structuree", ""),
        actions=resultat.get("actions_a_faire", []),
        points=resultat.get("points_a_retenir", []),
    )
    print("✓ Note enregistrée dans le dossier.\n")


def cmd_consulter_notes(args, dossier=None):
    if dossier is None:
        dossiers = db.list_dossiers()
        if not dossiers:
            print("Aucun dossier enregistré.")
            return
        print("Dossiers disponibles :")
        for d in dossiers:
            print(f"  {d['nom']} — {d['domaine'] or 'domaine non précisé'}")
        saisie = input("\nNom (ou numéro) du dossier : ").strip().lower()
        correspondances = [d for d in dossiers if saisie in d["nom"].lower() or (d["numero_dossier"] and saisie in d["numero_dossier"].lower())]
        if not correspondances:
            print(f"Aucun dossier ne correspond à « {saisie} ».")
            return
        if len(correspondances) > 1:
            print("Plusieurs dossiers correspondent, soyez plus précis.")
            return
        dossier = correspondances[0]

    notes = db.get_notes_dossier(dossier["id"])
    if not notes:
        print(f"\nAucune note enregistrée pour « {dossier['nom']} ».\n")
        return

    print(f"\n{len(notes)} note(s) pour « {dossier['nom']} » :\n")
    for n in notes:
        print(f"--- {n['date_creation']} ---")
        print(n["note_structuree"] or n["note_brute"])
        if n["actions"]:
            print("Actions :")
            for a in n["actions"]:
                print(f"   ☐ {a}")
        print()


SOURCES_JURIDIQUES = [
    "Légifrance (France)",
    "OHADA",
    "Union européenne",
    "Droit sénégalais",
    "CEDEAO",
    "Conseil de l'Europe / CEDH",
    "Autre",
]

# État de la juridiction active, valable pour la durée de la session.
# Légifrance par défaut (recherche live déjà existante).
PARAMETRES_JURIDIQUES = {
    "source_active": "Légifrance (France)",
}


def cmd_parametres_juridiques(args):
    """Écran simple de sélection de la juridiction active : Légifrance
    ou une autre source déjà importée (OHADA, UE...). Un seul choix actif
    à la fois — pas de mode multi-source, pour rester simple à comprendre."""
    while True:
        sources_importees = db.lister_sources_corpus()
        sources_disponibles = ["Légifrance (France)"] + [s for s in sources_importees if s != "Légifrance (France)"]

        print("\n⚙️  JURIDICTION ACTIVE\n")
        print(f"Actuellement : {PARAMETRES_JURIDIQUES['source_active']}\n")
        print("Choisir la juridiction avec laquelle travailler :")
        for i, s in enumerate(sources_disponibles, 1):
            marque = "●" if s == PARAMETRES_JURIDIQUES["source_active"] else "○"
            print(f"  {i}. {marque} {s}")
        print(f"  {len(sources_disponibles) + 1}. Retour")

        choix = input(f"\nVotre choix (1-{len(sources_disponibles) + 1}) : ").strip()

        try:
            index = int(choix) - 1
            if index == len(sources_disponibles):
                return
            if 0 <= index < len(sources_disponibles):
                PARAMETRES_JURIDIQUES["source_active"] = sources_disponibles[index]
                print(f"\n✅ Juridiction active : {sources_disponibles[index]}\n")
            else:
                print("Numéro invalide.")
        except ValueError:
            print("Choix non reconnu.")


def _choisir_source_juridique() -> str:
    print("Source juridique du texte :")
    for i, s in enumerate(SOURCES_JURIDIQUES, 1):
        print(f"  {i}. {s}")
    choix = input(f"Votre choix (1-{len(SOURCES_JURIDIQUES)}) : ").strip()
    try:
        index = int(choix) - 1
        if 0 <= index < len(SOURCES_JURIDIQUES):
            source = SOURCES_JURIDIQUES[index]
            if source == "Autre":
                return input("Précisez la source : ").strip()
            return source
    except ValueError:
        pass
    return "Non précisée"


def cmd_importer_texte_corpus(args):
    print("Importer un texte juridique (Acte uniforme OHADA, règlement UE, texte sénégalais...).")
    contenu = _saisir_texte_ou_fichier("Collez le texte, ou importez un fichier PDF/Word.")
    if not contenu:
        print("Aucun texte fourni.")
        return

    source = _choisir_source_juridique()
    pays = input("Pays / zone concernée (Entrée pour ignorer) : ").strip()
    type_texte = input("Type de texte (ex. 'Acte uniforme', 'Règlement', 'Loi' — Entrée pour ignorer) : ").strip()
    domaine = input("Domaine (ex. 'Droit commercial général' — Entrée pour ignorer) : ").strip()
    reference = input("Référence précise du texte : ").strip()
    date_texte = input("Date du texte (Entrée pour ignorer) : ").strip()

    texte_id = db.ajouter_texte_corpus(
        source=source, contenu=contenu, pays=pays, type_texte=type_texte,
        domaine=domaine, reference=reference, date_texte=date_texte, validee=False,
    )
    print(f"\n✓ Texte importé (id={texte_id}), en attente de validation.")
    print("Utilisez « Valider les textes en attente » avant de pouvoir vous en servir.\n")


def cmd_valider_corpus(args):
    en_attente = db.get_corpus_en_attente()
    if not en_attente:
        print("\nAucun texte en attente de validation.\n")
        return

    print(f"\n{len(en_attente)} texte(s) en attente :\n")
    for t in en_attente:
        apercu = t["contenu"][:150] + ("…" if len(t["contenu"]) > 150 else "")
        print(f"[{t['id']}] {t['source']} — {t['reference'] or 'sans référence'} ({t['pays'] or 'pays non précisé'})")
        print(f"    {apercu}\n")

    id_str = input("ID du texte à traiter (Entrée pour ignorer) : ").strip()
    if not id_str:
        return
    try:
        texte_id = int(id_str)
    except ValueError:
        print("ID invalide.\n")
        return

    decision = input("Valider ou rejeter ce texte ? (v/r) : ").strip().lower()
    if decision == "v":
        db.valider_texte_corpus(texte_id)
        print(f"✅ Texte [{texte_id}] validé — utilisable désormais comme source fiable.\n")
    elif decision == "r":
        db.rejeter_texte_corpus(texte_id)
        print(f"🗑 Texte [{texte_id}] rejeté et supprimé.\n")
    else:
        print("Choix non reconnu, aucune action effectuée.\n")


def cmd_gerer_corpus(args):
    """Fusionne 'Voir le corpus' et 'Valider/rejeter un texte' : affiche
    d'abord ce qui est en attente et propose de le traiter ; sinon,
    affiche ce qui est déjà validé."""
    en_attente = db.get_corpus_en_attente()

    if en_attente:
        print(f"\n{len(en_attente)} texte(s) en attente de validation :\n")
        for t in en_attente:
            apercu = t["contenu"][:150] + ("…" if len(t["contenu"]) > 150 else "")
            print(f"[{t['id']}] {t['source']} — {t['reference'] or 'sans référence'} ({t['pays'] or 'pays non précisé'})")
            print(f"    {apercu}\n")

        id_str = input("ID du texte à traiter (Entrée pour ignorer) : ").strip()
        if not id_str:
            return
        try:
            texte_id = int(id_str)
        except ValueError:
            print("ID invalide.\n")
            return

        decision = input("Valider ou rejeter ce texte ? (v/r) : ").strip().lower()
        if decision == "v":
            db.valider_texte_corpus(texte_id)
            print(f"✅ Texte [{texte_id}] validé — utilisable désormais comme source fiable.\n")
        elif decision == "r":
            db.rejeter_texte_corpus(texte_id)
            print(f"🗑 Texte [{texte_id}] rejeté et supprimé.\n")
        else:
            print("Choix non reconnu, aucune action effectuée.\n")
        return

    sources = db.lister_sources_corpus()
    if not sources:
        print("\nAucun texte dans le corpus multi-source pour l'instant.\n")
        return

    print(f"\nAucun texte en attente. Sources déjà validées : {', '.join(sources)}\n")
    filtre = input("Filtrer par source (Entrée pour tout voir) : ").strip()
    valides = db.get_corpus_valide(source=filtre or None)
    if not valides:
        print("Aucun texte validé pour ce filtre.\n")
        return
    for t in valides:
        print(f"[{t['source']}] {t['reference'] or 'sans référence'} — {t['pays'] or 'pays non précisé'}")
        print(f"   Domaine : {t['domaine'] or 'non précisé'} | Date : {t['date_texte'] or 'non précisée'}\n")


def cmd_voir_corpus(args):
    sources = db.lister_sources_corpus()
    if not sources:
        print("\nAucun texte dans le corpus multi-source pour l'instant.\n")
        return

    print(f"\nSources présentes : {', '.join(sources)}\n")
    filtre = input("Filtrer par source (Entrée pour tout voir) : ").strip()
    valides = db.get_corpus_valide(source=filtre or None)

    if not valides:
        print("Aucun texte validé pour ce filtre.\n")
        return

    for t in valides:
        print(f"[{t['source']}] {t['reference'] or 'sans référence'} — {t['pays'] or 'pays non précisé'}")
        print(f"   Domaine : {t['domaine'] or 'non précisé'} | Date : {t['date_texte'] or 'non précisée'}\n")


def cmd_consulter_jurisprudence(args):
    print("Décrivez la situation sur laquelle vous voulez savoir ce que dit la jurisprudence.")
    question = _saisir_texte_ou_fichier("Décrivez la situation.")
    if not question:
        print("Aucune question saisie.")
        return

    print("\nDans quel but ? (optionnel — oriente le classement des décisions trouvées)\n")
    buts = [
        "Décisions favorables à mon client",
        "Anticiper les décisions défavorables (adversaire)",
        "Comprendre l'état du droit — neutre",
        "Évaluer mes chances — vue équilibrée",
    ]
    for i, b in enumerate(buts, 1):
        print(f"  {i}. {b}")
    print(f"  {len(buts) + 1}. (non précisé)")
    choix_but = input(f"\nVotre choix (1-{len(buts) + 1}, Entrée pour ignorer) : ").strip()
    but = ""
    try:
        index = int(choix_but) - 1
        if 0 <= index < len(buts):
            but = buts[index]
    except ValueError:
        pass

    source_active = PARAMETRES_JURIDIQUES["source_active"]
    print(f"\nJuridiction active : {source_active}\n")

    print("Compréhension de la situation en cours...")
    notions = identifier_notions_juridiques(question, but)
    if notions.get("domaine"):
        print(f"Domaine identifié : {notions['domaine']}")
    mots_cles = notions.get("mots_cles_recherche") or []
    requete_recherche = " ".join(mots_cles) if mots_cles else question

    contexte_recherche = ""

    if source_active == "Légifrance (France)":
        print("\nRecherche en direct sur Judilibre (max 12s)...")
        contexte_live = recherche_juridique.rechercher_contexte_juridique(requete_recherche)
        contexte_recherche = recherche_juridique.formater_contexte_pour_prompt(contexte_live)
        print(f"  → {len(contexte_live['jurisprudence'])} décision(s) trouvée(s).\n")
    else:
        textes = db.get_corpus_valide(source=source_active)
        if textes:
            print(f"  → {len(textes)} texte(s) validé(s) trouvé(s) pour « {source_active} ».\n")
            bloc = "\n".join(f"[{t['reference'] or 'sans référence'}] {t['contenu'][:2000]}" for t in textes)
            contexte_recherche = f"--- Source : {source_active} ---\n{bloc}"
        else:
            print(f"⚠ Aucun texte validé pour « {source_active} » — importez-en depuis « Importer un texte », puis validez-le.\n")

    print("Analyse en cours...\n")
    reponse = consulter_jurisprudence(
        question, contexte_recherche,
        qualification=notions.get("qualification_juridique", ""),
        but=notions.get("but", but),
    )

    print("=" * 60)
    print(reponse)
    print("=" * 60)
    print()


def cmd_valider_rejeter_jurisprudence(args):
    rows = db.get_jurisprudence_en_attente()
    if not rows:
        print("\nAucune référence en attente de validation.\n")
        return

    print(f"\n{len(rows)} référence(s) en attente :\n")
    for r in rows:
        print(f"[{r['id']}] {r['reference']} ({r['domaine'] or 'domaine non précisé'})")
        resume = r['resume'][:200] + ("…" if len(r['resume']) > 200 else "")
        print(f"    {resume}")
        print(f"    Source : {r['source']}\n")

    id_str = input("ID de la référence à traiter (Entrée pour ignorer) : ").strip()
    if not id_str:
        return
    try:
        ref_id = int(id_str)
    except ValueError:
        print("ID invalide.\n")
        return

    decision = input("Valider ou rejeter cette référence ? (v/r) : ").strip().lower()
    if decision == "v":
        db.valider_jurisprudence(ref_id)
        print(f"✅ Référence [{ref_id}] validée — l'agent peut désormais s'y référer avec confiance.\n")
    elif decision == "r":
        db.rejeter_jurisprudence(ref_id)
        print(f"🗑 Référence [{ref_id}] rejetée et supprimée.\n")
    else:
        print("Choix non reconnu, aucune action effectuée.\n")


def _menu_actions_dossier(dossier):
    print(f"\n── Dossier : {dossier['nom']} ──")
    print("Tapez librement ce que vous voulez faire, ou '?' pour voir les options numérotées.\n")


def _afficher_options_dossier():
    print("  1. Importer des documents / préparer le dossier")
    print("  2. Analyser des conclusions adverses")
    print("  3. Résumer ce dossier")
    print("  4. Générer le plan de plaidoirie")
    print("  5. Simuler les objections probables")
    print("  6. Rapport complet")
    print("  7. Prendre une note")
    print("  8. Consulter les notes")
    print("  9. Rédiger une note client")
    print("  10. Exporter les faits bruts")
    print("  11. Changer de dossier")
    print("  12. Retour à l'accueil\n")


def _executer_action_dossier(code, dossier, duree_minutes=None):
    """Exécute une action sur un dossier déjà sélectionné, que le code
    vienne d'un choix numéroté ou d'une intention interprétée en langage
    naturel."""
    if code in ("1", "importer"):
        cmd_preparer_dossier(None, dossier_preselectionne=dossier)
    elif code in ("2", "analyser"):
        cmd_analyse_interactif(None, dossier=dossier)
    elif code in ("3", "resumer"):
        cmd_resumer_dossier(None, dossier=dossier)
    elif code in ("4", "plan"):
        cmd_generer_plan(None, dossier=dossier, duree_minutes=duree_minutes)
    elif code in ("5", "simulateur"):
        cmd_simuler_objections(None, dossier=dossier)
    elif code in ("6", "rapport"):
        cmd_rapport_complet(None, dossier=dossier)
    elif code in ("7", "note"):
        cmd_prendre_note(None, dossier=dossier)
    elif code in ("8", "notes_consulter"):
        cmd_consulter_notes(None, dossier=dossier)
    elif code in ("9", "note_client"):
        cmd_note_client(None, dossier=dossier)
    elif code in ("10", "export"):
        cmd_export_faits_bruts(None, dossier=dossier)
    else:
        return False
    return True


def cmd_ouvrir_dossier(args):
    nom = input("Nom du dossier : ").strip()
    numero_dossier = input("Numéro de référence (RG, numéro interne cabinet — Entrée pour ignorer) : ").strip()
    domaine = _choisir_domaine()
    parties = input("Parties concernées (Entrée pour ignorer) : ").strip()
    faits = input("Résumé des faits (Entrée pour ignorer) : ").strip()
    db.create_dossier(nom=nom, domaine=domaine, parties=parties, faits=faits, numero_dossier=numero_dossier)
    ref = f" (n° {numero_dossier})" if numero_dossier else ""
    print(f"\n✅ Dossier « {nom} »{ref} créé.\n")


def cmd_historique_dossier(args):
    dossiers = db.list_dossiers()
    if not dossiers:
        print("\nAucun dossier enregistré.\n")
        return
    print("\nDossiers disponibles :")
    for d in dossiers:
        print(f"  {d['nom']}")
    saisie = input("\nNom du dossier : ").strip().lower()
    correspondances = [d for d in dossiers if saisie in d["nom"].lower() or (d["numero_dossier"] and saisie in d["numero_dossier"].lower())]
    if not correspondances:
        print(f"Aucun dossier ne correspond à « {saisie} ».\n")
        return
    if len(correspondances) > 1:
        print("Plusieurs dossiers correspondent, soyez plus précis.\n")
        return
    analyses = db.get_analyses_for_dossier(correspondances[0]["id"])
    if not analyses:
        print("Aucune analyse enregistrée pour ce dossier.\n")
        return
    for a in analyses:
        print(f"\n=== Analyse du {a['date']} ===")
        _print_analyse(a)
    print()


def cmd_voir_tous_dossiers(args):
    dossiers = db.list_dossiers()
    if not dossiers:
        print("\nAucun dossier enregistré.\n")
        return
    print()
    par_domaine = {}
    for d in dossiers:
        cle = d["domaine"] or "Domaine non précisé"
        par_domaine.setdefault(cle, []).append(d)
    for domaine in sorted(par_domaine.keys()):
        print(f"── {domaine} ──")
        for d in par_domaine[domaine]:
            ref = f" [n° {d['numero_dossier']}]" if d["numero_dossier"] else ""
            print(f"  {d['nom']}{ref} — statut : {d['statut']}")
        print()


def cmd_parcourir_dossiers(args):
    """Fusionne 'Voir tous mes dossiers' et 'Rechercher dans tous les
    dossiers' : affiche d'abord la liste complète, puis propose une
    recherche par mot-clé optionnelle."""
    cmd_voir_tous_dossiers(args)
    mot_cle = input("Rechercher un terme précis (Entrée pour ne pas chercher) : ").strip()
    if mot_cle:
        cmd_rechercher_transversal_avec_terme(mot_cle)


def cmd_supprimer_dossier(args):
    dossiers = db.list_dossiers()
    if not dossiers:
        print("\nAucun dossier enregistré.\n")
        return
    print("\nDossiers disponibles :")
    for d in dossiers:
        print(f"  {d['nom']} — {d['domaine'] or 'domaine non précisé'}")
    saisie = input("\nNom du dossier à supprimer : ").strip().lower()
    correspondances = [d for d in dossiers if saisie in d["nom"].lower() or (d["numero_dossier"] and saisie in d["numero_dossier"].lower())]
    if not correspondances:
        print(f"Aucun dossier ne correspond à « {saisie} ».\n")
        return
    if len(correspondances) > 1:
        print("Plusieurs dossiers correspondent, soyez plus précis.\n")
        return
    cible = correspondances[0]
    analyses = db.get_analyses_for_dossier(cible["id"])
    print(f"\n⚠ Vous allez supprimer « {cible['nom']} » et {len(analyses)} analyse(s) associée(s).")
    print("Cette action est IRRÉVERSIBLE.")
    confirmation = input(f"Tapez exactement le nom du dossier pour confirmer ({cible['nom']}) : ").strip()
    if confirmation == cible["nom"]:
        db.delete_dossier(cible["id"])
        print(f"✅ Dossier « {cible['nom']} » supprimé.\n")
    else:
        print("Confirmation incorrecte — suppression annulée.\n")


def cmd_modifier_domaine_dossier(args):
    dossiers = db.list_dossiers()
    if not dossiers:
        print("\nAucun dossier enregistré.\n")
        return
    print("\nDossiers disponibles :")
    for d in dossiers:
        print(f"  {d['nom']} — domaine actuel : {d['domaine'] or 'non précisé'}")
    saisie = input("\nNom (ou numéro) du dossier à modifier : ").strip().lower()
    correspondances = [d for d in dossiers if saisie in d["nom"].lower() or (d["numero_dossier"] and saisie in d["numero_dossier"].lower())]
    if not correspondances:
        print(f"Aucun dossier ne correspond à « {saisie} ».\n")
        return
    if len(correspondances) > 1:
        print("Plusieurs dossiers correspondent, soyez plus précis.\n")
        return
    cible = correspondances[0]
    print(f"→ Dossier sélectionné : {cible['nom']} (domaine actuel : {cible['domaine'] or 'non précisé'})\n")
    nouveau_domaine = _choisir_domaine()
    db.update_domaine(cible["id"], nouveau_domaine)
    print(f"✅ Domaine mis à jour : « {nouveau_domaine or 'non précisé'} ».\n")


def cmd_travailler_dossier(args):
    dossiers = db.list_dossiers()
    if dossiers:
        print("Dossiers disponibles :")
        for d in dossiers:
            print(f"  {d['nom']} — {d['domaine'] or 'domaine non précisé'}")
        saisie = input("\nNom (ou numéro) du dossier, ou 'nouveau' pour en créer un : ").strip()
    else:
        print("Aucun dossier enregistré.")
        saisie = "nouveau"

    if saisie.lower() == "nouveau":
        nom = input("Nom du nouveau dossier : ").strip()
        if not nom:
            print("Nom vide, opération annulée.")
            return
        numero_dossier = input("Numéro de référence (Entrée pour ignorer) : ").strip()
        domaine = _choisir_domaine()
        dossier_id = db.create_dossier(nom=nom, domaine=domaine, numero_dossier=numero_dossier)
        print(f"✅ Dossier « {nom} » créé.\n")
        dossier = [d for d in db.list_dossiers() if d["id"] == dossier_id][0]
    else:
        saisie_lower = saisie.lower()
        correspondances = [d for d in dossiers if saisie_lower in d["nom"].lower() or (d["numero_dossier"] and saisie_lower in d["numero_dossier"].lower())]
        if not correspondances:
            print(f"Aucun dossier ne correspond à « {saisie} ».")
            return
        if len(correspondances) > 1:
            print("Plusieurs dossiers correspondent, soyez plus précis.")
            return
        dossier = correspondances[0]

    while True:
        _menu_actions_dossier(dossier)
        demande = input("Vous : ").strip()

        if not demande:
            continue

        if demande == "?":
            _afficher_options_dossier()
            continue

        # Choix numérique direct
        if demande in ("11",):
            return cmd_travailler_dossier(args)
        if demande in ("12",):
            return
        if demande in [str(i) for i in range(1, 11)]:
            try:
                _executer_action_dossier(demande, dossier)
            except Exception as e:
                print(f"\n⚠ Une erreur est survenue : {e}\n")
            continue

        # Sinon, interprétation en langage naturel
        try:
            intention = interpreter_intention(demande)
        except Exception as e:
            print(f"\n⚠ Impossible d'interpréter la demande : {e}")
            print("Tapez '?' pour voir les options numérotées.\n")
            continue

        action = intention.get("action", "menu")
        confiance = intention.get("confiance", "basse")
        reformulation = intention.get("reformulation", "")

        if action == "quitter":
            return cmd_travailler_dossier(args)
        if action == "menu" or confiance == "basse":
            if reformulation:
                print(f"\nJe ne suis pas certain d'avoir bien compris : {reformulation}")
            print("Tapez '?' pour voir les options numérotées, ou reformulez votre demande.\n")
            continue

        if reformulation:
            print(f"\n→ {reformulation}")

        try:
            executee = _executer_action_dossier(action, dossier, duree_minutes=intention.get("duree_minutes"))
            if not executee:
                print("Action non reconnue. Tapez '?' pour voir les options numérotées.\n")
        except Exception as e:
            print(f"\n⚠ Une erreur est survenue : {e}\n")


def cmd_menu_chemise(args):
    while True:
        print("\n── 📁 LA CHEMISE — Gestion des dossiers ──\n")
        print("  1. Ouvrir un nouveau dossier")
        print("  2. Consulter l'historique d'un dossier")
        print("  3. Parcourir mes dossiers (voir / rechercher)")
        print("  4. Préparer mon dossier (importer des documents)")
        print("  5. Exporter les faits bruts d'un dossier")
        print("  6. Modifier le domaine d'un dossier")
        print("  7. Supprimer un dossier")
        print("  8. Retour")

        choix = input("\nVotre choix (1-8) : ").strip()
        try:
            if choix == "1":
                cmd_ouvrir_dossier(args)
            elif choix == "2":
                cmd_historique_dossier(args)
            elif choix == "3":
                cmd_parcourir_dossiers(args)
            elif choix == "4":
                cmd_preparer_dossier(args)
            elif choix == "5":
                cmd_export_faits_bruts(args)
            elif choix == "6":
                cmd_modifier_domaine_dossier(args)
            elif choix == "7":
                cmd_supprimer_dossier(args)
            elif choix == "8":
                return
            else:
                print("\nChoix non reconnu.\n")
        except Exception as e:
            print(f"\n⚠ Une erreur est survenue pendant cette opération : {e}")
            print("Le programme continue normalement.\n")


def cmd_analyser_style(args):
    print("Analyse stylistique et rhétorique de conclusions adverses.")
    print("Complète l'analyse juridique classique par un angle linguistique : langage de couverture, affirmations risquées, voix passive suspecte, ruptures de registre.\n")

    texte = _saisir_texte_ou_fichier("Collez le texte des conclusions adverses à analyser.")
    if not texte:
        print("Aucun texte fourni.")
        return

    print("\nAnalyse stylistique en cours...\n")
    resultat = analyser_style_adverse(texte)

    print("=" * 60)
    print("🔍 ANALYSE STYLISTIQUE ET RHÉTORIQUE")
    print("=" * 60)

    sections = [
        ("langage_de_couverture", "🗣️  Langage de couverture (hedging)"),
        ("affirmations_absolues", "⚠️  Affirmations absolues risquées"),
        ("voix_passive_suspecte", "👤 Voix passive suspecte"),
        ("ruptures_registre", "📉 Ruptures de registre"),
    ]
    for cle, titre in sections:
        elements = resultat.get(cle, [])
        print(f"\n{titre} :")
        if elements:
            for e in elements:
                print(f"  « {e.get('citation', '')} »")
                print(f"    → {e.get('commentaire', '')}")
        else:
            print("  Rien de notable détecté.")

    if resultat.get("synthese_strategique"):
        print(f"\n💡 Synthèse stratégique :\n{resultat['synthese_strategique']}")

    print()
    print("ℹ Cette analyse est un outil de réflexion stratégique, pas une preuve juridique.\n")


def cmd_menu_arsenal(args):
    while True:
        print("\n── ⚔️ L'ARSENAL — Préparation stratégique ──\n")
        print("  1. Analyser des conclusions adverses")
        print("  2. Générer un plan de plaidoirie")
        print("  3. Simuler les questions/objections probables")
        print("  4. Rapport complet (analyse + plan + simulateur)")
        print("  5. Résumer un dossier")
        print("  6. 🔍 Analyse stylistique des conclusions adverses")
        print("  7. Retour")

        choix = input("\nVotre choix (1-7) : ").strip()
        try:
            if choix == "1":
                cmd_analyse_interactif(args)
            elif choix == "2":
                cmd_generer_plan(args)
            elif choix == "3":
                cmd_simuler_objections(args)
            elif choix == "4":
                cmd_rapport_complet(args)
            elif choix == "5":
                cmd_resumer_dossier(args)
            elif choix == "6":
                cmd_analyser_style(args)
            elif choix == "7":
                return
            else:
                print("\nChoix non reconnu.\n")
        except Exception as e:
            print(f"\n⚠ Une erreur est survenue pendant cette opération : {e}")
            print("Le programme continue normalement.\n")


def cmd_menu_grimoire(args):
    while True:
        print("\n── 📖 LE GRIMOIRE — Bibliothèque juridique multi-source ──\n")
        print("  1. Collecter de la jurisprudence française (Judilibre)")
        print("  2. Gérer la jurisprudence (voir / valider / rejeter)")
        print("  3. Consulter la jurisprudence sur une situation")
        print("  4. Importer un texte (OHADA, UE, Sénégal...)")
        print("  5. Gérer le corpus multi-source (voir / valider / rejeter)")
        print("  6. ⚙️  Paramètres juridiques (sources actives, mode)")
        print("  7. Retour")

        choix = input("\nVotre choix (1-7) : ").strip()
        try:
            if choix == "1":
                cmd_collecter_jurisprudence(args)
            elif choix == "2":
                cmd_gerer_jurisprudence(args)
            elif choix == "3":
                cmd_consulter_jurisprudence(args)
            elif choix == "4":
                cmd_importer_texte_corpus(args)
            elif choix == "5":
                cmd_gerer_corpus(args)
            elif choix == "6":
                cmd_parametres_juridiques(args)
            elif choix == "7":
                return
            else:
                print("\nChoix non reconnu.\n")
        except Exception as e:
            print(f"\n⚠ Une erreur est survenue pendant cette opération : {e}")
            print("Le programme continue normalement.\n")


def cmd_menu_carnet(args):
    while True:
        print("\n── ✒️ LE CARNET — Notes & communication ──\n")
        print("  1. Prendre une note intelligente")
        print("  2. Consulter les notes d'un dossier")
        print("  3. Note client en langage simple")
        print("  4. Retour")

        choix = input("\nVotre choix (1-4) : ").strip()
        try:
            if choix == "1":
                cmd_prendre_note(args)
            elif choix == "2":
                cmd_consulter_notes(args)
            elif choix == "3":
                cmd_note_client(args)
            elif choix == "4":
                return
            else:
                print("\nChoix non reconnu.\n")
        except Exception as e:
            print(f"\n⚠ Une erreur est survenue pendant cette opération : {e}")
            print("Le programme continue normalement.\n")


def cmd_menu_avocat(args):
    if not _demander_consentement_confidentialite():
        print("\nUtilisation annulée. À bientôt.")
        return

    print("\nBonjour, que souhaitez-vous faire ?\n")
    while True:
        print("  0. ⭐ Travailler sur un dossier (parlez librement à l'agent)")
        print("  1. Poser une question sur un cas")
        print("  2. 📁 La Chemise — gestion des dossiers")
        print("  3. ⚔️ L'Arsenal — analyse & préparation")
        print("  4. 📖 Le Grimoire — jurisprudence")
        print("  5. ✒️ Le Carnet — notes & communication")
        print("  6. Retour à l'accueil")

        choix = input("\nVotre choix (0-6) : ").strip()

        try:
            if choix == "0":
                cmd_travailler_dossier(args)
            elif choix == "1":
                cmd_poser_question(args)
            elif choix == "2":
                cmd_menu_chemise(args)
            elif choix == "3":
                cmd_menu_arsenal(args)
            elif choix == "4":
                cmd_menu_grimoire(args)
            elif choix == "5":
                cmd_menu_carnet(args)
            elif choix == "6":
                break
            else:
                print("\nChoix non reconnu, merci de taper un nombre entre 0 et 6.\n")
        except Exception as e:
            print(f"\n⚠ Une erreur est survenue pendant cette opération : {e}")
            print("Le programme continue normalement — vous pouvez réessayer ou choisir une autre option.\n")


AVERTISSEMENT_GREFFIER = """
════════════════════════════════════════════════════════════════════
  ⚠  ESPACE GREFFIER / MAGISTRAT — CONFIDENTIALITÉ ET NEUTRALITÉ
════════════════════════════════════════════════════════════════════

Cet espace propose des outils d'assistance neutres pour la gestion
d'affaires (chronologie, extraction de documents, classement,
résumé, recherche, vérification procédurale, contrôle de
cohérence, procès-verbal) — il ne prend parti pour aucune partie et
ne constitue pas un avis juridique.

Il ne propose à aucun moment d'aide à la rédaction d'une décision,
d'un raisonnement juridictionnel, ou d'une suggestion de solution.
Conformément à la Charte de déontologie des magistrats de l'ordre
judiciaire : « l'IA ne peut en aucun cas servir de fondement à une
décision de justice. »

Les informations saisies sont envoyées à l'API d'Anthropic (Claude)
pour être traitées. Avant toute utilisation sur une affaire réelle :

  • Assurez-vous que cette transmission est compatible avec votre
    obligation de discrétion professionnelle ou vos obligations
    déontologiques.
  • Limitez si nécessaire les données personnelles identifiantes
    avant de les saisir.

Cet outil est un prototype d'aide à l'organisation — toute
information extraite, classée ou synthétisée automatiquement doit
être vérifiée avant utilisation officielle.
════════════════════════════════════════════════════════════════════
"""


def _demander_consentement_greffier() -> bool:
    print(AVERTISSEMENT_GREFFIER)
    reponse = input("J'ai lu et je comprends ces informations — continuer ? (o/n) : ").strip().lower()
    return reponse == "o"


def cmd_chronologie(args):
    dossiers = db.list_dossiers()
    if not dossiers:
        print("Aucune affaire enregistrée.")
        return
    print("Affaires disponibles :")
    for d in dossiers:
        print(f"  {d['nom']} — {d['domaine'] or 'domaine non précisé'}")
    saisie = input("\nNom (ou numéro) de l'affaire : ").strip().lower()
    correspondances = [d for d in dossiers if saisie in d["nom"].lower() or (d["numero_dossier"] and saisie in d["numero_dossier"].lower())]
    if not correspondances:
        print(f"Aucune affaire ne correspond à « {saisie} ».")
        return
    if len(correspondances) > 1:
        print("Plusieurs affaires correspondent, soyez plus précis.")
        return
    dossier = correspondances[0]
    contexte = _construire_contexte_dossier(dossier)

    print("\nConstruction de la chronologie en cours...\n")
    chrono = construire_chronologie(contexte)

    print(f"📅 Période couverte : {chrono.get('periode_couverte', 'non déterminée')}\n")
    for ev in chrono.get("evenements", []):
        print(f"  {ev.get('date', '?')} — {ev.get('evenement', '')}")
    if chrono.get("elements_manquants"):
        print("\n⚠ Éléments manquants :")
        for e in chrono["elements_manquants"]:
            print(f"   - {e}")
    print()


def cmd_extraction_document(args):
    texte = _saisir_texte_ou_fichier("Collez le texte du document, ou importez un fichier.")
    if not texte:
        print("Aucun texte disponible.")
        return
    print("\nExtraction en cours...\n")
    elements = extraire_elements_cles(texte)
    for cle, libelle in [("dates", "Dates"), ("personnes_et_parties", "Personnes et parties"),
                          ("references", "Références"), ("demandes", "Demandes"), ("decisions", "Décisions")]:
        valeurs = elements.get(cle, [])
        print(f"{libelle} :")
        if valeurs:
            for v in valeurs:
                print(f"   • {v}")
        else:
            print("   (aucun élément identifié)")
        print()


def cmd_classement_document(args):
    texte = _saisir_texte_ou_fichier("Collez le texte du document, ou importez un fichier.")
    if not texte:
        print("Aucun texte disponible.")
        return
    print("\nClassement en cours...\n")
    resultat = classifier_document(texte)
    print(f"📂 Nature : {resultat.get('nature', 'autre')}")
    print(f"   Confiance : {resultat.get('confiance', 'Faible')}")
    print(f"   Justification : {resultat.get('justification', '')}\n")


def cmd_controle_coherence(args):
    print("Contrôle de cohérence entre plusieurs documents.")
    print("Fournissez au moins 2 documents à comparer (texte collé ou fichier).\n")

    documents = []
    while True:
        numero = len(documents) + 1
        print(f"--- Document {numero} ---")
        texte = _saisir_texte_ou_fichier(f"Document {numero}.")
        if not texte:
            if len(documents) < 2:
                print("Aucun texte fourni — au moins 2 documents sont nécessaires, réessayez.\n")
                continue
            break
        nom_document = input(f"Nom/référence pour ce document {numero} (ex. 'Assignation', 'Conclusions défendeur') : ").strip() or f"Document {numero}"

        print(f"Extraction des éléments clés de « {nom_document} » en cours...")
        try:
            elements = extraire_elements_cles(texte)
        except Exception as e:
            print(f"⚠ Erreur lors de l'extraction : {e}\n")
            continue
        documents.append({"nom_document": nom_document, "elements": elements})
        print(f"✓ Éléments extraits pour « {nom_document} ».\n")

        if len(documents) >= 2:
            suite = input("Ajouter un autre document ? (o/n, Entrée = non) : ").strip().lower()
            if suite != "o":
                break

    if len(documents) < 2:
        print("Au moins 2 documents sont nécessaires pour un contrôle de cohérence.")
        return

    print(f"\nComparaison de {len(documents)} documents en cours...\n")
    resultat = controler_coherence(documents)

    if resultat.get("contradictions"):
        print("⚠️ Contradictions détectées :")
        for c in resultat["contradictions"]:
            print(f"\n   [{c.get('gravite', '?')}] {c.get('sujet', '')}")
            print(f"      → {c.get('document_1', '')}")
            print(f"      → {c.get('document_2', '')}")
        print()
    else:
        print("✅ Aucune contradiction détectée entre les éléments extraits.\n")

    if resultat.get("elements_coherents"):
        print("Éléments cohérents entre documents :")
        for e in resultat["elements_coherents"]:
            print(f"   • {e}")
        print()

    if resultat.get("limites_analyse"):
        print(f"ℹ Limites de cette analyse : {resultat['limites_analyse']}\n")


def cmd_verification_procedurale(args):
    dossiers = db.list_dossiers()
    if not dossiers:
        print("Aucune affaire enregistrée.")
        return
    print("Affaires disponibles :")
    for d in dossiers:
        print(f"  {d['nom']} — {d['domaine'] or 'domaine non précisé'}")
    saisie = input("\nNom (ou numéro) de l'affaire : ").strip().lower()
    correspondances = [d for d in dossiers if saisie in d["nom"].lower() or (d["numero_dossier"] and saisie in d["numero_dossier"].lower())]
    if not correspondances:
        print(f"Aucune affaire ne correspond à « {saisie} ».")
        return
    if len(correspondances) > 1:
        print("Plusieurs affaires correspondent, soyez plus précis.")
        return
    dossier = correspondances[0]
    contexte = _construire_contexte_dossier(dossier)

    print("\nVérification procédurale en cours...\n")
    resultat = verifier_procedure(contexte)

    if resultat.get("echeances_identifiees"):
        print("📅 Échéances identifiées :")
        for ech in resultat["echeances_identifiees"]:
            print(f"   [{ech.get('statut', '?')}] {ech.get('echeance', '')} — {ech.get('date', 'date non précisée')}")
        print()

    if resultat.get("actes_potentiellement_manquants"):
        print("⚠ Actes potentiellement manquants :")
        for acte in resultat["actes_potentiellement_manquants"]:
            print(f"   • {acte}")
        print()

    if resultat.get("points_attention"):
        print("🔍 Points d'attention :")
        for p in resultat["points_attention"]:
            print(f"   - {p}")
        print()

    if not any([resultat.get("echeances_identifiees"), resultat.get("actes_potentiellement_manquants"), resultat.get("points_attention")]):
        print("Aucune échéance ni anomalie identifiée dans le contenu disponible.\n")


def cmd_pv_audience(args):
    print("Collez ou tapez vos notes prises pendant l'audience.")
    notes = _saisir_texte_ou_fichier("Notes d'audience.")
    if not notes:
        print("Aucune note fournie.")
        return

    print("\nRédaction de la première version du PV en cours...\n")
    pv = rediger_pv(notes)

    pv = _boucle_revision(pv, label="procès-verbal")

    choix_export = input("Exporter ce PV en Word ? (o/n) : ").strip().lower()
    if choix_export == "o":
        titre = input("Nom/référence pour ce PV (ex. 'PV audience 2026-01-15') : ").strip() or "PV audience"
        try:
            chemin = export.exporter_texte_libre_word(
                titre, pv,
                note_bas_page="Première version générée à partir de notes — à relire, compléter et signer par le greffier."
            )
            print(f"✅ PV créé : {chemin}")
        except Exception as e:
            print(f"Erreur lors de l'export : {e}")
    print()


def cmd_menu_greffier(args):
    if not _demander_consentement_greffier():
        print("\nUtilisation annulée. Retour à l'accueil.")
        return

    print("\n── ESPACE GREFFIER / MAGISTRAT ──\n")
    while True:
        print("  1. Chronologie automatique d'une affaire")
        print("  2. Extraction d'éléments clés d'un document")
        print("  3. Classement automatique d'un document")
        print("  4. Résumer une affaire")
        print("  5. Rechercher dans toutes les affaires")
        print("  6. Rédiger un procès-verbal à partir de notes")
        print("  7. Vérification procédurale (échéances, actes manquants)")
        print("  8. Contrôle de cohérence entre documents")
        print("  9. Retour à l'accueil")

        choix = input("\nVotre choix (1-9) : ").strip()

        try:
            if choix == "1":
                cmd_chronologie(args)
            elif choix == "2":
                cmd_extraction_document(args)
            elif choix == "3":
                cmd_classement_document(args)
            elif choix == "4":
                cmd_resumer_dossier(args)
            elif choix == "5":
                cmd_rechercher_transversal(args)
            elif choix == "6":
                cmd_pv_audience(args)
            elif choix == "7":
                cmd_verification_procedurale(args)
            elif choix == "8":
                cmd_controle_coherence(args)
            elif choix == "9":
                print()
                break
            else:
                print("\nChoix non reconnu, merci de taper un nombre entre 1 et 9.\n")
        except Exception as e:
            print(f"\n⚠ Une erreur est survenue pendant cette opération : {e}")
            print("Le programme continue normalement — vous pouvez réessayer ou choisir une autre option.\n")


def cmd_accueil(args):
    while True:
        print("Bienvenue. Quel espace souhaitez-vous utiliser ?\n")
        print("  1. Espace Avocat (préparation de plaidoirie, analyse d'arguments)")
        print("  2. Espace Greffier / Magistrat (chronologie, extraction, classement, PV...)")
        print("  3. Quitter")

        choix = input("\nVotre choix (1-3) : ").strip()
        if choix == "1":
            cmd_menu_avocat(args)
        elif choix == "2":
            cmd_menu_greffier(args)
        elif choix == "3":
            print("\nÀ bientôt !")
            break
        else:
            print("Choix non reconnu, merci de taper 1, 2 ou 3.")


def main():
    parser = argparse.ArgumentParser(description="Agent de préparation de plaidoirie")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init-db", help="Initialise la base de données").set_defaults(func=cmd_init_db)

    p_add = sub.add_parser("add-dossier", help="Créer un nouveau dossier")
    p_add.add_argument("--nom", required=True)
    p_add.add_argument("--domaine")
    p_add.add_argument("--parties")
    p_add.add_argument("--faits")
    p_add.set_defaults(func=cmd_add_dossier)

    sub.add_parser("list-dossiers", help="Lister les dossiers").set_defaults(func=cmd_list_dossiers)

    p_analyse = sub.add_parser("analyse", help="Analyser des conclusions adverses")
    p_analyse.add_argument("--dossier-id", type=int, required=True)
    p_analyse.add_argument("--fichier", help="Chemin vers un fichier .pdf, .docx ou .txt")
    p_analyse.add_argument("--texte", help="Texte collé directement")
    p_analyse.add_argument(
        "--recherche-live", nargs="?", const=True, default=False,
        help="Interroge Légifrance/Judilibre en direct. Optionnel : mots-clés précis (sinon domaine/nom du dossier)."
    )
    p_analyse.set_defaults(func=cmd_analyse)

    p_show = sub.add_parser("show-analyses", help="Afficher les analyses d'un dossier")
    p_show.add_argument("--dossier-id", type=int, required=True)
    p_show.set_defaults(func=cmd_show_analyses)

    p_collecte = sub.add_parser("collecte-jurisprudence", help="Collecter de la jurisprudence depuis Judilibre")
    p_collecte.add_argument("--query", required=True, help="Mots-clés de recherche")
    p_collecte.add_argument("--domaine", help="Domaine associé (prud'hommes, pénal...)")
    p_collecte.add_argument("--max", type=int, default=10, help="Nombre max de décisions à collecter")
    p_collecte.set_defaults(func=cmd_collecte_jurisprudence)

    p_listjuris = sub.add_parser("list-jurisprudence", help="Lister la jurisprudence en base")
    p_listjuris.add_argument("--statut", choices=["attente", "validee"], default="attente")
    p_listjuris.add_argument("--domaine")
    p_listjuris.set_defaults(func=cmd_list_jurisprudence)

    p_valider = sub.add_parser("valider-jurisprudence", help="Valider une référence collectée")
    p_valider.add_argument("--id", type=int, required=True)
    p_valider.set_defaults(func=cmd_valider_jurisprudence)

    p_rejeter = sub.add_parser("rejeter-jurisprudence", help="Rejeter/supprimer une référence non pertinente")
    p_rejeter.add_argument("--id", type=int, required=True)
    p_rejeter.set_defaults(func=cmd_rejeter_jurisprudence)

    sub.add_parser("analyse-interactif", help="Analyser un dossier en mode guidé, sans arguments à taper").set_defaults(func=cmd_analyse_interactif)

    args = parser.parse_args()
    if args.command is None:
        cmd_accueil(args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
