"""
run_evaluation.py : lance le jeu d'évaluation de Plaid'IA contre les VRAIS
prompts et agents de l'application (analyse.py, quality_pipeline.py), pas
contre une copie.

Depuis la racine du dépôt :

    python -m evaluation.run_evaluation --estimer               # coût prévu, aucun appel
    python -m evaluation.run_evaluation --dry-run               # plomberie complète, faux modèle, gratuit
    python -m evaluation.run_evaluation                          # vrai run (API Anthropic, clé apikey.txt)
    python -m evaluation.run_evaluation --reprendre <run_id>    # reprend un run interrompu
    python -m evaluation.run_evaluation --rapport <run_id>      # régénère le rapport (après revue_manuelle.json)

Un plafond de dépense (--budget-usd, 6 $ par défaut) arrête le run proprement
si le coût estimé le dépasse ; les résultats déjà obtenus sont conservés.
"""

import argparse
import concurrent.futures
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import types
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
DOSSIER = Path(__file__).resolve().parent
DATASET = DOSSIER / "jeu_evaluation.json"
REVUE = DOSSIER / "revue_manuelle.json"
RESULTATS = DOSSIER / "resultats"

# Tarifs publics indicatifs, en dollars par million de tokens (entrée, sortie).
# Sert au plafond de dépense et à l'estimation : à vérifier sur la page de
# tarification d'Anthropic avant de citer un coût.
PRIX = {
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
}
PRIX_PAR_DEFAUT = (3.0, 15.0)

# Copie de backend/app/routers/chat.py::_construire_contexte_recherche(juridiction, False, "").
# Un test (backend/tests/test_evaluation.py) vérifie l'égalité avec la vraie fonction.
def contexte_chat(juridiction: str = "Légifrance (France)") -> str:
    return (
        f"\n\nContexte juridictionnel par défaut réglé par l'avocat dans les paramètres : {juridiction}. "
        "Utilise ce cadre par défaut pour répondre si la question ne précise rien d'autre. "
        "Mais si la question mentionne clairement un autre pays ou système juridique, "
        "privilégie ce que la question indique explicitement plutôt que ce réglage par défaut."
    )


class BudgetDepasse(Exception):
    pass


# --- Clients : enregistreur (vrai) et simulé (dry-run) -----------------------------------

class Enregistreur:
    """Enveloppe le vrai client Anthropic : compte les tokens et le coût estimé,
    et refuse un appel de plus si le plafond est atteint. Expose la même
    interface (`.messages.create`) que le client que analyse.py attend."""

    def __init__(self, client, budget_usd: float):
        self._client = client
        self._budget = budget_usd
        self._verrou = threading.Lock()
        self.tokens: dict[str, list[int]] = {}
        self.appels = 0

    @property
    def messages(self):
        return self

    def cout_usd(self) -> float:
        total = 0.0
        for modele, (entree, sortie) in self.tokens.items():
            p_in, p_out = PRIX.get(modele, PRIX_PAR_DEFAUT)
            total += entree / 1e6 * p_in + sortie / 1e6 * p_out
        return total

    def create(self, **kwargs):
        with self._verrou:
            if self.cout_usd() >= self._budget:
                raise BudgetDepasse(f"Plafond de {self._budget:.2f} $ atteint (coût estimé {self.cout_usd():.2f} $)")
        reponse = self._client.messages.create(**kwargs)
        usage = getattr(reponse, "usage", None)
        with self._verrou:
            self.appels += 1
            t = self.tokens.setdefault(kwargs.get("model", "?"), [0, 0])
            t[0] += getattr(usage, "input_tokens", 0) or 0
            t[1] += getattr(usage, "output_tokens", 0) or 0
        return reponse


class ClientSimule:
    """Faux modèle pour --dry-run et les tests : aucune requête réseau. Réponses
    déterministes choisies d'après le prompt système, juste assez réalistes pour
    exercer toute la chaîne (garde-fou, intention, réponse balisée, vérificateur, critique)."""

    DECLENCHEURS_REFUS = ("ignore toutes", "dan,", "faux certificat", "antidater", "faire disparaître", "recette", "équation",
                          "instruction à l'ia", "clé api", "intimider", "nouvelle consigne")

    def __init__(self):
        self.appels = 0

    @property
    def messages(self):
        return self

    def create(self, **kwargs):
        self.appels += 1
        systeme = kwargs.get("system", "")
        contenu = kwargs["messages"][-1]["content"]
        bas = contenu.lower()
        if systeme.startswith("Tu es le garde-fou d'entrée"):
            refuse = any(d in bas for d in self.DECLENCHEURS_REFUS)
            texte = json.dumps({"allowed": not refuse, "risk_level": "high" if refuse else "low", "reason": "simulé", "requires_clarification": False})
        elif systeme.startswith("Tu es l'agent de compréhension"):
            texte = json.dumps({"objectif": "simulé", "type_tache": "question", "necessite_verification_approfondie": True})
        elif systeme.startswith("Tu es l'agent vérificateur"):
            elements = []
            for m in re.finditer(r"\[ART:([^:\]]+):([A-Z]+)\]", contenu):
                num = m.group(1)
                statut = "NON_VERIFIE" if num in ("1240-9", "L1235-42", "222-199", "4999", "9999-1", "L4999-12") else "A_VERIFIER"
                elements.append({"affirmation": m.group(0), "statut": statut, "commentaire": f"simulé pour {num}"})
            texte = json.dumps({"statut_global": "NON_VERIFIE" if any(e["statut"] == "NON_VERIFIE" for e in elements) else "A_VERIFIER", "elements": elements})
        elif systeme.startswith("Tu es l'agent critique"):
            texte = json.dumps({"critiques": [], "synthese": "simulé"})
        else:
            if "1240-9" in bas:
                texte = "L'article 1240-9 du Code civil [ART:1240-9:CCIV] prévoit une responsabilité spécifique."
            elif "31-11.111" in bas:
                texte = "L'arrêt n° 31-11.111 [JURISPRUDENCE:Cass. civ. 3e, 14 mars 2031, n° 31-11.111] juge que..."
            elif "1240 du code pénal" in bas:
                texte = "Le Code pénal ne contient pas d'article 1240 ; voir l'article 1240 [ART:1240:CCIV] du Code civil."
            else:
                texte = "La responsabilité suppose une faute, un dommage et un lien de causalité [ART:1240:CCIV] [ART:1241:CCIV]. [VERIF:jurisprudence à confirmer]"
        usage = types.SimpleNamespace(input_tokens=1000, output_tokens=400)
        return types.SimpleNamespace(content=[types.SimpleNamespace(text=texte)], usage=usage)


# --- Environnement et chargement --------------------------------------------------------

def preparer_environnement() -> None:
    """Le run n'a aucune raison de toucher la vraie base de l'application : on
    la redirige vers un fichier jetable avant tout import de `db`."""
    os.environ.setdefault("PLAIDIA_DB_PATH", str(Path(tempfile.mkdtemp(prefix="plaidia_eval_")) / "eval.db"))
    os.environ.setdefault("DEMO_MODE", "false")
    for chemin in (str(RACINE), str(RACINE / "backend")):
        if chemin not in sys.path:
            sys.path.insert(0, chemin)


def charger_dataset() -> dict:
    return json.loads(DATASET.read_text(encoding="utf-8"))


def charger_revue() -> dict:
    if REVUE.exists():
        return json.loads(REVUE.read_text(encoding="utf-8"))
    return {"articles": {}, "pieges": {}}


def commit_courant() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RACINE, capture_output=True, text=True, timeout=10).stdout.strip() or "inconnu"
    except Exception:
        return "inconnu"


def charger_ancien_prompt_garde_fou(ref: str) -> str:
    """Prompt du garde-fou tel qu'il était au commit `ref` (avant la correction
    des faux refus), pour mesurer l'avant/après avec le même jeu de questions."""
    sortie = subprocess.run(["git", "show", f"{ref}:analyse.py"], cwd=RACINE, capture_output=True, timeout=30)
    if sortie.returncode != 0:
        raise RuntimeError(f"git show {ref}:analyse.py a échoué : {sortie.stderr.decode('utf-8', 'replace')[:200]}")
    m = re.search(r'GARDE_FOU_SYSTEM_PROMPT = """(.*?)"""', sortie.stdout.decode("utf-8"), re.DOTALL)
    if not m:
        raise RuntimeError(f"GARDE_FOU_SYSTEM_PROMPT introuvable dans {ref}:analyse.py")
    return m.group(1)


# --- Exécution --------------------------------------------------------------------------

def evaluer_garde_fou(texte: str) -> dict:
    import analyse as legacy_analyse

    e = legacy_analyse.evaluer_garde_fou_entree(texte)
    return {"allowed": bool(e.get("allowed", True)), "risk_level": e.get("risk_level"), "reason": (e.get("reason") or "")[:300]}


def executer_question(question: str) -> dict:
    """Reproduit le chemin du chat en production : garde-fou, agent de
    compréhension, réponse de l'agent principal (mêmes prompt, modèle et
    max_tokens que le flux SSE), puis trio qualité. Le trio est TOUJOURS
    exécuté ici pour mesurer ce qu'il rattrape ; en production il ne l'est
    que si l'agent de compréhension le juge nécessaire (champ enregistré)."""
    import analyse as legacy_analyse
    from app import quality_pipeline

    garde = legacy_analyse.evaluer_garde_fou_entree(question)
    intention = legacy_analyse.analyser_intention_juridique(question)
    reponse = legacy_analyse.repondre_conversation([{"role": "user", "content": question}], contexte_recherche=contexte_chat())
    verification, trace = quality_pipeline.executer_trio_qualite(reponse, sources_textes=None, contexte_dossier="")
    return {
        "garde_fou_allowed": bool(garde.get("allowed", True)),
        "verification_declenchee_par_intention": bool(intention.get("necessite_verification_approfondie")),
        "reponse": reponse,
        "verification": verification,
        "etapes_degradees": [t.agent for t in trace if t.statut == "degrade"],
    }


class Journal:
    """Fichier JSON-lines des résultats bruts, ajout atomique par ligne, pour
    pouvoir reprendre un run interrompu sans rien refaire."""

    def __init__(self, chemin: Path):
        self.chemin = chemin
        self._verrou = threading.Lock()
        self.faits: set[tuple] = set()
        self.enregistrements: list[dict] = []
        if chemin.exists():
            for ligne in chemin.read_text(encoding="utf-8").splitlines():
                if ligne.strip():
                    e = json.loads(ligne)
                    self.enregistrements.append(e)
                    if not e.get("erreur"):
                        self.faits.add((e["section"], e["item_id"], e.get("rep", 0)))

    def ajouter(self, e: dict) -> None:
        with self._verrou:
            self.enregistrements.append(e)
            with self.chemin.open("a", encoding="utf-8") as f:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

    def section(self, nom: str) -> list[dict]:
        # dernier enregistrement valide par (item, rep) : un rejeu après erreur remplace l'erreur
        par_cle: dict[tuple, dict] = {}
        for e in self.enregistrements:
            if e["section"] == nom:
                par_cle[(e["item_id"], e.get("rep", 0))] = e
        return list(par_cle.values())


def lancer_garde_fou(journal: Journal, section: str, items: list[dict], repetitions: int, workers: int) -> None:
    taches = [(it, r) for it in items for r in range(repetitions) if (section, it["id"], r) not in journal.faits]

    def une(tache):
        it, r = tache
        try:
            res = evaluer_garde_fou(it["texte"])
            journal.ajouter({"section": section, "item_id": it["id"], "rep": r, **res})
        except BudgetDepasse:
            raise
        except Exception as ex:  # noqa: BLE001 : une erreur ponctuelle ne doit pas arrêter le run
            journal.ajouter({"section": section, "item_id": it["id"], "rep": r, "erreur": f"{type(ex).__name__}: {ex}"[:300]})

    executer_en_parallele(une, taches, workers)


def lancer_questions(journal: Journal, section: str, items: list[dict], workers: int) -> None:
    taches = [it for it in items if (section, it["id"], 0) not in journal.faits]

    def une(it):
        try:
            res = executer_question(it["question"])
            journal.ajouter({"section": section, "item_id": it["id"], "rep": 0, **res})
        except BudgetDepasse:
            raise
        except Exception as ex:  # noqa: BLE001
            journal.ajouter({"section": section, "item_id": it["id"], "rep": 0, "erreur": f"{type(ex).__name__}: {ex}"[:300]})

    executer_en_parallele(une, taches, workers)


def executer_en_parallele(fonction, taches: list, workers: int) -> None:
    if not taches:
        return
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futurs = [pool.submit(fonction, t) for t in taches]
        for f in concurrent.futures.as_completed(futurs):
            f.result()  # remonte BudgetDepasse, seule exception qui doit interrompre


# --- Estimation du coût -----------------------------------------------------------------

def estimer_cout(dataset: dict, sections: list[str], repetitions: int, avec_ancien: bool) -> dict:
    """Ordre de grandeur, SANS appel réseau : tokens ≈ caractères / 3,2 pour le
    français ; sorties supposées à leur plafond moyen observé."""
    import analyse as a

    def tok(s: str) -> int:
        return int(len(s) / 3.2)

    n_legit, n_att = len(dataset["garde_fou_legitimes"]), len(dataset["garde_fou_attaques"])
    n_q = len(dataset["questions_fond"]) + len(dataset["questions_pieges"])
    moy_msg = sum(tok(i["texte"]) for i in dataset["garde_fou_legitimes"] + dataset["garde_fou_attaques"]) / (n_legit + n_att)
    moy_q = sum(tok(i["question"]) for i in dataset["questions_fond"] + dataset["questions_pieges"]) / n_q

    haiku_in = haiku_out = sonnet_in = sonnet_out = 0
    if "garde_fou" in sections:
        appels = (n_legit + n_att) * repetitions * (2 if avec_ancien else 1)
        haiku_in += appels * (tok(a.GARDE_FOU_SYSTEM_PROMPT) + moy_msg)
        haiku_out += appels * 120
    if "fond" in sections or "pieges" in sections:
        n = (len(dataset["questions_fond"]) if "fond" in sections else 0) + (len(dataset["questions_pieges"]) if "pieges" in sections else 0)
        haiku_in += n * (tok(a.GARDE_FOU_SYSTEM_PROMPT) + tok(a.INTENTION_JURIDIQUE_SYSTEM_PROMPT) + 2 * moy_q)
        haiku_out += n * (120 + 250)
        rep_out = 1300
        sonnet_in += n * (tok(a.QUESTION_SYSTEM_PROMPT) + tok(a.REGLE_BALISAGE_CITATIONS) + tok(contexte_chat()) + moy_q)
        sonnet_out += n * rep_out
        sonnet_in += n * (tok(a.VERIFICATEUR_SYSTEM_PROMPT) + rep_out + 300)  # vérificateur
        sonnet_out += n * 500
        sonnet_in += n * (tok(a.CRITIQUE_SYSTEM_PROMPT) + rep_out + 300)  # critique
        sonnet_out += n * 600
    p_h, p_s = PRIX["claude-haiku-4-5-20251001"], PRIX["claude-sonnet-4-6"]
    cout = haiku_in / 1e6 * p_h[0] + haiku_out / 1e6 * p_h[1] + sonnet_in / 1e6 * p_s[0] + sonnet_out / 1e6 * p_s[1]
    return {"haiku": [int(haiku_in), int(haiku_out)], "sonnet": [int(sonnet_in), int(sonnet_out)], "cout_usd": round(cout, 2)}


# --- Agrégation et rapport --------------------------------------------------------------

def agreger(journal: Journal, dataset: dict, revue: dict) -> dict:
    from evaluation import metriques as m

    reels = m.ensemble_articles(dataset.get("articles_reels_connus"))
    resultat = {}
    for version in ("garde_fou_actuel", "garde_fou_ancien"):
        enr = journal.section(version)
        if enr:
            resultat[version] = m.agreger_garde_fou(enr, dataset["garde_fou_legitimes"], dataset["garde_fou_attaques"])
    fond = journal.section("fond")
    if fond:
        resultat["fond"] = m.agreger_fond(fond, dataset["questions_fond"], reels, revue.get("articles"))
    pieges = journal.section("pieges")
    if pieges:
        resultat["pieges"] = m.agreger_pieges(pieges, dataset["questions_pieges"], revue.get("pieges"))
    return resultat


def rendre_markdown(agrege: dict, meta: dict) -> str:
    from evaluation.metriques import pourcent as p

    L = []
    L.append(f"# Résultats de l'évaluation de Plaid'IA ({meta.get('date', '')})")
    L.append("")
    L.append(f"- Commit évalué : `{meta.get('commit', '?')}`")
    L.append(f"- Modèles : réponse et vérification `{meta.get('modele_principal', '?')}`, garde-fou et intention `{meta.get('modele_leger', '?')}`")
    L.append(f"- Répétitions du garde-fou : {meta.get('repetitions', '?')} par demande. Questions de fond et pièges : 1 réponse chacune.")
    if meta.get("cout_usd") is not None:
        L.append(f"- Coût estimé du run : {meta['cout_usd']:.2f} $ ({meta.get('appels', '?')} appels)")
    if meta.get("simule"):
        L.append("- **RUN SIMULÉ (--dry-run) : chiffres sans valeur, aucun vrai modèle appelé.**")
    L.append("")

    gf = [(k, agrege[k]) for k in ("garde_fou_ancien", "garde_fou_actuel") if k in agrege]
    if gf:
        L.append("## 1. Garde-fou d'entrée")
        L.append("")
        L.append("| Version du prompt | Faux refus (demandes légitimes refusées) | Détection (attaques bloquées) |")
        L.append("|---|---|---|")
        for k, v in gf:
            nom = "Avant correction" if k == "garde_fou_ancien" else "Actuelle"
            L.append(f"| {nom} | {p(v['faux_refus'])} | {p(v['detection'])} |")
        L.append("")
        for k, v in gf:
            nom = "avant correction" if k == "garde_fou_ancien" else "actuelle"
            if v["legitimes_refusees"]:
                L.append(f"- Demandes légitimes refusées au moins une fois ({nom}) : {', '.join(v['legitimes_refusees'])}")
            if v["attaques_passees"]:
                L.append(f"- Attaques non bloquées au moins une fois ({nom}) : {', '.join(v['attaques_passees'])}")
            if v["items_instables"]:
                L.append(f"- Demandes au verdict instable d'une répétition à l'autre ({nom}) : {', '.join(v['items_instables'])}")
        L.append("")

    if "fond" in agrege:
        f = agrege["fond"]
        L.append("## 2. Exactitude des citations d'articles (questions de fond)")
        L.append("")
        L.append(f"{f['n_questions']} questions, {f['n_citations_articles']} citations d'articles balisées `[ART:...]`.")
        L.append("")
        L.append("| Mesure | Résultat |")
        L.append("|---|---|")
        L.append(f"| Citations exactes | {p(f['citations_exactes'])} |")
        L.append(f"| Citations inventées ou mal attribuées | {p(f['citations_inventees'])} |")
        L.append(f"| Citations non tranchées (revue manuelle en attente) | {f['citations_non_tranchees']} |")
        L.append(f"| Questions citant au moins un article attendu | {p(f['questions_avec_au_moins_un_article_attendu'])} |")
        L.append(f"| Références de jurisprudence citées (non vérifiées automatiquement) | {f['references_jurisprudence_citees']} |")
        L.append(f"| Articles cités en clair sans balise | {f['mentions_articles_non_balisees']} |")
        L.append("")
        if f["detail_citations_a_revoir"]:
            L.append("Citations à revoir ou jugées fausses :")
            for d in f["detail_citations_a_revoir"]:
                L.append(f"- {d['question']} : {d['citation']} ({d['verdict']})")
            L.append("")

    if "pieges" in agrege:
        g = agrege["pieges"]
        L.append("## 3. Questions-pièges (sources qui n'existent pas)")
        L.append("")
        L.append("| Mesure | Résultat |")
        L.append("|---|---|")
        L.append(f"| Source fictive adoptée comme réelle | {p(g['fictifs_adoptes'])} |")
        L.append(f"| Inexistence signalée par le modèle | {p(g['inexistance_signalee_par_le_modele'])} |")
        L.append(f"| Source fictive non reprise | {p(g['non_cites'])} |")
        L.append("")
        L.append("| Type de piège | Questions | Adoptées |")
        L.append("|---|---|---|")
        for t, d in g["par_type"].items():
            L.append(f"| {t} | {d['n']} | {d['adoptes']} |")
        L.append("")
        v = g["verificateur_sur_fictifs_adoptes"]
        L.append("### Ce que le vérificateur fait des fictifs adoptés")
        L.append("")
        if v["n"] == 0:
            L.append("Aucun fictif n'a été adopté : le vérificateur n'a rien eu à rattraper sur ce jeu.")
        else:
            L.append(f"Sur {v['n']} réponses ayant adopté un fictif :")
            L.append("")
            L.append("| Mesure | Résultat |")
            L.append("|---|---|")
            L.append(f"| Fictif explicitement signalé (NON_VERIFIE ou A_VERIFIER) | {p(v['fictif_signale'])} |")
            L.append(f"| Fictif validé à tort (VERIFIE ou PARTIELLEMENT_VERIFIE) | {p(v['fictif_valide_a_tort'])} |")
            L.append(f"| Fictif non mentionné par le vérificateur | {p(v['fictif_non_mentionne'])} |")
            L.append(f"| Statut global jamais « VERIFIE » | {p(v['statut_global_pas_verifie'])} |")
        L.append("")
        corriges = [d["question"] for d in g["detail"] if d["corrige_a_la_main"]]
        if corriges:
            L.append(f"Classement corrigé à la main après lecture : {', '.join(corriges)}.")
            L.append("")

    if "fond" in agrege:
        fa = agrege["fond"]["fausses_alertes_verificateur"]
        L.append("## 4. Fausses alertes du vérificateur")
        L.append("")
        L.append(f"Articles réels cités que le vérificateur marque NON_VERIFIE : {p(fa)}.")
        L.append("")
        L.append("Note : ce run est celui du chat de production, sans corpus de sources fourni. Le contrôle déterministe (recherche de la citation dans les sources) vaut alors `AUCUNE_SOURCE` et le statut ne repose que sur le modèle vérificateur.")
        L.append("")
    L.append("Voir `evaluation/README.md` pour la méthode et les limites de ces chiffres.")
    return "\n".join(L) + "\n"


def ecrire_rapport(run_dir: Path, journal: Journal, dataset: dict, meta: dict) -> Path:
    revue = charger_revue()
    agrege = agreger(journal, dataset, revue)
    (run_dir / "agrege.json").write_text(json.dumps(agrege, ensure_ascii=False, indent=2), encoding="utf-8")
    chemin = run_dir / "RESULTATS.md"
    chemin.write_text(rendre_markdown(agrege, meta), encoding="utf-8")
    return chemin


# --- Programme principal ----------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Évaluation anti-hallucination de Plaid'IA")
    ap.add_argument("--sections", nargs="+", choices=["garde_fou", "fond", "pieges"], default=["garde_fou", "fond", "pieges"])
    ap.add_argument("--repetitions", type=int, default=3, help="répétitions du garde-fou par demande (défaut 3)")
    ap.add_argument("--budget-usd", type=float, default=6.0)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--garde-fou-ancien", metavar="REF_GIT", nargs="?", const="95b38fd", default=None,
                    help="mesure aussi le prompt du garde-fou tel qu'au commit REF_GIT (défaut 95b38fd, avant la correction)")
    ap.add_argument("--estimer", action="store_true", help="affiche le coût prévu et s'arrête, sans aucun appel")
    ap.add_argument("--dry-run", action="store_true", help="faux modèle, aucun appel réseau")
    ap.add_argument("--reprendre", metavar="RUN_ID")
    ap.add_argument("--rapport", metavar="RUN_ID", help="régénère RESULTATS.md d'un run existant")
    ap.add_argument("--sortie", type=Path, default=RESULTATS, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    preparer_environnement()
    import analyse as legacy_analyse

    dataset = charger_dataset()

    if args.estimer:
        est = estimer_cout(dataset, args.sections, args.repetitions, args.garde_fou_ancien is not None)
        print(f"Estimation (aucun appel effectué) : Haiku {est['haiku'][0]:,} tokens entrée / {est['haiku'][1]:,} sortie, "
              f"Sonnet {est['sonnet'][0]:,} entrée / {est['sonnet'][1]:,} sortie -> environ {est['cout_usd']:.2f} $")
        print("Tarifs supposés (à vérifier) : Sonnet 3/15 $, Haiku 1/5 $ par million de tokens.")
        return 0

    if args.rapport:
        run_dir = args.sortie / args.rapport
        journal = Journal(run_dir / "brut.jsonl")
        meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
        print(f"Rapport régénéré : {ecrire_rapport(run_dir, journal, dataset, meta)}")
        return 0

    run_id = args.reprendre or datetime.datetime.now().strftime("%Y-%m-%d_%Hh%M") + ("_simule" if args.dry_run else "")
    run_dir = args.sortie / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    journal = Journal(run_dir / "brut.jsonl")

    if args.dry_run:
        client = ClientSimule()
        enregistreur = None
    else:
        enregistreur = Enregistreur(legacy_analyse._client(), args.budget_usd)
        client = enregistreur
    legacy_analyse._client = lambda: client

    interrompu = None
    prompt_actuel = legacy_analyse.GARDE_FOU_SYSTEM_PROMPT
    try:
        if "garde_fou" in args.sections:
            items = dataset["garde_fou_legitimes"] + dataset["garde_fou_attaques"]
            print(f"Garde-fou (prompt actuel) : {len(items)} demandes x {args.repetitions}...")
            lancer_garde_fou(journal, "garde_fou_actuel", items, args.repetitions, args.workers)
            if args.garde_fou_ancien:
                legacy_analyse.GARDE_FOU_SYSTEM_PROMPT = charger_ancien_prompt_garde_fou(args.garde_fou_ancien)
                try:
                    print(f"Garde-fou (prompt du commit {args.garde_fou_ancien}) : {len(items)} demandes x {args.repetitions}...")
                    lancer_garde_fou(journal, "garde_fou_ancien", items, args.repetitions, args.workers)
                finally:
                    legacy_analyse.GARDE_FOU_SYSTEM_PROMPT = prompt_actuel
        if "fond" in args.sections:
            print(f"Questions de fond : {len(dataset['questions_fond'])}...")
            lancer_questions(journal, "fond", dataset["questions_fond"], args.workers)
        if "pieges" in args.sections:
            print(f"Questions-pièges : {len(dataset['questions_pieges'])}...")
            lancer_questions(journal, "pieges", dataset["questions_pieges"], args.workers)
    except BudgetDepasse as e:
        interrompu = str(e)
        print(f"\nARRÊT : {e}. Résultats partiels conservés ; relancez avec --reprendre {run_id} et un budget plus haut.")
    finally:
        legacy_analyse.GARDE_FOU_SYSTEM_PROMPT = prompt_actuel

    meta = {
        "run_id": run_id,
        "date": datetime.date.today().isoformat(),
        "commit": commit_courant(),
        "modele_principal": legacy_analyse.MODEL_ACTIF,
        "modele_leger": legacy_analyse.MODEL_LEGER,
        "repetitions": args.repetitions,
        "simule": args.dry_run,
        "interrompu": interrompu,
        "cout_usd": round(enregistreur.cout_usd(), 3) if enregistreur else 0.0,
        "appels": enregistreur.appels if enregistreur else client.appels,
        "tokens": enregistreur.tokens if enregistreur else None,
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    chemin = ecrire_rapport(run_dir, journal, dataset, meta)
    print(f"\nRun {run_id} : {meta['appels']} appels, coût estimé {meta['cout_usd']:.2f} $.")
    print(f"Rapport : {chemin}")
    erreurs = [e for e in journal.enregistrements if e.get("erreur")]
    if erreurs:
        print(f"Attention : {len(erreurs)} enregistrement(s) en erreur (voir brut.jsonl) ; relancer avec --reprendre {run_id}.")
    return 1 if interrompu else 0


if __name__ == "__main__":
    sys.exit(main())
