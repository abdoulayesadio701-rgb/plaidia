"""
gui.py — Interface graphique de Plaid'IA (tkinter, inclus avec Python).

Couvre le cœur essentiel de l'outil : dossiers, analyse des conclusions
adverses, résumé, plan de plaidoirie, simulateur d'objections, notes,
et questions libres — avec de vrais boutons, sans commande à taper.

Lancement : python gui.py
"""

import re
import sys
import threading
import time
import uuid
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog

import db
import analyse
from analyse import interpreter_intention

# ---------- Balisage des références juridiques (voir analyse.REGLE_BALISAGE_CITATIONS) --
# Remplace l'ancien marqueur libre "À VÉRIFIER : " -- même jeu de regex que
# backend/app/quality_pipeline.py et export.py, dupliqué ici plutôt
# qu'importé : gui.py est l'application standalone historique, elle ne
# dépend jamais de backend/app (voir backend/README.md).
_RE_TAG_ART = re.compile(r"\[ART:([^:\]]+):([A-Z]+)\]")
_RE_TAG_JURISPRUDENCE = re.compile(r"\[JURISPRUDENCE:([^\]]+)\]")
_RE_TAG_VERIF = re.compile(r"\[VERIF:([^\]]*)\]")
_RE_TAG_TOUTE = re.compile(r"\[(?:ART|JURISPRUDENCE|VERIF):[^\]]*\]")
_CODES_LIBELLES = {
    "CP": "Code pénal", "CCIV": "Code civil", "CPC": "Code de procédure civile",
    "CPP": "Code de procédure pénale", "CTRAV": "Code du travail", "CCOM": "Code de commerce",
}

# ---------- Palette et polices ----------
NAVY = "#1F3A5F"
NAVY_DARK = "#152A47"
GOLD = "#B8860B"
LIGHT_BG = "#F5F6F8"
WHITE = "#FFFFFF"
TEXT = "#1A1A1A"
GRAY = "#6B7280"

FONT_BASE = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_BTN = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 10)


class DialogueTexteLong(tk.Toplevel):
    """Fenêtre modale pour saisir un texte long (conclusions, notes...),
    car les boîtes de dialogue standard de tkinter ne gèrent qu'une ligne.

    Propose aussi d'importer directement un fichier (PDF, Word, Excel,
    image, texte) plutôt que de devoir copier-coller à la main — le texte
    extrait vient remplir la même zone de saisie."""

    def __init__(self, parent, titre, consigne):
        super().__init__(parent)
        self.title(titre)
        self.geometry("640x460")
        self.configure(bg=WHITE)
        self.resultat = None
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text=consigne, font=FONT_BASE, bg=WHITE, wraplength=600, justify="left").pack(
            padx=16, pady=(16, 4), anchor="w"
        )

        zone_import = tk.Frame(self, bg=WHITE)
        zone_import.pack(fill="x", padx=16, pady=(0, 8))
        tk.Button(
            zone_import, text="📁 Importer un fichier (PDF, Word, Excel, image...)",
            command=self._importer_fichier, font=("Segoe UI", 9), bg=LIGHT_BG, fg=TEXT, relief="flat", padx=10, pady=4,
        ).pack(side="left")
        self.label_fichier_importe = tk.Label(zone_import, text="", font=("Segoe UI", 9), bg=WHITE, fg=GRAY)
        self.label_fichier_importe.pack(side="left", padx=(10, 0))

        self.zone_texte = scrolledtext.ScrolledText(self, wrap="word", font=FONT_BASE, height=15)
        self.zone_texte.pack(fill="both", expand=True, padx=16, pady=8)
        self.zone_texte.focus_set()

        boutons = tk.Frame(self, bg=WHITE)
        boutons.pack(fill="x", padx=16, pady=(0, 16))

        tk.Button(boutons, text="Annuler", command=self._annuler, font=FONT_BTN).pack(side="right", padx=(8, 0))
        tk.Button(
            boutons, text="Valider", command=self._valider, font=FONT_BTN,
            bg=GOLD, fg="white", activebackground="#9A6F09", activeforeground="white",
        ).pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._annuler)

    def _importer_fichier(self):
        from tkinter import filedialog
        import extract as extract_module

        chemin = filedialog.askopenfilename(
            title="Choisir un fichier à importer",
            filetypes=[("Documents", "*.pdf *.docx *.xlsx *.xls *.txt *.png *.jpg *.jpeg *.webp"), ("Tous les fichiers", "*.*")],
        )
        if not chemin:
            return
        try:
            texte_extrait = extract_module.extract_text(chemin)
        except Exception as e:
            messagebox.showerror("Erreur d'import", str(e))
            return

        nom_fichier = chemin.split("/")[-1].split("\\")[-1]
        contenu_actuel = self.zone_texte.get("1.0", "end").strip()
        if contenu_actuel:
            remplacer = messagebox.askyesnocancel(
                "Texte déjà présent",
                "Il y a déjà du texte dans la zone de saisie.\n\n"
                "Oui = remplacer par le contenu du fichier\n"
                "Non = ajouter à la suite\n"
                "Annuler = ne rien faire",
            )
            if remplacer is None:
                return
            if remplacer:
                self.zone_texte.delete("1.0", "end")
                self.zone_texte.insert("1.0", texte_extrait)
            else:
                self.zone_texte.insert("end", "\n\n" + texte_extrait)
        else:
            self.zone_texte.insert("1.0", texte_extrait)

        self.label_fichier_importe.config(text=f"✓ {nom_fichier} importé")

    def _valider(self):
        self.resultat = self.zone_texte.get("1.0", "end").strip()
        self.destroy()

    def _annuler(self):
        self.resultat = None
        self.destroy()


class DialogueNouveauDossier(tk.Toplevel):
    """Fenêtre modale de création de dossier — nom, domaine, faits."""

    DOMAINES = [
        "Prud'hommes", "Pénal", "Civil", "Commercial", "Bail commercial",
        "Famille / Divorce", "Administratif", "Social", "Immobilier", "Autre",
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Nouveau dossier")
        self.geometry("480x420")
        self.configure(bg=WHITE)
        self.resultat = None
        self.transient(parent)
        self.grab_set()

        pad = {"padx": 16, "pady": (12, 4)}

        tk.Label(self, text="Nom du dossier", font=FONT_BASE, bg=WHITE).pack(anchor="w", **pad)
        self.entree_nom = tk.Entry(self, font=FONT_BASE)
        self.entree_nom.pack(fill="x", padx=16)
        self.entree_nom.focus_set()

        tk.Label(self, text="Numéro de référence (optionnel)", font=FONT_BASE, bg=WHITE).pack(anchor="w", **pad)
        self.entree_numero = tk.Entry(self, font=FONT_BASE)
        self.entree_numero.pack(fill="x", padx=16)

        tk.Label(self, text="Domaine", font=FONT_BASE, bg=WHITE).pack(anchor="w", **pad)
        self.combo_domaine = ttk.Combobox(self, values=self.DOMAINES, state="readonly", font=FONT_BASE)
        self.combo_domaine.pack(fill="x", padx=16)

        tk.Label(self, text="Faits (optionnel)", font=FONT_BASE, bg=WHITE).pack(anchor="w", **pad)
        self.zone_faits = scrolledtext.ScrolledText(self, wrap="word", font=FONT_BASE, height=6)
        self.zone_faits.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        boutons = tk.Frame(self, bg=WHITE)
        boutons.pack(fill="x", padx=16, pady=(0, 16))
        tk.Button(boutons, text="Annuler", command=self._annuler, font=FONT_BTN).pack(side="right", padx=(8, 0))
        tk.Button(
            boutons, text="Créer", command=self._valider, font=FONT_BTN,
            bg=GOLD, fg="white", activebackground="#9A6F09", activeforeground="white",
        ).pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._annuler)

    def _valider(self):
        nom = self.entree_nom.get().strip()
        if not nom:
            messagebox.showwarning("Nom manquant", "Veuillez indiquer un nom pour ce dossier.")
            return
        self.resultat = {
            "nom": nom,
            "numero_dossier": self.entree_numero.get().strip(),
            "domaine": self.combo_domaine.get(),
            "faits": self.zone_faits.get("1.0", "end").strip(),
        }
        self.destroy()

    def _annuler(self):
        self.resultat = None
        self.destroy()


class DialogueChoixListe(tk.Toplevel):
    """Fenêtre modale de sélection dans une liste de choix (domaine, source
    juridique...), pour remplacer les saisies de numéro façon CLI."""

    def __init__(self, parent, titre, consigne, options, permettre_vide=True):
        super().__init__(parent)
        self.title(titre)
        self.configure(bg=WHITE)
        self.resultat = None
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text=consigne, font=FONT_BASE, bg=WHITE, wraplength=340, justify="left").pack(
            padx=16, pady=(16, 8), anchor="w"
        )

        zone_liste = tk.Frame(self, bg=WHITE)
        zone_liste.pack(padx=16, pady=8, fill="both", expand=True)
        self.listbox = tk.Listbox(zone_liste, font=FONT_BASE, height=min(10, len(options) + 1), exportselection=False)
        if permettre_vide:
            self.listbox.insert("end", "(non précisé)")
        for opt in options:
            self.listbox.insert("end", opt)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", lambda e: self._valider())

        boutons = tk.Frame(self, bg=WHITE)
        boutons.pack(fill="x", padx=16, pady=(0, 16))
        tk.Button(boutons, text="Annuler", command=self._annuler, font=FONT_BTN).pack(side="right", padx=(8, 0))
        tk.Button(
            boutons, text="Valider", command=self._valider, font=FONT_BTN, bg=GOLD, fg="white", relief="flat"
        ).pack(side="right")

    def _valider(self):
        selection = self.listbox.curselection()
        if not selection:
            self.resultat = None
        else:
            texte = self.listbox.get(selection[0])
            self.resultat = "" if texte == "(non précisé)" else texte
        self.destroy()

    def _annuler(self):
        self.resultat = None
        self.destroy()


class DialogueGererListe(tk.Toplevel):
    """Fenêtre modale listant des entrées en attente (jurisprudence, corpus)
    avec un bouton Valider/Rejeter par ligne — remplace la saisie d'ID du
    terminal par un vrai clic."""

    def __init__(self, parent, titre, entrees, libelle, sur_valider, sur_rejeter):
        super().__init__(parent)
        self.title(titre)
        self.geometry("620x480")
        self.configure(bg=WHITE)
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text=f"{len(entrees)} entrée(s) en attente de validation :", font=FONT_BASE, bg=WHITE).pack(
            anchor="w", padx=16, pady=(16, 8)
        )

        canvas = tk.Canvas(self, bg=WHITE, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        frame_liste = tk.Frame(canvas, bg=WHITE)
        frame_liste.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame_liste, anchor="nw", width=580)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(16, 0), pady=8)
        scrollbar.pack(side="right", fill="y", pady=8)

        for entree in list(entrees):
            ligne = tk.Frame(frame_liste, bg=LIGHT_BG)
            ligne.pack(fill="x", pady=4, padx=(0, 12))
            tk.Label(ligne, text=libelle(entree), font=FONT_BASE, bg=LIGHT_BG, wraplength=380, justify="left", anchor="w").pack(
                side="left", fill="x", expand=True, padx=8, pady=8
            )
            zone_boutons = tk.Frame(ligne, bg=LIGHT_BG)
            zone_boutons.pack(side="right", padx=8)

            def _faire_valider(e=entree, l=ligne):
                sur_valider(e)
                l.destroy()

            def _faire_rejeter(e=entree, l=ligne):
                sur_rejeter(e)
                l.destroy()

            tk.Button(zone_boutons, text="✅ Valider", command=_faire_valider, font=FONT_BTN, bg="#3D8B5A", fg="white", relief="flat").pack(pady=2)
            tk.Button(zone_boutons, text="🗑️ Rejeter", command=_faire_rejeter, font=FONT_BTN, bg="#C0403A", fg="white", relief="flat").pack(pady=2)

        tk.Button(self, text="Fermer", command=self.destroy, font=FONT_BTN).pack(pady=(0, 16))


class DialogueHistoriqueConversations(tk.Toplevel):
    """Fenêtre modale listant les conversations de chat enregistrées —
    « Ouvrir » recharge la conversation dans le chat principal, « Supprimer »
    la retire de la base pour libérer de l'espace. Sur le modèle de la
    liste des discussions passées d'une application comme Claude.ai."""

    def __init__(self, parent, titre, entrees, libelle, sur_ouvrir, sur_supprimer):
        super().__init__(parent)
        self.title(titre)
        self.geometry("620x480")
        self.configure(bg=WHITE)
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text=f"{len(entrees)} conversation(s) enregistrée(s) :", font=FONT_BASE, bg=WHITE).pack(
            anchor="w", padx=16, pady=(16, 8)
        )

        canvas = tk.Canvas(self, bg=WHITE, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        frame_liste = tk.Frame(canvas, bg=WHITE)
        frame_liste.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame_liste, anchor="nw", width=580)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(16, 0), pady=8)
        scrollbar.pack(side="right", fill="y", pady=8)

        for entree in list(entrees):
            ligne = tk.Frame(frame_liste, bg=LIGHT_BG)
            ligne.pack(fill="x", pady=4, padx=(0, 12))
            tk.Label(ligne, text=libelle(entree), font=FONT_BASE, bg=LIGHT_BG, wraplength=380, justify="left", anchor="w").pack(
                side="left", fill="x", expand=True, padx=8, pady=8
            )
            zone_boutons = tk.Frame(ligne, bg=LIGHT_BG)
            zone_boutons.pack(side="right", padx=8)

            def _faire_ouvrir(e=entree):
                sur_ouvrir(e)
                self.destroy()

            def _faire_supprimer(e=entree, l=ligne):
                if messagebox.askyesno("Supprimer", f"Supprimer définitivement « {e['titre']} » ?"):
                    sur_supprimer(e)
                    l.destroy()

            tk.Button(zone_boutons, text="📂 Ouvrir", command=_faire_ouvrir, font=FONT_BTN, bg=GOLD, fg="white", relief="flat").pack(pady=2)
            tk.Button(zone_boutons, text="🗑️ Supprimer", command=_faire_supprimer, font=FONT_BTN, bg="#C0403A", fg="white", relief="flat").pack(pady=2)

        tk.Button(self, text="Fermer", command=self.destroy, font=FONT_BTN).pack(pady=(0, 16))


class DialogueNotificationsVeille(tk.Toplevel):
    """Fenêtre modale affichant les nouveautés de veille juridique détectées
    pour les dossiers actifs -- jurisprudence (existant) ET modifications
    d'articles de loi (voir veille_lois.py), plus le rappel OHADA le cas
    échéant -- consultée d'un clic sur le badge 🔔, jamais imposée. Chaque
    notification porte un "type" ("jurisprudence" | "loi" | "ohada") qui
    détermine son rendu."""

    def __init__(self, parent, notifications):
        super().__init__(parent)
        self.title("Veille juridique")
        self.geometry("640x480")
        self.configure(bg=WHITE)
        self.transient(parent)
        self.grab_set()

        tk.Label(
            self, text=f"{len(notifications)} nouveauté(s) pour vos dossiers actifs :",
            font=FONT_BASE, bg=WHITE, wraplength=600, justify="left",
        ).pack(anchor="w", padx=16, pady=(16, 8))

        canvas = tk.Canvas(self, bg=WHITE, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        frame_liste = tk.Frame(canvas, bg=WHITE)
        frame_liste.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame_liste, anchor="nw", width=580)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(16, 0), pady=8)
        scrollbar.pack(side="right", fill="y", pady=8)

        import webbrowser

        for notif in notifications:
            type_notif = notif.get("type", "jurisprudence")
            ligne = tk.Frame(frame_liste, bg=LIGHT_BG)
            ligne.pack(fill="x", pady=4, padx=(0, 12))

            if type_notif == "jurisprudence":
                texte = f"📁 {notif['dossier_nom']}\n{notif['reference']}\n{notif['resume'][:150]}"
                lien = notif.get("source")
            elif type_notif == "loi":
                dossiers_txt = ", ".join(d["nom"] for d in notif["dossiers"]) or "(aucun dossier actif ne le cite plus)"
                etats = f"{notif['ancien_etat'] or '?'} → {notif['nouvel_etat'] or '?'}"
                texte = (
                    f"⚠️ Article {notif['numero']} du {_CODES_LIBELLES.get(notif['code'], notif['code'])} modifié "
                    f"({etats})\nDossier(s) concerné(s) : {dossiers_txt}"
                )
                lien = notif.get("lien")
            else:  # "ohada" -- rappel global, non lié à un dossier précis (voir veille_lois.rappel_veille_ohada)
                texte = f"📚 {notif['message']}"
                lien = None

            tk.Label(ligne, text=texte, font=FONT_BASE, bg=LIGHT_BG, wraplength=420, justify="left", anchor="w").pack(
                side="left", fill="x", expand=True, padx=8, pady=8
            )
            zone_boutons = tk.Frame(ligne, bg=LIGHT_BG)
            zone_boutons.pack(side="right", padx=8)
            if lien:
                tk.Button(
                    zone_boutons, text="🔗 Source", command=lambda url=lien: webbrowser.open(url),
                    font=FONT_BTN, bg=GOLD, fg="white", relief="flat",
                ).pack(side="top", pady=2, fill="x")
            if type_notif == "ohada":
                tk.Button(
                    zone_boutons, text="Marquer vérifié", command=self._marquer_ohada_verifie,
                    font=FONT_BTN, bg=WHITE, fg=TEXT, relief="flat",
                ).pack(side="top", pady=2, fill="x")

        tk.Button(self, text="Fermer", command=self.destroy, font=FONT_BTN).pack(pady=(0, 16))

    def _marquer_ohada_verifie(self):
        import veille_lois
        veille_lois.marquer_veille_ohada_verifiee()
        messagebox.showinfo(
            "Corpus OHADA",
            "Noté : le corpus OHADA sera considéré comme revérifié à partir de maintenant. "
            "Prochain rappel dans plusieurs mois.",
        )


class DialogueAlertesArticles(tk.Toplevel):
    """Fenêtre listant les articles de loi modifiés référencés dans un
    dossier précis -- ouverte depuis le signal « ⚠️ Loi modifiée » du
    bandeau (voir PlaidIAApp._afficher_alertes_articles_dossier). Chaque
    alerte ne peut être acquittée qu'explicitement (bouton « Vu, ignorer
    cette alerte ») -- jamais automatiquement, et rien dans cette fenêtre
    ne modifie le contenu du dossier lui-même."""

    def __init__(self, parent, app, nom_dossier, alertes):
        super().__init__(parent)
        self.title(f"Lois modifiées — {nom_dossier}")
        self.geometry("560x420")
        self.configure(bg=WHITE)
        self.transient(parent)
        self.grab_set()

        tk.Label(
            self,
            text=(
                f"{len(alertes)} article(s) référencé(s) dans « {nom_dossier} » ont été modifiés depuis leur "
                "dernière citation. Rien n'a été changé automatiquement dans vos analyses ou plans -- à vous de "
                "vérifier et, si besoin, de relancer une génération."
            ),
            font=FONT_BASE, bg=WHITE, wraplength=520, justify="left",
        ).pack(anchor="w", padx=16, pady=(16, 8))

        import webbrowser

        canvas = tk.Canvas(self, bg=WHITE, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        frame_liste = tk.Frame(canvas, bg=WHITE)
        frame_liste.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame_liste, anchor="nw", width=500)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(16, 0), pady=8)
        scrollbar.pack(side="right", fill="y", pady=8)

        for alerte in alertes:
            ligne = tk.Frame(frame_liste, bg=LIGHT_BG)
            ligne.pack(fill="x", pady=4, padx=(0, 12))
            etats = f"{alerte['ancien_etat'] or '?'} → {alerte['nouvel_etat'] or '?'}"
            date_mod = f"\nDate d'effet : {alerte['date_modification']}" if alerte.get("date_modification") else ""
            texte = f"Article {alerte['numero']} du {_CODES_LIBELLES.get(alerte['code'], alerte['code'])} ({etats}){date_mod}"
            tk.Label(ligne, text=texte, font=FONT_BASE, bg=LIGHT_BG, wraplength=320, justify="left", anchor="w").pack(
                side="left", fill="x", expand=True, padx=8, pady=8
            )
            zone_boutons = tk.Frame(ligne, bg=LIGHT_BG)
            zone_boutons.pack(side="right", padx=8)
            if alerte.get("lien_source"):
                tk.Button(
                    zone_boutons, text="🔗 Voir à jour", command=lambda url=alerte["lien_source"]: webbrowser.open(url),
                    font=FONT_BTN, bg=GOLD, fg="white", relief="flat",
                ).pack(side="top", pady=2, fill="x")
            tk.Button(
                zone_boutons, text="Vu, ignorer", command=lambda a=alerte, l=ligne: self._acquitter(app, a, l),
                font=FONT_BTN, bg=WHITE, fg=TEXT, relief="flat",
            ).pack(side="top", pady=2, fill="x")

        tk.Button(self, text="Fermer", command=self.destroy, font=FONT_BTN).pack(pady=(0, 16))

    def _acquitter(self, app, alerte, ligne):
        app._acquitter_alerte_article(alerte["id"])
        ligne.destroy()


class Generation:
    """Un traitement long (analyse, plan, plaidoirie, simulateur...) suivi
    indépendamment de l'écran affiché -- voir PlaidIAApp._lancer_generation.

    `dossier_id`/`dossier_nom` sont figés au lancement, jamais relus depuis
    self.dossier_actuel plus tard : sans ça, changer de dossier (ou de
    sélection) pendant qu'une génération tourne ferait enregistrer le
    résultat sous le mauvais dossier -- ou le perdrait silencieusement si
    plus aucun dossier n'était sélectionné à la fin. C'était le vrai bug
    derrière « la génération s'interrompt quand je change d'écran » : le
    thread continuait, mais son résultat n'atteignait plus jamais le bon
    endroit."""

    def __init__(self, id_, dossier_id, dossier_nom, feature, libelle, fonction_sauvegarde, fonction_affichage, widget_erreur):
        self.id = id_  # identifiant en mémoire (uuid), valable pour la durée de la session
        self.db_id = None  # id de la ligne dans db.generations -- voir _lancer_generation ; None tant que non encore posé
        self.dossier_id = dossier_id
        self.dossier_nom = dossier_nom
        self.feature = feature
        self.libelle = libelle
        self.fonction_sauvegarde = fonction_sauvegarde
        self.fonction_affichage = fonction_affichage
        self.widget_erreur = widget_erreur
        self.statut = "en_cours"  # "en_cours" | "terminee" | "erreur" -- reflète UNIQUEMENT le traitement IA lui-même
        self.resultat = None
        self.erreur = None
        self.avertissement = None  # non None si le contenu a bien été généré (statut="terminee") mais pas enregistré dans le dossier
        self.horodatage_debut = time.time()
        self.horodatage_fin = None
        self.lue = False  # passe à True une fois vue dans DialogueGenerations


class EntreeHistorique:
    """Vue en lecture seule d'une ligne de db.generations, pour affichage
    dans DialogueGenerations -- même attributs que Generation pour que la
    fenêtre puisse traiter les deux de façon identique (voir
    PlaidIAApp._entrees_historique_generations, qui fusionne les deux
    sources : la session en cours et l'historique persistant).

    Contrairement à Generation, `fonction_affichage` est toujours None :
    le rendu soigné d'origine n'existe qu'en mémoire, le temps de la
    session qui a lancé la génération -- une entrée retrouvée après
    redémarrage de l'app s'ouvre donc avec un rendu générique du contenu
    JSON stocké, honnête plutôt que reconstitué."""

    def __init__(self, row, dossier_nom):
        self.db_id = row["id"]
        self.dossier_id = row["dossier_id"]
        self.dossier_nom = dossier_nom
        self.feature = row["type"]
        self.libelle = row["libelle"]
        self.statut = row["statut"]
        self.resultat = row["contenu"]
        self.erreur = row["erreur"]
        self.avertissement = None
        self.horodatage_debut = datetime.fromisoformat(row["date_creation"]).timestamp()
        self.horodatage_fin = datetime.fromisoformat(row["date_fin"]).timestamp() if row["date_fin"] else None
        self.fonction_affichage = None
        self.widget_erreur = None
        self.lue = True  # l'historique persisté n'alimente pas le compteur "non lu", propre à la session en cours


class DialogueGenerations(tk.Toplevel):
    """Fenêtre listant toutes les générations suivies (en cours et
    récentes), consultée d'un clic sur le badge 🔄 -- permet de retrouver
    un résultat produit pendant qu'on travaillait ailleurs dans l'app,
    sans jamais avoir interrompu le traitement lui-même (même idiome que
    DialogueNotificationsVeille pour la veille juridique)."""

    _LIBELLES_STATUT = {"en_cours": "⏳ En cours", "terminee": "✅ Terminée", "erreur": "⚠ Erreur"}

    def __init__(self, parent, app, generations):
        super().__init__(parent)
        self.title("Générations")
        self.geometry("560x440")
        self.configure(bg=WHITE)
        self.transient(parent)
        self.grab_set()

        tk.Label(
            self, text="Générations en cours et récentes :", font=FONT_BASE, bg=WHITE,
        ).pack(anchor="w", padx=16, pady=(16, 8))

        canvas = tk.Canvas(self, bg=WHITE, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        frame_liste = tk.Frame(canvas, bg=WHITE)
        frame_liste.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame_liste, anchor="nw", width=500)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(16, 0), pady=8)
        scrollbar.pack(side="right", fill="y", pady=8)

        for gen in sorted(generations, key=lambda g: g.horodatage_debut, reverse=True):
            ligne = tk.Frame(frame_liste, bg=LIGHT_BG)
            ligne.pack(fill="x", pady=4, padx=(0, 12))
            duree = int((gen.horodatage_fin or time.time()) - gen.horodatage_debut)
            prefixe = f"📁 {gen.dossier_nom} — " if gen.dossier_nom else ""
            texte = f"{prefixe}{gen.libelle}\n{self._LIBELLES_STATUT.get(gen.statut, gen.statut)} ({duree}s)"
            if gen.statut == "erreur" and gen.erreur:
                texte += f"\n{gen.erreur[:150]}"
            if getattr(gen, "avertissement", None):
                texte += f"\n⚠ {gen.avertissement[:150]}"
            tk.Label(
                ligne, text=texte, font=FONT_BASE, bg=LIGHT_BG, wraplength=300, justify="left", anchor="w",
            ).pack(side="left", fill="x", expand=True, padx=8, pady=8)

            zone_boutons = tk.Frame(ligne, bg=LIGHT_BG)
            zone_boutons.pack(side="right", padx=8)
            if gen.statut == "terminee":
                tk.Button(
                    zone_boutons, text="Ouvrir →", command=lambda g=gen: (self.destroy(), app._ouvrir_resultat_generation(g)),
                    font=FONT_BTN, bg=GOLD, fg="white", relief="flat",
                ).pack(side="top", pady=2, fill="x")
            if gen.statut in ("terminee", "erreur"):
                tk.Button(
                    zone_boutons, text="Supprimer", command=lambda g=gen, l=ligne: self._supprimer(app, g, l),
                    font=FONT_BTN, bg=WHITE, fg="#B91C1C", relief="flat",
                ).pack(side="top", pady=2, fill="x")

        tk.Button(self, text="Fermer", command=self.destroy, font=FONT_BTN).pack(pady=(0, 16))

    def _supprimer(self, app, gen, ligne):
        """Suppression DÉFINITIVE d'une entrée d'historique -- toujours
        confirmée explicitement, jamais automatique (voir
        db.supprimer_generation). Ne touche qu'à cette ligne, la fenêtre
        reste ouverte sur le reste de l'historique."""
        confirme = messagebox.askyesno(
            "Suppression définitive",
            f"Supprimer définitivement « {gen.libelle} » de l'historique des générations ?\n\n"
            "Cette action est irréversible.",
            icon="warning",
        )
        if not confirme:
            return
        app._supprimer_generation(gen)
        ligne.destroy()


class DialogueImporterTexte(tk.Toplevel):
    """Fenêtre modale pour importer un texte juridique dans le corpus
    multi-source (OHADA, UE, droit sénégalais...)."""

    SOURCES = ["Légifrance (France)", "OHADA", "Union européenne", "Droit sénégalais", "CEDEAO", "Conseil de l'Europe / CEDH", "Autre"]

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Importer un texte juridique")
        self.geometry("620x600")
        self.configure(bg=WHITE)
        self.resultat = None
        self.transient(parent)
        self.grab_set()

        def champ(label):
            tk.Label(self, text=label, font=FONT_BASE, bg=WHITE).pack(anchor="w", padx=16, pady=(8, 2))
            entree = tk.Entry(self, font=FONT_BASE)
            entree.pack(fill="x", padx=16)
            return entree

        tk.Label(self, text="Source :", font=FONT_BASE, bg=WHITE).pack(anchor="w", padx=16, pady=(12, 2))
        self.source_var = tk.StringVar(value=self.SOURCES[1])
        combo_source = ttk.Combobox(self, textvariable=self.source_var, values=self.SOURCES, state="readonly", font=FONT_BASE)
        combo_source.pack(fill="x", padx=16)

        self.entree_pays = champ("Pays / zone concernée (optionnel) :")
        self.entree_type = champ("Type de texte (ex. « Acte uniforme », « Règlement », « Loi ») :")
        self.entree_domaine = champ("Domaine (ex. « Droit commercial général ») :")
        self.entree_reference = champ("Référence précise du texte :")
        self.entree_date = champ("Date du texte (optionnel) :")

        tk.Label(self, text="Contenu du texte :", font=FONT_BASE, bg=WHITE).pack(anchor="w", padx=16, pady=(12, 2))
        self.zone_texte = scrolledtext.ScrolledText(self, wrap="word", font=FONT_BASE, height=8)
        self.zone_texte.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        boutons = tk.Frame(self, bg=WHITE)
        boutons.pack(fill="x", padx=16, pady=(0, 16))
        tk.Button(boutons, text="Annuler", command=self._annuler, font=FONT_BTN).pack(side="right", padx=(8, 0))
        tk.Button(boutons, text="Importer", command=self._valider, font=FONT_BTN, bg=GOLD, fg="white", relief="flat").pack(side="right")

    def _valider(self):
        contenu = self.zone_texte.get("1.0", "end").strip()
        if not contenu:
            messagebox.showwarning("Contenu manquant", "Veuillez transmettre le texte à importer.")
            return
        self.resultat = {
            "source": self.source_var.get(),
            "contenu": contenu,
            "pays": self.entree_pays.get().strip(),
            "type_texte": self.entree_type.get().strip(),
            "domaine": self.entree_domaine.get().strip(),
            "reference": self.entree_reference.get().strip(),
            "date_texte": self.entree_date.get().strip(),
        }
        self.destroy()

    def _annuler(self):
        self.resultat = None
        self.destroy()


class PlaidIAApp:
    # Fréquence de re-vérification des veilles (jurisprudence + lois)
    # PENDANT que l'app reste ouverte, pas seulement à son lancement --
    # voir _boucle_veille. Le throttle propre à chaque article
    # (veille_lois.DELAI_MIN_ENTRE_VERIFICATIONS_HEURES) protège le quota
    # Légifrance indépendamment de cette fréquence.
    INTERVALLE_VEILLE_MS = 60 * 60 * 1000  # 1 heure

    def __init__(self, root):
        self.root = root
        self.root.title("Plaid'IA — Assistant de préparation de plaidoirie")
        self.root.geometry("1080x720")
        self.root.minsize(900, 600)
        try:
            # Démarre en fenêtre maximisée pour que le maximum de boutons
            # de la barre latérale soit visible sans avoir à défiler.
            self.root.state("zoomed")
        except tk.TclError:
            pass
        self.root.configure(bg=LIGHT_BG)

        self.dossier_actuel = None
        self.dossiers_map = {}
        self.boutons_actions = []
        # Suivi des générations en arrière-plan (analyse, plan, plaidoirie...)
        # -- voir _lancer_generation. `ecran_actuel` identifie la
        # fonctionnalité actuellement affichée dans le panneau de sortie
        # (ex. "analyser", "plan"...), posée par chaque _action_xxx qui
        # affiche un résultat ; sert à décider si le résultat d'une
        # génération qui se termine doit être rendu tout de suite ou
        # seulement signalé par le badge 🔄.
        self.generations = {}
        self._generations_actives_par_cle = set()
        self.ecran_actuel = None
        # Historique de la conversation "Poser une question" — persiste tant
        # que l'avocat ne démarre pas explicitement une nouvelle discussion
        # (comme sur Claude.ai), ou qu'il ne change pas de dossier.
        self.historique_question = []
        # Id de la conversation en base — None tant qu'aucun message n'a
        # été envoyé ; sauvegarde automatique à chaque échange, sans que
        # l'avocat ait à cliquer sur « Enregistrer » (comme Claude.ai).
        self.conversation_chat_id = None
        # Garde-fous anti-superposition des veilles (voir _boucle_veille) --
        # évitent qu'un cycle démarre alors que le précédent tourne encore.
        self._veille_jurisprudence_en_cours = False
        self._veille_lois_en_cours = False

        self._construire_interface()
        self._rafraichir_dossiers()
        self._rafraichir_juridictions()
        self._boucle_veille()

    # ---------- Construction de l'interface ----------
    def _construire_interface(self):
        # Bandeau du haut
        bandeau = tk.Frame(self.root, bg=NAVY, height=64)
        bandeau.pack(fill="x")
        bandeau.pack_propagate(False)

        tk.Label(bandeau, text="⚖ Plaid'IA", font=FONT_TITLE, fg="white", bg=NAVY).pack(side="left", padx=24)

        zone_dossier = tk.Frame(bandeau, bg=NAVY)
        zone_dossier.pack(side="left", padx=20)

        self.dossier_var = tk.StringVar()
        self.combo_dossiers = ttk.Combobox(
            zone_dossier, textvariable=self.dossier_var, state="readonly", width=36, font=FONT_BASE
        )
        self.combo_dossiers.pack(side="left")
        self.combo_dossiers.bind("<<ComboboxSelected>>", self._selectionner_dossier)

        tk.Button(
            bandeau, text="＋ Nouveau dossier", command=self._nouveau_dossier, font=FONT_BTN,
            bg=GOLD, fg="white", activebackground="#9A6F09", activeforeground="white", relief="flat", padx=12,
        ).pack(side="left", padx=8)

        # Sélecteur de juridiction — toujours visible, modifiable en un clic,
        # et mémorisé d'un lancement de l'application à l'autre (moderne :
        # pas de fenêtre imposée au démarrage, juste un réglage accessible
        # et qui se souvient de votre dernier choix).
        zone_juridiction = tk.Frame(bandeau, bg=NAVY)
        zone_juridiction.pack(side="left", padx=(4, 0))
        tk.Label(zone_juridiction, text="⚖ Droit :", font=("Segoe UI", 9), fg="#C9D6E8", bg=NAVY).pack(side="left", padx=(0, 6))
        self.juridiction_var = tk.StringVar()
        self.combo_juridiction = ttk.Combobox(
            zone_juridiction, textvariable=self.juridiction_var, state="readonly", width=20, font=("Segoe UI", 9),
        )
        self.combo_juridiction.pack(side="left")
        self.combo_juridiction.bind("<<ComboboxSelected>>", self._changer_juridiction)

        # Badge de veille juridique — toujours visible en discret (gris
        # bleuté), pour que la fonctionnalité soit repérable même quand
        # rien de neuf n'a été trouvé ; devient doré et affiche un nombre
        # dès qu'une vraie nouveauté est détectée. Vérification silencieuse
        # au lancement, jamais intrusive, jamais de fenêtre imposée.
        self.bouton_veille = tk.Button(
            bandeau, text="🔔", command=self._afficher_notifications_veille, font=("Segoe UI", 11),
            bg=NAVY, fg="#5578A0", activebackground=NAVY, activeforeground="#5578A0", relief="flat", bd=0, cursor="hand2",
        )
        self.bouton_veille.pack(side="left", padx=(10, 0))
        self.notifications_veille = []  # liste de dicts {dossier_nom, reference, resume, source}

        # Badge des générations en arrière-plan -- même idiome que le badge
        # de veille juste au-dessus : toujours visible (discret au repos),
        # doré et avec un compteur dès qu'une génération tourne ou vient de
        # se terminer, quel que soit l'écran affiché au moment où ça arrive.
        self.bouton_generations = tk.Button(
            bandeau, text="🔄", command=self._afficher_generations, font=("Segoe UI", 11),
            bg=NAVY, fg="#5578A0", activebackground=NAVY, activeforeground="#5578A0", relief="flat", bd=0, cursor="hand2",
        )
        self.bouton_generations.pack(side="left", padx=(10, 0))

        self.label_dossier_actif = tk.Label(bandeau, text="Aucun dossier sélectionné", font=FONT_BASE, fg="#C9D6E8", bg=NAVY)
        self.label_dossier_actif.pack(side="right", padx=(4, 24))

        # Signal d'alerte "article de loi modifié" pour le dossier actif --
        # voir veille_lois.py. Même principe que les badges 🔔/🔄 : toujours
        # visible, en discret (gris) par défaut, seul le texte se colore et
        # affiche un nombre quand une alerte active existe -- jamais masqué/
        # réaffiché par pack/pack_forget, pour que sa position reste stable
        # dans le bandeau. Recalculé à chaque changement de dossier (voir
        # _selectionner_dossier).
        self.bouton_alerte_dossier = tk.Button(
            bandeau, text="⚠️", command=self._afficher_alertes_articles_dossier, font=("Segoe UI", 9, "bold"),
            bg=NAVY, fg="#5578A0", activebackground=NAVY, activeforeground="#5578A0", relief="flat", bd=0, cursor="hand2",
        )
        self.bouton_alerte_dossier.pack(side="right", padx=(0, 8))

        # Barre de commande en langage naturel — la vraie signature de l'outil :
        # parler à l'agent plutôt que naviguer dans des menus.
        barre_commande = tk.Frame(self.root, bg=NAVY_DARK, height=52)
        barre_commande.pack(fill="x")
        barre_commande.pack_propagate(False)

        tk.Label(barre_commande, text="💬", font=("Segoe UI", 14), fg=GOLD, bg=NAVY_DARK).pack(side="left", padx=(24, 8))

        self.commande_var = tk.StringVar()
        entree_commande = tk.Entry(
            barre_commande, textvariable=self.commande_var, font=("Segoe UI", 11),
            relief="flat", bg="#24405F", fg="white", insertbackground="white",
        )
        entree_commande.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=10)
        entree_commande.insert(0, "")
        entree_commande.bind("<Return>", lambda e: self._commande_naturelle())
        self._placeholder_commande(entree_commande)

        tk.Button(
            barre_commande, text="Envoyer →", command=self._commande_naturelle, font=FONT_BTN,
            bg=GOLD, fg="white", activebackground="#9A6F09", activeforeground="white", relief="flat", padx=14,
        ).pack(side="left", padx=(0, 24))

        self.entree_commande = entree_commande

        # Zone principale : boutons à gauche, sortie à droite
        principal = tk.Frame(self.root, bg=LIGHT_BG)
        principal.pack(fill="both", expand=True, padx=14, pady=14)

        panneau_gauche = tk.Frame(principal, bg=LIGHT_BG, width=250)
        panneau_gauche.pack(side="left", fill="y", padx=(0, 14))
        panneau_gauche.pack_propagate(False)

        # Sélecteur d'espace — Avocat / Greffier, comme l'écran d'accueil du
        # terminal. Bascule l'affichage entre les deux jeux de boutons.
        zone_espace = tk.Frame(panneau_gauche, bg=LIGHT_BG)
        zone_espace.pack(fill="x", pady=(0, 10))
        self.bouton_espace_avocat = tk.Button(
            zone_espace, text="⚖️ Avocat", font=("Segoe UI", 9, "bold"),
            command=lambda: self._changer_espace("avocat"), relief="flat", padx=8, pady=6,
        )
        self.bouton_espace_avocat.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.bouton_espace_greffier = tk.Button(
            zone_espace, text="🖋️ Greffier", font=("Segoe UI", 9, "bold"),
            command=lambda: self._changer_espace("greffier"), relief="flat", padx=8, pady=6,
        )
        self.bouton_espace_greffier.pack(side="left", fill="x", expand=True)

        # Sélecteur de catégorie — remplace la longue liste défilante par
        # des catégories qu'on choisit dans un menu déroulant, pour ne
        # jamais avoir besoin de défiler pour atteindre un bouton.
        zone_categorie = tk.Frame(panneau_gauche, bg=LIGHT_BG)
        zone_categorie.pack(fill="x", pady=(0, 10))
        tk.Label(zone_categorie, text="Catégorie :", font=("Segoe UI", 9), bg=LIGHT_BG, fg=GRAY).pack(anchor="w")
        self.categorie_var = tk.StringVar()
        self.combo_categorie = ttk.Combobox(
            zone_categorie, textvariable=self.categorie_var, state="readonly", font=FONT_BASE
        )
        self.combo_categorie.pack(fill="x", pady=(2, 0))
        self.combo_categorie.bind("<<ComboboxSelected>>", lambda e: self._afficher_categorie(self.categorie_var.get()))

        self.frame_boutons_categorie = tk.Frame(panneau_gauche, bg=LIGHT_BG)
        self.frame_boutons_categorie.pack(fill="both", expand=True, pady=(8, 0))

        # Définition de toutes les catégories, par espace. Chaque catégorie
        # ne contient que quelques boutons — tient toujours à l'écran sans
        # avoir besoin de défiler, contrairement à l'ancienne liste unique.
        self.categories = {
            "avocat": [
                ("💬 Poser une question", [
                ("💬  Échanger avec l'agent juridique\n     (indépendamment du dossier)", self._action_question, False),
                ]),
                ("⚔️ L'Arsenal", [
                    ("📊  Analyser des conclusions adverses", self._action_analyser, True),
                    ("📋  Résumer ce dossier", self._action_resumer, True),
                    ("🎤  Générer un plan de plaidoirie", self._action_plan, True),
                    ("❓  Simuler les objections probables", self._action_simulateur, True),
                    ("📑  Rapport complet", self._action_rapport_complet, True),
                    ("🔍  Analyse stylistique des\n     conclusions adverses", self._action_analyser_style, False),
                    ("⏱️  Vérification procédurale\n     (avant de déposer un acte ou plaider)", self._action_verification_procedurale, True),
                ]),
                ("📁 La Chemise", [
                    ("🕘  Historique de ce dossier", self._action_historique_dossier, True),
                    ("🗂️  Parcourir mes dossiers", self._action_parcourir_dossiers, False),
                    ("📥  Préparer ce dossier\n     (importer des documents)", self._action_preparer_dossier, True),
                    ("📤  Exporter les faits bruts", self._action_export_faits_bruts, True),
                    ("🏷️  Modifier le domaine", self._action_modifier_domaine, True),
                    ("🗑️  Supprimer ce dossier", self._action_supprimer_dossier, True),
                ]),
                ("📖 Le Grimoire", [
                    ("🔎  Consulter la jurisprudence\n     sur une situation", self._action_consulter_jurisprudence, False),
                    ("📚  Collecter de la jurisprudence\n     (Judilibre)", self._action_collecter_jurisprudence, False),
                    ("✅  Gérer la jurisprudence\n     (valider / rejeter)", self._action_gerer_jurisprudence, False),
                    ("📄  Importer un texte\n     (OHADA, UE, Sénégal...)", self._action_importer_texte_corpus, False),
                    ("✅  Gérer le corpus multi-source", self._action_gerer_corpus, False),
                ]),
                ("✒️ Le Carnet", [
                    ("📝  Prendre une note", self._action_note, True),
                    ("📖  Consulter les notes", self._action_consulter_notes, True),
                    ("💌  Rédiger une note client", self._action_note_client, True),
                ]),
            ],
            "greffier": [
                ("📋 Affaire en cours", [
                    ("📅  Chronologie automatique\n     de cette affaire", self._action_chronologie, True),
                    ("📋  Résumer cette affaire", self._action_resumer, True),
                    ("⏱️  Vérification procédurale", self._action_verification_procedurale, True),
                ]),
                ("📄 Documents", [
                    ("🔬  Extraction d'éléments clés\n     d'un document", self._action_extraction_document, False),
                    ("📂  Classement automatique\n     d'un document", self._action_classement_document, False),
                    ("⚖️  Contrôle de cohérence\n     entre documents", self._action_controle_coherence, False),
                    ("🗣️  Analyser un réquisitoire", self._action_analyser_requisitoire, False),
                    ("📑  Rapport d'instruction", self._action_rapport_instruction, False),
                ]),
                ("🔍 Recherche & rédaction", [
                    ("🔍  Rechercher dans toutes\n     les affaires", self._action_rechercher_transversal, False),
                    ("🖊️  Rédiger un procès-verbal\n     d'audience", self._action_pv_audience, False),
                ]),
            ],
        }

        self.espace_actuel = "avocat"
        self._changer_espace("avocat")
        self._styliser_boutons_espace()

        # Zone de sortie — deux vues qui se substituent l'une à l'autre :
        # la vue "résultats" pour les actions ponctuelles (Analyser, Résumer...)
        # et la vue "chat" pour Poser une question, avec sa propre zone de
        # saisie toujours visible en bas, comme une vraie fenêtre de discussion.
        panneau_droit = tk.Frame(principal, bg=WHITE)
        panneau_droit.pack(side="left", fill="both", expand=True)

        # --- Vue "résultats" ---
        self.frame_sortie = tk.Frame(panneau_droit, bg=WHITE)
        self.sortie = scrolledtext.ScrolledText(
            self.frame_sortie, wrap="word", font=FONT_MONO, bg=WHITE, fg=TEXT, relief="flat", padx=16, pady=16
        )
        self.sortie.pack(fill="both", expand=True)
        for widget in (self.sortie,):
            widget.tag_configure("titre", font=("Segoe UI", 12, "bold"), foreground=NAVY)
            widget.tag_configure("risque_eleve", foreground="#B3261E", font=("Consolas", 10, "bold"))
            widget.tag_configure("risque_moyen", foreground="#9A6F09", font=("Consolas", 10, "bold"))
            widget.tag_configure("risque_faible", foreground="#4C6B3F", font=("Consolas", 10, "bold"))
            widget.tag_configure("attention", foreground="#B3261E")
            widget.tag_configure("a_verifier", background="#FFE9B0", foreground="#7A4A00", font=("Consolas", 10, "bold"))
            widget.tag_configure("citation", foreground=NAVY, font=("Consolas", 10, "bold"))
            widget.tag_configure("gras", font=("Consolas", 10, "bold"))
        self._afficher("Bienvenue dans Plaid'IA.\n\nCréez ou sélectionnez un dossier ci-dessus pour commencer.", "titre")
        self.sortie.config(state="disabled")
        self.frame_sortie.pack(fill="both", expand=True)

        # --- Vue "chat" (Poser une question) ---
        self.frame_chat = tk.Frame(panneau_droit, bg=WHITE)

        barre_saisie_chat = tk.Frame(self.frame_chat, bg=LIGHT_BG, height=52)
        barre_saisie_chat.pack(fill="x", side="bottom")
        barre_saisie_chat.pack_propagate(False)

        self.recherche_live_var = tk.BooleanVar(value=False)

        tk.Button(
            barre_saisie_chat, text="📁", command=self._coller_texte_long_chat, font=("Segoe UI", 11),
            bg=LIGHT_BG, fg=TEXT, relief="flat", padx=10,
        ).pack(side="left", padx=(12, 4), pady=10)

        self.chat_var = tk.StringVar()
        self.entree_chat = tk.Entry(
            barre_saisie_chat, textvariable=self.chat_var, font=("Segoe UI", 11),
            relief="flat", bg=WHITE, fg=TEXT, insertbackground=TEXT,
        )
        self.entree_chat.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=10)
        self.entree_chat.bind("<Return>", lambda e: self._envoyer_message_chat())

        tk.Button(
            barre_saisie_chat, text="Envoyer →", command=self._envoyer_message_chat, font=FONT_BTN,
            bg=GOLD, fg="white", activebackground="#9A6F09", activeforeground="white", relief="flat", padx=14,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            barre_saisie_chat, text="🔄 Nouvelle conversation", command=self._nouvelle_conversation, font=("Segoe UI", 9),
            bg=LIGHT_BG, fg=GRAY, relief="flat", padx=10,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            barre_saisie_chat, text="📚 Historique", command=self._action_historique_conversations, font=("Segoe UI", 9),
            bg=LIGHT_BG, fg=GRAY, relief="flat", padx=10,
        ).pack(side="left", padx=(0, 12))

        # Zone principale du chat : la conversation à gauche, un panneau
        # "Intelligence juridique" à droite qui résume ce qui a réellement
        # étayé la dernière réponse (pas une auto-évaluation du modèle,
        # mais des faits vérifiables : sources trouvées, marqueurs à vérifier).
        zone_centrale_chat = tk.Frame(self.frame_chat, bg=WHITE)
        zone_centrale_chat.pack(fill="both", expand=True)

        self.zone_chat = scrolledtext.ScrolledText(
            zone_centrale_chat, wrap="word", font=FONT_MONO, bg=WHITE, fg=TEXT, relief="flat", padx=16, pady=16
        )
        self.zone_chat.pack(side="left", fill="both", expand=True)
        self.zone_chat.tag_configure("titre", font=("Segoe UI", 12, "bold"), foreground=NAVY)
        self.zone_chat.tag_configure("attention", foreground="#B3261E")
        self.zone_chat.tag_configure("a_verifier", background="#FFE9B0", foreground="#7A4A00", font=("Consolas", 10, "bold"))
        self.zone_chat.tag_configure("citation", foreground=NAVY, font=("Consolas", 10, "bold"))
        self.zone_chat.tag_configure("gras", font=("Consolas", 10, "bold"))
        self.zone_chat.config(state="disabled")

        self.panneau_intelligence = tk.Frame(zone_centrale_chat, bg="#EEF1F6", width=220)
        self.panneau_intelligence.pack(side="right", fill="y")
        self.panneau_intelligence.pack_propagate(False)
        self._construire_panneau_intelligence_vide()

        # Barre de statut
        self.barre_statut = tk.Label(
            self.root, text="Prêt", anchor="w", bg="#E5E7EB", fg=GRAY, font=("Segoe UI", 9), padx=10, pady=4
        )
        self.barre_statut.pack(fill="x", side="bottom")

    # ---------- Gestion des dossiers ----------
    def _bouton_sidebar(self, parent, texte, commande, besoin_dossier=True):
        actif = (not besoin_dossier) or (self.dossier_actuel is not None)
        b = tk.Button(
            parent, text=texte, command=commande, font=FONT_BTN, anchor="w", justify="left",
            bg=WHITE, relief="flat", padx=12, pady=8, wraplength=215,
            activebackground="#E8ECF2", state="normal" if actif else "disabled",
        )
        b.pack(fill="x", pady=3)
        if besoin_dossier:
            self.boutons_actions.append(b)
        return b

    def _afficher_categorie(self, nom_categorie):
        """Vide et reconstruit le panneau de boutons pour la catégorie
        choisie dans le menu déroulant — chaque catégorie ne contient que
        quelques boutons, donc tient toujours à l'écran sans défilement."""
        for widget in self.frame_boutons_categorie.winfo_children():
            widget.destroy()
        self.boutons_actions = []

        categorie = next((c for c in self.categories[self.espace_actuel] if c[0] == nom_categorie), None)
        if not categorie:
            return
        for libelle, commande, besoin_dossier in categorie[1]:
            self._bouton_sidebar(self.frame_boutons_categorie, libelle, commande, besoin_dossier=besoin_dossier)

    def _changer_espace(self, espace):
        self.espace_actuel = espace
        noms_categories = [c[0] for c in self.categories[espace]]
        self.combo_categorie["values"] = noms_categories
        self.categorie_var.set(noms_categories[0])
        self._afficher_categorie(noms_categories[0])
        self._styliser_boutons_espace()

    def _styliser_boutons_espace(self):
        actif, inactif = NAVY, WHITE
        actif_fg, inactif_fg = "white", TEXT
        if self.espace_actuel == "avocat":
            self.bouton_espace_avocat.config(bg=actif, fg=actif_fg, activebackground=actif)
            self.bouton_espace_greffier.config(bg=inactif, fg=inactif_fg, activebackground="#E8ECF2")
        else:
            self.bouton_espace_greffier.config(bg=actif, fg=actif_fg, activebackground=actif)
            self.bouton_espace_avocat.config(bg=inactif, fg=inactif_fg, activebackground="#E8ECF2")

    def _rafraichir_dossiers(self):
        dossiers = db.list_dossiers()
        self.dossiers_map = {d["nom"]: dict(d) for d in dossiers}
        self.combo_dossiers["values"] = list(self.dossiers_map.keys())

    def _rafraichir_juridictions(self):
        """(Re)construit la liste déroulante des juridictions disponibles
        dans la barre du haut — Légifrance plus toute source de corpus déjà
        importée — et applique le dernier choix mémorisé en base."""
        sources_importees = db.lister_sources_corpus()
        sources = ["Légifrance (France)"] + [s for s in sources_importees if s != "Légifrance (France)"]
        self.combo_juridiction["values"] = sources

        sauvegardee = db.get_parametre("juridiction_active", "Légifrance (France)")
        if sauvegardee not in sources:
            sauvegardee = "Légifrance (France)"
        self.source_juridique_active = sauvegardee
        self.juridiction_var.set(sauvegardee)

    def _changer_juridiction(self, event):
        """Applique et mémorise immédiatement le nouveau choix de
        juridiction — un seul réglage, toujours visible, jamais besoin de
        le redéfinir au prochain lancement."""
        nouvelle = self.juridiction_var.get()
        self.source_juridique_active = nouvelle
        db.set_parametre("juridiction_active", nouvelle)

    def _lancer_verification_veille(self):
        """Vérification silencieuse et non bloquante de l'existence de
        jurisprudence nouvelle liée aux dossiers actifs — sur le modèle
        d'une application moderne (badge discret, jamais de fenêtre
        imposée). Si Judilibre n'est pas configuré, ou en cas d'erreur
        réseau, échoue silencieusement : cette vérification en
        arrière-plan ne doit jamais perturber l'usage normal de
        l'application ni afficher d'erreur intrusive.

        Relancée toutes les INTERVALLE_VEILLE_MS millisecondes tant que
        l'app reste ouverte (voir _boucle_veille), pas seulement au
        lancement -- un garde-fou (_veille_jurisprudence_en_cours) évite
        de superposer deux vérifications si l'une n'est pas encore
        terminée quand la suivante devrait démarrer (ne devrait pas
        arriver à l'intervalle choisi, mais coûte rien à prévenir)."""
        if self._veille_jurisprudence_en_cours:
            return
        self._veille_jurisprudence_en_cours = True

        def travail():
            try:
                try:
                    import judilibre
                except Exception:
                    return

                try:
                    dossiers = db.list_dossiers()
                except Exception:
                    return

                dossiers_actifs = [dict(d) for d in dossiers if d["statut"] == "en cours" and d["domaine"]][:5]
                nouvelles = []
                for d in dossiers_actifs:
                    try:
                        resultats = judilibre.collecter_jurisprudence(query=d["domaine"], max_results=5)
                    except Exception:
                        continue
                    deja_vues = db.get_references_vues(d["id"])
                    references_ce_dossier = []
                    for r in resultats:
                        references_ce_dossier.append(r["reference"])
                        if r["reference"] not in deja_vues:
                            nouvelles.append({
                                "type": "jurisprudence",
                                "dossier_nom": d["nom"],
                                "dossier_id": d["id"],
                                "reference": r["reference"],
                                "resume": r["resume"],
                                "source": r["source"],
                            })
                    db.marquer_references_vues(d["id"], references_ce_dossier)

                if nouvelles:
                    self.root.after(0, lambda: self._afficher_badge_veille(nouvelles))
            finally:
                self._veille_jurisprudence_en_cours = False

        threading.Thread(target=travail, daemon=True).start()

    def _lancer_verification_veille_lois(self):
        """Vérification silencieuse et non bloquante des modifications
        d'articles de loi référencés dans les dossiers actifs -- voir
        veille_lois.py. Même mécanique de badge que
        _lancer_verification_veille (jurisprudence, ci-dessus), mais thread
        et logique entièrement séparés : construite EN PARALLÈLE, ne
        modifie jamais son fonctionnement ni ses tables. Ne modifie non
        plus JAMAIS le contenu d'une analyse/d'un plan/d'un dossier existant
        -- seulement db.alertes_articles_dossier (une alerte informative).

        Relancée toutes les INTERVALLE_VEILLE_MS millisecondes tant que
        l'app reste ouverte (voir _boucle_veille), pas seulement au
        lancement -- même garde-fou anti-superposition que
        _lancer_verification_veille (_veille_lois_en_cours) ; le throttle
        par article (veille_lois.DELAI_MIN_ENTRE_VERIFICATIONS_HEURES)
        continue de protéger le quota Légifrance indépendamment de la
        fréquence de cette boucle."""
        if self._veille_lois_en_cours:
            return
        self._veille_lois_en_cours = True

        def travail():
            try:
                try:
                    import veille_lois
                except Exception:
                    return
                try:
                    dossiers_actifs = [dict(d) for d in db.list_dossiers() if d["statut"] == "en cours"]
                except Exception:
                    return

                # 1) Réextrait les articles [ART:...] cités par chaque dossier
                #    actif, à partir du contenu déjà généré -- jamais réécrit,
                #    seulement lu (analyses, generations, notes, faits bruts).
                for d in dossiers_actifs:
                    try:
                        textes = [d.get("faits") or ""]
                        for a in db.get_analyses_for_dossier(d["id"]):
                            textes.append(str(a.get("arguments") or ""))
                            textes.append(str(a.get("points_attention") or ""))
                        for g in db.list_generations(dossier_id=d["id"]):
                            textes.append(str(g.get("contenu") or ""))
                        for n in db.get_notes_dossier(d["id"]):
                            textes.append(n.get("note_structuree") or "")
                        db.remplacer_articles_cites_dossier(d["id"], veille_lois.extraire_articles_cites(*textes))
                    except Exception:
                        continue

                # 2) Une seule vérification Légifrance par article distinct,
                #    même cité par plusieurs dossiers (voir veille_lois, qui
                #    limite déjà à une vérification par jour par article).
                nouvelles = []
                try:
                    articles = db.tous_articles_cites()
                except Exception:
                    articles = []
                for code, numero in articles:
                    try:
                        changement = veille_lois.verifier_et_detecter_changement(code, numero)
                    except Exception:
                        continue
                    if not changement:
                        continue
                    dossiers_concernes = db.lister_dossiers_citant_article(code, numero)
                    for dc in dossiers_concernes:
                        db.creer_alerte_article(
                            dc["id"], code, numero,
                            changement["ancien_etat"], changement["nouvel_etat"],
                            changement["date_modification"], changement["lien"],
                        )
                    nouvelles.append({
                        "type": "loi", "code": code, "numero": numero,
                        "ancien_etat": changement["ancien_etat"], "nouvel_etat": changement["nouvel_etat"],
                        "date_modification": changement["date_modification"], "lien": changement["lien"],
                        "dossiers": dossiers_concernes,
                    })

                try:
                    rappel_ohada = veille_lois.rappel_veille_ohada()
                except Exception:
                    rappel_ohada = None
                if rappel_ohada:
                    nouvelles.append({"type": "ohada", "message": rappel_ohada})

                if nouvelles:
                    self.root.after(0, lambda: self._afficher_badge_veille(nouvelles))
            finally:
                self._veille_lois_en_cours = False

        threading.Thread(target=travail, daemon=True).start()

    def _boucle_veille(self):
        """Relance les deux veilles (jurisprudence + lois) toutes les
        INTERVALLE_VEILLE_MS millisecondes tant que l'app reste ouverte --
        pas seulement au lancement, pour que le badge/l'alerte apparaissent
        sans attendre un redémarrage. Chaque veille garde sa propre
        protection anti-répétition (db.elements_veille_vus pour la
        jurisprudence, db.articles_surveilles avec son throttle quotidien
        par article pour les lois) : relancer souvent ne duplique jamais
        une notification déjà vue, ça raccourcit seulement le délai avant
        qu'une vraie nouveauté ne soit détectée."""
        self._lancer_verification_veille()
        self._lancer_verification_veille_lois()
        self.root.after(self.INTERVALLE_VEILLE_MS, self._boucle_veille)

    def _afficher_badge_veille(self, nouvelles):
        """Rend le badge doré et affiche le nombre — au repos, il reste
        visible en discret (voir construction du bandeau), jamais invisible.
        Fusionne avec les notifications déjà présentes plutôt que d'écraser
        -- jurisprudence et lois arrivent depuis deux threads indépendants,
        pas nécessairement au même moment."""
        self.notifications_veille = self.notifications_veille + nouvelles
        self.bouton_veille.config(text=f"🔔 {len(self.notifications_veille)}", fg=GOLD, activeforeground=GOLD)

    def _afficher_notifications_veille(self):
        if not self.notifications_veille:
            messagebox.showinfo(
                "Veille juridique",
                "Aucune nouveauté pour l'instant (jurisprudence ou modification de loi).\n\n"
                "La vérification se fait au lancement de l'application, pour les dossiers « en cours ».",
            )
            return
        DialogueNotificationsVeille(self.root, self.notifications_veille)
        # Déjà marquées comme vues en base au moment de la détection —
        # le badge repasse à l'état discret (mais toujours visible) une
        # fois consulté.
        self.notifications_veille = []
        self.bouton_veille.config(text="🔔", fg="#5578A0", activeforeground="#5578A0")

    def _rafraichir_alerte_articles_dossier(self):
        """Met à jour le signal « ⚠️ » du bandeau selon l'existence
        d'alertes actives pour le dossier actif -- voir veille_lois.py.
        Toujours visible (comme 🔔/🔄) : seuls le texte et la couleur
        changent, jamais pack/pack_forget. Recalculé à chaque changement
        de dossier (voir _selectionner_dossier)."""
        alertes = db.get_alertes_actives_dossier(self.dossier_actuel["id"]) if self.dossier_actuel else []
        if alertes:
            self.bouton_alerte_dossier.config(
                text=f"⚠️ {len(alertes)}", fg="#F59E0B", activeforeground="#F59E0B",
            )
        else:
            self.bouton_alerte_dossier.config(text="⚠️", fg="#5578A0", activeforeground="#5578A0")

    def _afficher_alertes_articles_dossier(self):
        if self.dossier_actuel is None:
            return
        alertes = db.get_alertes_actives_dossier(self.dossier_actuel["id"])
        if not alertes:
            self._rafraichir_alerte_articles_dossier()
            return
        DialogueAlertesArticles(self.root, self, self.dossier_actuel["nom"], alertes)

    def _acquitter_alerte_article(self, alerte_id):
        """Marque une alerte comme vue/traitée -- appelée depuis
        DialogueAlertesArticles. Ne modifie STRICTEMENT que le statut de
        l'alerte : aucune analyse, aucun plan, aucun contenu du dossier
        n'est jamais touché par cette action (voir db.acquitter_alerte_article)."""
        db.acquitter_alerte_article(alerte_id)
        self._rafraichir_alerte_articles_dossier()

    def _nouveau_dossier(self):
        dialogue = DialogueNouveauDossier(self.root)
        self.root.wait_window(dialogue)
        if not dialogue.resultat:
            return
        r = dialogue.resultat
        db.create_dossier(nom=r["nom"], domaine=r["domaine"], faits=r["faits"], numero_dossier=r["numero_dossier"])
        self._rafraichir_dossiers()
        self.dossier_var.set(r["nom"])
        self._selectionner_dossier(None)

    def _selectionner_dossier(self, event):
        nom = self.dossier_var.get()
        self.dossier_actuel = self.dossiers_map.get(nom)
        if not self.dossier_actuel:
            return
        for b in self.boutons_actions:
            b.config(state="normal")
        self.label_dossier_actif.config(text=f"Dossier actif : {nom}")
        self._rafraichir_alerte_articles_dossier()
        self._afficher(f"→ Dossier sélectionné : {nom}\n", "titre")
        # Changer de dossier démarre implicitement une nouvelle conversation :
        # le contexte d'un autre dossier n'a pas de sens à mélanger ici.
        self.historique_question = []
        self.conversation_chat_id = None
        self._effacer_sortie(widget=self.zone_chat)

    # ---------- Utilitaires d'affichage et de tâches en arrière-plan ----------
    def _afficher(self, texte, tag=None, widget=None, saut_ligne=True):
        widget = widget if widget is not None else self.sortie
        widget.config(state="normal")

        def _inserer(contenu, tag_a_utiliser):
            if contenu:
                widget.insert("end", contenu, tag_a_utiliser) if tag_a_utiliser else widget.insert("end", contenu)

        # Balises [ART:...]/[JURISPRUDENCE:...]/[VERIF:...] (voir
        # analyse.REGLE_BALISAGE_CITATIONS) -- rendues en texte lisible avec
        # une mise en forme dédiée, comme le faisait l'ancien marqueur libre
        # "À VÉRIFIER" pour les documents antérieurs à ce chantier (repéré
        # ici via le même regex, jamais régénéré rétroactivement).
        texte = texte or ""
        if not _RE_TAG_TOUTE.search(texte) and "À VÉRIFIER" not in texte:
            _inserer((texte + "\n") if saut_ligne else texte, tag)
        else:
            pos = 0
            for segment_avant, brut in re.findall(r"(.*?)(\[(?:ART|JURISPRUDENCE|VERIF):[^\]]*\]|À VÉRIFIER)", texte, re.DOTALL):
                _inserer(segment_avant, tag)
                pos += len(segment_avant) + len(brut)
                m_verif = _RE_TAG_VERIF.fullmatch(brut)
                m_art = _RE_TAG_ART.fullmatch(brut)
                m_jur = _RE_TAG_JURISPRUDENCE.fullmatch(brut)
                if m_verif:
                    _inserer(f"À VÉRIFIER : {m_verif.group(1)}", "a_verifier")
                elif m_art:
                    _inserer(f"art. {m_art.group(1)} du {_CODES_LIBELLES.get(m_art.group(2), m_art.group(2))}", "citation")
                elif m_jur:
                    _inserer(m_jur.group(1), "citation")
                else:
                    _inserer(brut, "a_verifier")  # "À VÉRIFIER" hérité, texte antérieur à ce chantier
            fin = texte[pos:]
            _inserer((fin + "\n") if saut_ligne else fin, tag)
        widget.see("end")
        widget.config(state="disabled")

    def _effacer_sortie(self, widget=None):
        widget = widget if widget is not None else self.sortie
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.config(state="disabled")

    def _afficher_vue_sortie(self):
        self.frame_chat.pack_forget()
        self.frame_sortie.pack(fill="both", expand=True)

    def _afficher_vue_chat(self):
        self.frame_sortie.pack_forget()
        self.frame_chat.pack(fill="both", expand=True)
        self.entree_chat.focus_set()

    def _lancer_tache(self, fonction_tache, fonction_affichage, widget_erreur=None):
        """Exécute fonction_tache() dans un thread séparé (pour ne pas
        geler la fenêtre pendant un appel à l'API), puis appelle
        fonction_affichage(resultat) sur le thread principal. Affiche un
        indicateur animé avec le temps écoulé pour que l'attente ne
        semble jamais figée."""
        self._temps_debut_tache = __import__("time").time()
        self._animation_en_cours = True
        self._animer_statut()
        for b in self.boutons_actions:
            b.config(state="disabled")

        def travail():
            try:
                resultat = fonction_tache()
                self.root.after(0, lambda: self._fin_tache(fonction_affichage, resultat, None, widget_erreur))
            except Exception as e:
                # Python supprime automatiquement la variable `e` à la sortie
                # du bloc except — il faut la recopier avant que le lambda,
                # exécuté plus tard via root.after, ne tente d'y accéder.
                err = e
                self.root.after(0, lambda err=err: self._fin_tache(None, None, err, widget_erreur))

        threading.Thread(target=travail, daemon=True).start()

    def _animer_statut(self):
        if not getattr(self, "_animation_en_cours", False):
            return
        import time
        ecoule = int(time.time() - self._temps_debut_tache)
        points = "." * ((ecoule % 3) + 1)
        self.barre_statut.config(text=f"⏳ Traitement en cours{points} ({ecoule}s écoulées)")
        self.root.after(400, self._animer_statut)

    def _fin_tache(self, fonction_affichage, resultat, erreur, widget_erreur=None):
        self._animation_en_cours = False
        self.barre_statut.config(text="Prêt")
        for b in self.boutons_actions:
            b.config(state="normal")
        if erreur:
            messagebox.showerror("Une erreur est survenue", str(erreur))
            self._afficher(f"⚠ Erreur : {erreur}", "attention", widget=widget_erreur)
        else:
            fonction_affichage(resultat)

    # ---------- Générations en arrière-plan (ne s'interrompent jamais en changeant d'écran) ----------
    #
    # À la différence de _lancer_tache (au-dessus, pensé pour une action
    # rapide et strictement liée à l'écran qui l'a déclenchée -- le chat, la
    # commande en langage naturel), _lancer_generation est pour les
    # traitements longs (analyse, plan, plaidoirie, simulateur...) :
    #   - le dossier cible est figé au lancement (paramètre `dossier`),
    #     jamais relu depuis self.dossier_actuel à la fin ;
    #   - fonction_sauvegarde() est TOUJOURS appelée en cas de succès, quel
    #     que soit l'écran affiché à ce moment-là -- le résultat ne se perd
    #     donc jamais, contrairement à l'ancien code où l'enregistrement
    #     vivait dans la fonction d'affichage et lisait self.dossier_actuel
    #     en direct ;
    #   - fonction_affichage() n'est appelée (et le panneau de sortie mis à
    #     jour tout de suite) que si le dossier et l'écran affichés sont
    #     encore ceux de cette génération ; sinon, seul le badge 🔄 change,
    #     sans rien perturber de ce que l'utilisateur fait ailleurs ;
    #   - plusieurs générations peuvent tourner en parallèle (même dossier
    #     ou dossiers différents), chacune dans son propre thread, sans état
    #     partagé entre elles (contrairement à self.boutons_actions /
    #     self._animation_en_cours, qui sont globaux et à usage unique).

    def _cle_generation(self, dossier_id, feature):
        return (dossier_id, feature)

    def _lancer_generation(self, dossier, feature, libelle, fonction_tache, fonction_sauvegarde, fonction_affichage=None, widget_erreur=None):
        """Lance fonction_tache() dans un thread séparé pour `dossier`
        (dict complet, comme self.dossier_actuel) et `feature` (ex.
        "analyser", "plan"...). `dossier` peut être None pour les actions
        qui ne sont pas liées à un dossier précis (ex. consulter la
        jurisprudence sur une situation décrite librement) -- dans ce cas,
        aucune protection anti double-lancement n'est appliquée (rien ne
        permet de distinguer deux demandes différentes sans dossier), et
        fonction_sauvegarde reçoit dossier_id=None.

        Refuse silencieusement (avec un message) de relancer une génération
        identique déjà en cours pour le même dossier."""
        cle = self._cle_generation(dossier["id"], feature) if dossier is not None else None
        if cle is not None and cle in self._generations_actives_par_cle:
            messagebox.showinfo(
                "Génération déjà en cours",
                f"« {libelle} » est déjà en cours pour ce dossier — inutile de la relancer, "
                "le badge 🔄 en haut vous préviendra dès qu'elle sera prête.",
            )
            return

        gen = Generation(
            uuid.uuid4().hex,
            dossier["id"] if dossier is not None else None,
            dossier["nom"] if dossier is not None else None,
            feature, libelle, fonction_sauvegarde, fonction_affichage, widget_erreur,
        )
        # Écrit tout de suite en base (statut 'en_cours') -- avant même de
        # savoir si la génération va réussir -- pour que l'historique
        # persistant (db.generations) survive à un arrêt brutal de l'app,
        # pas seulement à une navigation entre écrans (voir Generation.db_id).
        gen.db_id = db.creer_generation(gen.dossier_id, feature, libelle)
        self.generations[gen.id] = gen
        if cle is not None:
            self._generations_actives_par_cle.add(cle)
        self._rafraichir_badge_generations()

        def travail():
            try:
                resultat = fonction_tache()
                self.root.after(0, lambda: self._generation_terminee(gen.id, resultat, None))
            except Exception as e:
                # Voir la même remarque dans _lancer_tache ci-dessus : `e`
                # doit être recopiée pour survivre jusqu'à l'exécution du
                # lambda, plus tard, sur le thread principal.
                err = e
                self.root.after(0, lambda err=err: self._generation_terminee(gen.id, None, err))

        threading.Thread(target=travail, daemon=True).start()

    def _generation_terminee(self, generation_id, resultat, erreur):
        gen = self.generations.get(generation_id)
        if gen is None:
            return  # garde-fou défensif, ne devrait pas arriver
        if gen.dossier_id is not None:
            self._generations_actives_par_cle.discard(self._cle_generation(gen.dossier_id, gen.feature))
        gen.horodatage_fin = time.time()

        if erreur is not None:
            # Le traitement IA lui-même a échoué -- rien n'a été généré, il
            # n'y a donc rien à perdre : seul db.generations.statut='erreur'
            # est écrit (contenu_json reste NULL).
            gen.statut = "erreur"
            gen.erreur = str(erreur)
            db.echouer_generation(gen.db_id, gen.erreur)
        else:
            # Le contenu existe : il est acquis dans l'historique persistant
            # AVANT toute tentative d'enregistrement dans une table annexe
            # (analyses, notes...) -- si celle-ci échoue plus bas, le
            # contenu n'est donc jamais perdu, seulement absent de cette
            # table-là (voir gen.avertissement, distinct de gen.erreur).
            gen.resultat = resultat
            gen.statut = "terminee"
            db.terminer_generation(gen.db_id, resultat)
            if gen.fonction_sauvegarde is not None:
                try:
                    gen.fonction_sauvegarde(gen.dossier_id, resultat)
                except Exception as e:
                    # Jamais silencieux (contrairement à l'ancien `except
                    # Exception: pass`) : signalé sans dégrader le statut
                    # global de la génération, qui a réussi.
                    gen.avertissement = f"Généré et conservé dans l'historique, mais pas enregistré dans le dossier : {e}"

        self._rafraichir_badge_generations()

        if gen.dossier_id is None:
            dossier_correspond = True  # génération non liée à un dossier -- pas de vérification à faire
        else:
            dossier_correspond = self.dossier_actuel is not None and self.dossier_actuel["id"] == gen.dossier_id
        ecran_correspond = dossier_correspond and self.ecran_actuel == gen.feature
        if not ecran_correspond:
            return  # le badge suffit -- rien à changer sur l'écran affiché
        if gen.statut == "terminee" and gen.fonction_affichage is not None:
            gen.fonction_affichage(resultat)
            if gen.avertissement:
                self._afficher(f"⚠ {gen.avertissement}", "attention", widget=gen.widget_erreur)
        elif gen.statut == "erreur":
            self._afficher(f"⚠ Erreur : {gen.erreur}", "attention", widget=gen.widget_erreur)

    def _rafraichir_badge_generations(self):
        en_cours = [g for g in self.generations.values() if g.statut == "en_cours"]
        non_lues = [g for g in self.generations.values() if g.statut in ("terminee", "erreur") and not g.lue]
        if en_cours:
            self.bouton_generations.config(text=f"🔄 {len(en_cours)}", fg=GOLD, activeforeground=GOLD)
        elif non_lues:
            self.bouton_generations.config(text=f"✅ {len(non_lues)}", fg=GOLD, activeforeground=GOLD)
        else:
            self.bouton_generations.config(text="🔄", fg="#5578A0", activeforeground="#5578A0")

    def _nom_dossier(self, dossier_id):
        """Nom actuel d'un dossier à partir de son id, ou None (dossier
        supprimé depuis, ou génération sans dossier) -- self.dossiers_map
        est indexé par nom, d'où la recherche inverse."""
        if dossier_id is None:
            return None
        return next((nom for nom, d in self.dossiers_map.items() if d["id"] == dossier_id), None)

    def _entrees_historique_generations(self):
        """Fusionne les générations de la session en cours (self.generations,
        qui savent réafficher leur résultat avec le rendu soigné d'origine)
        et l'historique persistant en base (db.generations, qui survit à un
        redémarrage de l'app) -- une seule ligne par génération, dédupliquée
        par db_id ; la version en mémoire est préférée quand les deux
        existent, c'est elle qui sait effectivement réafficher le résultat."""
        par_db_id = {}
        for row in db.list_generations():
            par_db_id[row["id"]] = EntreeHistorique(row, self._nom_dossier(row["dossier_id"]))
        for gen in self.generations.values():
            if gen.db_id is not None:
                par_db_id[gen.db_id] = gen
        return sorted(par_db_id.values(), key=lambda g: g.horodatage_debut, reverse=True)

    def _afficher_generations(self):
        entrees = self._entrees_historique_generations()
        if not entrees:
            messagebox.showinfo(
                "Générations",
                "Aucune génération en cours ni récente. Lancez une analyse, un plan, une plaidoirie... : "
                "ce badge, et l'historique qu'il ouvre, permettent de la retrouver même après avoir "
                "redémarré l'application.",
            )
            return
        DialogueGenerations(self.root, self, entrees)
        for g in self.generations.values():
            g.lue = True
        self._rafraichir_badge_generations()

    def _afficher_contenu_generique(self, contenu):
        """Rendu générique (JSON structuré -> texte lisible), utilisé quand
        le rendu soigné d'origine n'existe plus (résultat retrouvé dans
        l'historique persistant après redémarrage -- voir EntreeHistorique) :
        honnête plutôt que de fabriquer un faux rendu spécifique à la
        fonctionnalité."""
        import json as _json
        self._afficher(_json.dumps(contenu, ensure_ascii=False, indent=2))

    def _ouvrir_resultat_generation(self, gen):
        """Bascule sur le dossier et l'écran d'une génération terminée pour
        en afficher le résultat -- appelé depuis le bouton « Ouvrir » de
        DialogueGenerations. Ne fait rien si le dossier a entre-temps été
        supprimé (self.dossiers_map ne le contient plus) ; ne touche pas à
        la sélection de dossier pour une génération qui n'en avait pas
        (dossier_nom est alors None)."""
        if gen.statut != "terminee":
            return
        if gen.dossier_nom is not None and gen.dossier_nom in self.dossiers_map:
            self.dossier_var.set(gen.dossier_nom)
            self._selectionner_dossier(None)
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self.ecran_actuel = gen.feature
        if gen.fonction_affichage is not None:
            gen.fonction_affichage(gen.resultat)
        else:
            self._afficher(f"=== {gen.libelle} (historique) ===\n", "titre")
            self._afficher_contenu_generique(gen.resultat)

    def _supprimer_generation(self, gen):
        """Suppression DÉFINITIVE d'une entrée d'historique -- appelée
        uniquement depuis le bouton « Supprimer » de DialogueGenerations,
        déjà confirmé à ce stade. Jamais appelée automatiquement (pas
        d'expiration, pas de purge) -- voir db.supprimer_generation."""
        db.supprimer_generation(gen.db_id)
        en_memoire = next((g for g in self.generations.values() if g.db_id == gen.db_id), None)
        if en_memoire is not None:
            del self.generations[en_memoire.id]
        self._rafraichir_badge_generations()

    def _contexte_dossier(self):
        d = self.dossier_actuel
        parts = []
        if d.get("faits"):
            parts.append(f"Faits : {d['faits']}")
        if d.get("parties"):
            parts.append(f"Parties : {d['parties']}")
        analyses = db.get_analyses_for_dossier(d["id"])
        if analyses:
            derniere = analyses[0]
            parts.append("Arguments adverses déjà analysés :")
            for arg in derniere["arguments"]:
                parts.append(f"- [{arg.get('risque', '?')}] {arg.get('resume', '')}")
        return "\n".join(parts) if parts else f"Dossier « {d['nom']} », domaine : {d.get('domaine', '')}."

    # ---------- Barre de commande en langage naturel ----------
    def _placeholder_commande(self, entree):
        placeholder = "Indiquez l'action souhaitée, par exemple : « analyser ces conclusions » ou « établir un plan de 10 minutes »..."
        entree.insert(0, placeholder)
        entree.config(fg="#8FA3BC")

        def on_focus_in(event):
            if entree.get() == placeholder:
                entree.delete(0, "end")
                entree.config(fg="white")

        def on_focus_out(event):
            if not entree.get():
                entree.insert(0, placeholder)
                entree.config(fg="#8FA3BC")

        entree.bind("<FocusIn>", on_focus_in)
        entree.bind("<FocusOut>", on_focus_out)

    def _commande_naturelle(self):
        texte = self.commande_var.get().strip()
        if not texte or texte.startswith("Indiquez l'action souhaitée"):
            return
        if not self.dossier_actuel:
            messagebox.showinfo("Aucun dossier sélectionné", "Veuillez créer ou sélectionner un dossier avant de formuler une commande.")
            return

        self.commande_var.set("")
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher(f"Vous : « {texte} »\n", "titre")
        self._afficher("Interprétation de la demande...\n")

        def tache():
            return interpreter_intention(texte)

        def afficher(intention):
            action = intention.get("action", "menu")
            confiance = intention.get("confiance", "basse")
            reformulation = intention.get("reformulation", "")

            if reformulation:
                self._afficher(f"→ {reformulation}\n")

            if confiance == "basse" or action == "menu":
                self._afficher(
                    "Je ne suis pas certain d'avoir bien compris — utilisez les boutons à gauche, "
                    "ou reformulez votre demande.", "attention"
                )
                return

            mapping = {
                "analyser": lambda: self._action_analyser(),
                "resumer": lambda: self._action_resumer(),
                "plan": lambda: self._action_plan(duree_preremplie=intention.get("duree_minutes")),
                "simulateur": lambda: self._action_simulateur(),
                "note": lambda: self._action_note(),
            }
            fonction = mapping.get(action)
            if fonction:
                fonction()
            else:
                self._afficher("Cette demande ne correspond à aucune action disponible ici. Utilisez les boutons à gauche.", "attention")

        self._lancer_tache(tache, afficher)

    # ---------- Actions ----------
    def _action_analyser(self):
        dialogue = DialogueTexteLong(self.root, "Analyser des conclusions adverses", "Veuillez transmettre le texte des conclusions adverses :")
        self.root.wait_window(dialogue)
        if not dialogue.resultat:
            return
        texte = dialogue.resultat
        dossier = self.dossier_actuel  # figé ici -- voir Generation, jamais relu plus tard

        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher(
            "Analyse en cours...\nVous pouvez changer de dossier ou d'écran : le badge 🔄 en haut "
            "vous préviendra dès que ce sera prêt.\n"
        )
        self.ecran_actuel = "analyser"

        def tache():
            return analyse.analyser_conclusions(texte)

        def sauvegarder(dossier_id, result):
            db.save_analyse(dossier_id, result.get("arguments", []), result.get("points_attention", []))

        def afficher(result):
            self._effacer_sortie()
            self._afficher("=== ANALYSE DES CONCLUSIONS ADVERSES ===\n", "titre")
            for arg in result.get("arguments", []):
                risque = arg.get("risque", "?")
                tag = {"Élevé": "risque_eleve", "Moyen": "risque_moyen", "Faible": "risque_faible"}.get(risque, None)
                self._afficher(f"[{risque}] {arg.get('resume', '')}", tag)
                self._afficher(f"   Fondement : {arg.get('fondement', '')}")
                raisonnement = arg.get("raisonnement") or {}
                if raisonnement.get("probleme_de_droit"):
                    self._afficher(f"   Problème de droit : {raisonnement.get('probleme_de_droit', '')}")
                if raisonnement.get("regle_applicable"):
                    self._afficher(f"   Règle applicable : {raisonnement.get('regle_applicable', '')}")
                if raisonnement.get("application_aux_faits"):
                    self._afficher(f"   Application aux faits : {raisonnement.get('application_aux_faits', '')}")
                if arg.get("justification_risque"):
                    self._afficher(f"   Conclusion : {arg.get('justification_risque', '')}")
                for r in arg.get("refutations", []):
                    self._afficher(f"   → [{r.get('angle', '')}] {r.get('piste', '')}")
                self._afficher("")
            if result.get("points_attention"):
                self._afficher("Points d'attention :", "attention")
                for p in result["points_attention"]:
                    self._afficher(f"  - {p}")

        self._lancer_generation(dossier, "analyser", "Analyse des conclusions adverses", tache, sauvegarder, afficher, widget_erreur=self.sortie)

    def _action_resumer(self):
        dossier = self.dossier_actuel
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher("Génération du résumé en cours...\n")
        self.ecran_actuel = "resumer"
        contexte = self._contexte_dossier()

        def tache():
            return analyse.resumer_dossier(contexte)

        def afficher(result):
            self._effacer_sortie()
            self._afficher("=== RÉSUMÉ DU DOSSIER ===\n", "titre")
            self._afficher(result.get("resume_court", ""))
            self._afficher("")
            if result.get("points_cles"):
                self._afficher("Points clés :")
                for p in result["points_cles"]:
                    self._afficher(f"  • {p}")
                self._afficher("")
            if result.get("elements_manquants"):
                self._afficher("Éléments manquants :", "attention")
                for e in result["elements_manquants"]:
                    self._afficher(f"  - {e}")

        self._lancer_generation(dossier, "resumer", "Résumé du dossier", tache, None, afficher)

    def _action_plan(self, duree_preremplie=None):
        duree = duree_preremplie or simpledialog.askinteger("Plan de plaidoirie", "Temps de parole imparti (en minutes) :", minvalue=1, maxvalue=180)
        if not duree:
            return
        dossier = self.dossier_actuel
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher("Génération du plan en cours...\n")
        self.ecran_actuel = "plan"
        contexte = self._contexte_dossier()

        def tache():
            return analyse.generer_plan_plaidoirie(contexte, duree)

        def afficher(result):
            self._effacer_sortie()
            self._afficher("=== PLAN DE PLAIDOIRIE ===\n", "titre")
            self._afficher("🎤 ACCROCHE")
            self._afficher(result.get("accroche", "") + "\n")
            for i, point in enumerate(result.get("plan", []), 1):
                self._afficher(f"{i}. {point.get('point', '')} ({point.get('duree_minutes', '?')} min)", "titre")
                self._afficher(f"   Argument clé : {point.get('argument_cle', '')}")
                self._afficher(f"   Notes : {point.get('notes', '')}\n")
            self._afficher("🎤 CONCLUSION")
            self._afficher(result.get("conclusion", "") + "\n")
            if result.get("points_attention"):
                self._afficher("Points d'attention :", "attention")
                for p in result["points_attention"]:
                    self._afficher(f"  - {p}")

        self._lancer_generation(dossier, "plan", "Plan de plaidoirie", tache, None, afficher)

    def _action_simulateur(self):
        dossier = self.dossier_actuel
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher("Génération des questions probables en cours...\n")
        self.ecran_actuel = "simulateur"
        contexte = self._contexte_dossier()

        def tache():
            return analyse.simuler_objections(contexte)

        def afficher(result):
            self._effacer_sortie()
            self._afficher("=== QUESTIONS / OBJECTIONS PROBABLES ===\n", "titre")
            for i, obj in enumerate(result.get("objections", []), 1):
                self._afficher(f"{i}. [{obj.get('origine', '?')}] {obj.get('question', '')}", "titre")
                self._afficher(f"   Piège : {obj.get('piege', '')}")
                self._afficher(f"   Piste de réponse : {obj.get('piste_reponse', '')}\n")
            if result.get("point_le_plus_faible"):
                self._afficher("Point le plus faible du dossier :", "attention")
                self._afficher(f"  {result['point_le_plus_faible']}")

        self._lancer_generation(dossier, "simulateur", "Simulateur d'objections", tache, None, afficher)

    def _action_note(self):
        dialogue = DialogueTexteLong(self.root, "Prendre une note", "Saisissez votre note, quelle qu'en soit la forme ; l'agent se chargera de la structurer :")
        self.root.wait_window(dialogue)
        if not dialogue.resultat:
            return
        note_brute = dialogue.resultat
        dossier = self.dossier_actuel
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher("Structuration de la note en cours...\n")
        self.ecran_actuel = "note"

        def tache():
            return analyse.traiter_notes(note_brute)

        def sauvegarder(dossier_id, result):
            db.ajouter_note(
                dossier_id, note_brute,
                note_structuree=result.get("note_structuree", ""),
                actions=result.get("actions_a_faire", []),
                points=result.get("points_a_retenir", []),
            )

        def afficher(result):
            self._effacer_sortie()
            self._afficher("=== NOTE STRUCTURÉE ===\n", "titre")
            self._afficher(result.get("note_structuree", "") + "\n")
            if result.get("actions_a_faire"):
                self._afficher("Actions à faire :")
                for a in result["actions_a_faire"]:
                    self._afficher(f"  ☐ {a}")
                self._afficher("")
            if result.get("points_a_retenir"):
                self._afficher("Points à retenir :")
                for p in result["points_a_retenir"]:
                    self._afficher(f"  • {p}")

        self._lancer_generation(dossier, "note", "Note structurée", tache, sauvegarder, afficher)

    def _action_rapport_complet(self):
        duree = simpledialog.askinteger("Rapport complet", "Temps de parole pour le plan de plaidoirie, en minutes :", minvalue=1, maxvalue=180)
        dossier = self.dossier_actuel
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher("Génération du plan et du simulateur en parallèle...\n")
        self.ecran_actuel = "rapport_complet"
        contexte = self._contexte_dossier()
        analyses_existantes = db.get_analyses_for_dossier(dossier["id"])
        analyse_result = None
        if analyses_existantes:
            derniere = analyses_existantes[0]
            analyse_result = {"arguments": derniere["arguments"], "points_attention": derniere["points_attention"]}

        def tache():
            import concurrent.futures
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
            try:
                future_plan = executor.submit(analyse.generer_plan_plaidoirie, contexte, duree) if duree else None
                future_sim = executor.submit(analyse.simuler_objections, contexte)
                plan_result = future_plan.result() if future_plan else None
                sim_result = future_sim.result()
            finally:
                executor.shutdown(wait=False)
            return {"analyse": analyse_result, "plan": plan_result, "simulateur": sim_result}

        def afficher(resultats):
            self._effacer_sortie()
            self._afficher("=== RAPPORT COMPLET ===\n", "titre")
            if resultats["plan"]:
                self._afficher("--- Plan de plaidoirie ---", "titre")
                self._afficher(f"Accroche : {resultats['plan'].get('accroche', '')}\n")
                for i, point in enumerate(resultats["plan"].get("plan", []), 1):
                    self._afficher(f"{i}. {point.get('point', '')} ({point.get('duree_minutes', '?')} min)")
                    self._afficher(f"   {point.get('argument_cle', '')}")
                self._afficher("")
            if resultats["analyse"]:
                self._afficher(f"--- Analyse ({len(resultats['analyse'].get('arguments', []))} argument(s) adverse(s)) ---", "titre")
            self._afficher(f"--- Simulateur ({len(resultats['simulateur'].get('objections', []))} question(s)/objection(s)) ---\n", "titre")
            for i, obj in enumerate(resultats["simulateur"].get("objections", []), 1):
                self._afficher(f"{i}. [{obj.get('origine', '?')}] {obj.get('question', '')}")
                self._afficher(f"   Piste : {obj.get('piste_reponse', '')}")

        self._lancer_generation(dossier, "rapport_complet", "Rapport complet (plan + simulateur)", tache, None, afficher)

    def _action_analyser_style(self):
        dialogue = DialogueTexteLong(self.root, "Analyse stylistique", "Veuillez transmettre le texte des conclusions adverses à analyser :")
        self.root.wait_window(dialogue)
        if not dialogue.resultat:
            return
        texte = dialogue.resultat
        # besoin_dossier=False (voir self.categories) : pas de dossier figé,
        # cette analyse porte sur un texte collé, indépendamment de tout dossier.
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher("Analyse stylistique en cours...\n")
        self.ecran_actuel = "analyser_style"

        def tache():
            return analyse.analyser_style_adverse(texte)

        def afficher(result):
            self._effacer_sortie()
            self._afficher("=== ANALYSE STYLISTIQUE ET RHÉTORIQUE ===\n", "titre")
            sections = [
                ("langage_de_couverture", "🗣️ Langage de couverture (hedging)"),
                ("affirmations_absolues", "⚠️ Affirmations absolues risquées"),
                ("voix_passive_suspecte", "👤 Voix passive suspecte"),
                ("ruptures_registre", "📉 Ruptures de registre"),
            ]
            for cle, titre in sections:
                elements = result.get(cle, [])
                self._afficher(f"\n{titre} :", "titre")
                if elements:
                    for e in elements:
                        self._afficher(f"  « {e.get('citation', '')} »")
                        self._afficher(f"    → {e.get('commentaire', '')}")
                else:
                    self._afficher("  Rien de notable détecté.")
            if result.get("synthese_strategique"):
                self._afficher(f"\n💡 Synthèse stratégique :\n{result['synthese_strategique']}", "titre")
            self._afficher("\n⚡ Outil de réflexion stratégique, pas une preuve juridique.", "attention")

        self._lancer_generation(None, "analyser_style", "Analyse stylistique", tache, None, afficher)

    # ---------- La Chemise ----------
    def _action_historique_dossier(self):
        self._afficher_vue_sortie()
        self._effacer_sortie()
        analyses = db.get_analyses_for_dossier(self.dossier_actuel["id"])
        if not analyses:
            self._afficher("Aucune analyse enregistrée pour ce dossier.")
            return
        self._afficher(f"=== HISTORIQUE — {self.dossier_actuel['nom']} ===\n", "titre")
        for a in analyses:
            self._afficher(f"--- Analyse du {a['date']} ---", "titre")
            for arg in a["arguments"]:
                self._afficher(f"  [{arg.get('risque', '?')}] {arg.get('resume', '')}")
            self._afficher("")

    def _action_parcourir_dossiers(self):
        self._afficher_vue_sortie()
        self._effacer_sortie()
        dossiers = db.list_dossiers()
        if not dossiers:
            self._afficher("Aucun dossier enregistré.")
            return
        self._afficher("=== TOUS MES DOSSIERS ===\n", "titre")
        par_domaine = {}
        for d in dossiers:
            cle = d["domaine"] or "Domaine non précisé"
            par_domaine.setdefault(cle, []).append(d)
        for domaine in sorted(par_domaine.keys()):
            self._afficher(domaine, "titre")
            for d in par_domaine[domaine]:
                ref = f" (n° {d['numero_dossier']})" if d["numero_dossier"] else ""
                self._afficher(f"  {d['nom']}{ref} — statut : {d['statut']}")
            self._afficher("")

        terme = simpledialog.askstring("Recherche", "Rechercher un terme dans tous vos dossiers (laisser vide pour ignorer) :")
        if terme:
            resultats = db.rechercher_dans_dossiers(terme)
            self._afficher(f"\n=== RECHERCHE : « {terme} » ===\n", "titre")
            if not resultats:
                self._afficher("Aucun dossier ne contient ce terme.")
            for r in resultats:
                self._afficher(f"📁 {r['dossier']['nom']}", "titre")
                for champ, extrait in r["extraits"]:
                    self._afficher(f"   [{champ}] {extrait}")

    def _action_preparer_dossier(self):
        from tkinter import filedialog
        import extract as extract_module

        importes = 0
        while True:
            choix = messagebox.askquestion(
                "Préparer ce dossier",
                "Souhaitez-vous ajouter un document ?\n\nOui = sélectionner un fichier (PDF/Word/Excel/Image/Texte)\nNon = transmettre le texte directement",
                icon="question",
            )
            if choix == "yes":
                chemin = filedialog.askopenfilename(
                    title="Choisir un document",
                    filetypes=[("Documents", "*.pdf *.docx *.xlsx *.xls *.txt *.png *.jpg *.jpeg *.webp"), ("Tous les fichiers", "*.*")],
                )
                if not chemin:
                    break
                try:
                    texte = extract_module.extract_text(chemin)
                except Exception as e:
                    messagebox.showerror("Erreur d'import", str(e))
                    continue
                nom_fichier = chemin.split("/")[-1].split("\\")[-1]
                db.ajouter_aux_faits(self.dossier_actuel["id"], texte, source=nom_fichier)
                importes += 1
            else:
                dialogue = DialogueTexteLong(self.root, "Coller du texte", "Veuillez transmettre le texte à ajouter au dossier :")
                self.root.wait_window(dialogue)
                if not dialogue.resultat:
                    break
                db.ajouter_aux_faits(self.dossier_actuel["id"], dialogue.resultat, source="texte collé")
                importes += 1

            if not messagebox.askyesno("Continuer ?", "Souhaitez-vous ajouter un autre document à ce dossier ?"):
                break

        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher(f"✅ {importes} document(s) importé(s) dans « {self.dossier_actuel['nom']} ».", "titre")

    def _action_export_faits_bruts(self):
        import export as export_module
        try:
            chemin = export_module.exporter_faits_bruts_word(self.dossier_actuel)
            messagebox.showinfo("Export réussi", f"Faits bruts exportés :\n{chemin}")
        except Exception as e:
            messagebox.showerror("Erreur d'export", str(e))

    def _action_modifier_domaine(self):
        domaines = ["Prud'hommes", "Pénal", "Civil", "Commercial", "Bail commercial", "Famille / Divorce",
                    "Administratif", "Social", "Immobilier", "Autre"]
        dialogue = DialogueChoixListe(self.root, "Modifier le domaine", "Nouveau domaine du dossier :", domaines)
        self.root.wait_window(dialogue)
        nouveau = dialogue.resultat
        if nouveau is None:
            return
        db.update_domaine(self.dossier_actuel["id"], nouveau)
        self.dossier_actuel["domaine"] = nouveau
        self._rafraichir_dossiers()
        self.dossier_var.set(self.dossier_actuel["nom"])
        messagebox.showinfo("Domaine mis à jour", f"Nouveau domaine : {nouveau or 'non précisé'}")

    def _action_supprimer_dossier(self):
        nom = self.dossier_actuel["nom"]
        analyses = db.get_analyses_for_dossier(self.dossier_actuel["id"])
        confirme = messagebox.askyesno(
            "Suppression IRRÉVERSIBLE",
            f"Cette opération supprimera définitivement « {nom} » ainsi que {len(analyses)} analyse(s) associée(s).\n\n"
            "Cette action est irréversible. Souhaitez-vous poursuivre ?",
            icon="warning",
        )
        if not confirme:
            return
        db.delete_dossier(self.dossier_actuel["id"])
        self.dossier_actuel = None
        self.dossier_var.set("")
        self._rafraichir_dossiers()
        self.label_dossier_actif.config(text="Aucun dossier sélectionné")
        self._rafraichir_alerte_articles_dossier()
        for b in self.boutons_actions:
            b.config(state="disabled")
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher(f"✅ Dossier « {nom} » supprimé.", "titre")
    # ---------- Espace Greffier ----------
    # ---------- Le Grimoire ----------
    def _action_consulter_jurisprudence(self):
        dialogue = DialogueTexteLong(self.root, "Consulter la jurisprudence", "Veuillez décrire la situation sur laquelle vous souhaitez connaître la position de la jurisprudence :")
        self.root.wait_window(dialogue)
        if not dialogue.resultat:
            return
        question = dialogue.resultat

        buts = [
            "Décisions favorables à mon client",
            "Anticiper les décisions défavorables (adversaire)",
            "Comprendre l'état du droit — neutre",
            "Évaluer mes chances — vue équilibrée",
        ]
        dialogue_but = DialogueChoixListe(
            self.root, "Dans quel but ? (optionnel)",
            "Cela oriente comment les décisions trouvées seront classées et triées.\n"
            "Laissez vide pour une recherche neutre :",
            buts,
        )
        self.root.wait_window(dialogue_but)
        but = dialogue_but.resultat or ""

        source_active = getattr(self, "source_juridique_active", "Légifrance (France)")

        # besoin_dossier=False : une consultation de jurisprudence porte sur
        # une situation décrite librement, jamais sur un dossier en
        # particulier -- pas de dossier à figer ici.
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher(f"Juridiction active : {source_active}\n", "titre")
        self._afficher("Compréhension de la situation en cours...\n")
        self.ecran_actuel = "consulter_jurisprudence"

        def tache():
            import recherche_juridique as rj

            notions = analyse.identifier_notions_juridiques(question, but)
            mots_cles = notions.get("mots_cles_recherche") or []
            requete_recherche = " ".join(mots_cles) if mots_cles else question

            if source_active == "Légifrance (France)":
                contexte_live = rj.rechercher_contexte_juridique(requete_recherche)
                contexte_recherche = rj.formater_contexte_pour_prompt(contexte_live)
            else:
                textes = db.get_corpus_valide(source=source_active)
                if textes:
                    bloc = "\n".join(f"[{t['reference'] or 'sans référence'}] {t['contenu'][:2000]}" for t in textes)
                    contexte_recherche = f"--- Source : {source_active} ---\n{bloc}"
                else:
                    contexte_recherche = ""

            reponse = analyse.consulter_jurisprudence(
                question, contexte_recherche,
                qualification=notions.get("qualification_juridique", ""),
                but=notions.get("but", but),
            )
            return {"notions": notions, "reponse": reponse}

        def afficher(resultat):
            self._effacer_sortie()
            self._afficher(f"Juridiction active : {source_active}\n", "titre")
            notions = resultat["notions"]
            if notions.get("domaine"):
                self._afficher(f"Domaine identifié : {notions['domaine']}\n")
            self._afficher(resultat["reponse"])

        self._lancer_generation(None, "consulter_jurisprudence", f"Jurisprudence : « {question[:40]} »", tache, None, afficher, widget_erreur=self.sortie)

    def _action_collecter_jurisprudence(self):
        query = simpledialog.askstring("Collecter de la jurisprudence", "Mots-clés de recherche (ex. « licenciement faute grave ») :")
        if not query:
            return
        domaines = ["Prud'hommes", "Pénal", "Civil", "Commercial", "Bail commercial", "Famille / Divorce",
                    "Administratif", "Social", "Immobilier", "Autre"]
        dialogue = DialogueChoixListe(self.root, "Domaine", "Domaine associé (optionnel) :", domaines)
        self.root.wait_window(dialogue)
        domaine = dialogue.resultat or ""

        # besoin_dossier=False : la collecte alimente la file d'attente
        # commune de jurisprudence (db.add_jurisprudence), pas un dossier.
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher(f"Recherche Judilibre : « {query} »...\n")
        self.ecran_actuel = "collecter_jurisprudence"

        def tache():
            import judilibre
            return judilibre.collecter_jurisprudence(query=query, domaine=domaine, max_results=10)

        def sauvegarder(dossier_id, collectees):
            for c in collectees:
                db.add_jurisprudence(reference=c["reference"], resume=c["resume"], domaine=c["domaine"], source=c["source"], validee=False)

        def afficher(collectees):
            self._effacer_sortie()
            if not collectees:
                self._afficher("Aucun résultat.")
                return
            self._afficher(f"✅ {len(collectees)} décision(s) collectée(s), en attente de validation.", "titre")
            self._afficher("Utilisez « Gérer la jurisprudence » pour les relire et les valider avant qu'elles ne soient utilisables.")

        self._lancer_generation(None, "collecter_jurisprudence", f"Collecte Judilibre : « {query[:40]} »", tache, sauvegarder, afficher)

    def _action_gerer_jurisprudence(self):
        en_attente = db.get_jurisprudence_en_attente()
        if not en_attente:
            self._afficher_vue_sortie()
            self._effacer_sortie()
            self._afficher("Aucune référence en attente. Voici les références déjà validées :\n", "titre")
            for r in db.get_jurisprudence_validee():
                self._afficher(f"  {r['reference']} ({r['domaine'] or 'domaine non précisé'})")
            return
        DialogueGererListe(
            self.root, "Gérer la jurisprudence", en_attente,
            libelle=lambda r: f"{r['reference']} ({r['domaine'] or 'domaine non précisé'})\n{r['resume'][:150]}",
            sur_valider=lambda r: db.valider_jurisprudence(r["id"]),
            sur_rejeter=lambda r: db.rejeter_jurisprudence(r["id"]),
        )

    def _action_importer_texte_corpus(self):
        dialogue = DialogueImporterTexte(self.root)
        self.root.wait_window(dialogue)
        if not dialogue.resultat:
            return
        r = dialogue.resultat
        texte_id = db.ajouter_texte_corpus(
            source=r["source"], contenu=r["contenu"], pays=r["pays"], type_texte=r["type_texte"],
            domaine=r["domaine"], reference=r["reference"], date_texte=r["date_texte"], validee=False,
        )
        self._rafraichir_juridictions()
        messagebox.showinfo("Texte importé", f"Le texte a été importé (identifiant {texte_id}) et demeure en attente de validation.\nVeuillez utiliser « Gérer le corpus » pour procéder à sa validation.\n\nCette nouvelle source figure désormais dans le sélecteur « ⚖ Droit », en haut de l'écran.")

    def _action_gerer_corpus(self):
        en_attente = db.get_corpus_en_attente()
        if not en_attente:
            self._afficher_vue_sortie()
            self._effacer_sortie()
            sources = db.lister_sources_corpus()
            if not sources:
                self._afficher("Aucun texte dans le corpus multi-source pour l'instant.")
                return
            self._afficher(f"Aucun texte en attente. Sources déjà validées : {', '.join(sources)}\n", "titre")
            for t in db.get_corpus_valide():
                self._afficher(f"[{t['source']}] {t['reference'] or 'sans référence'} — {t['pays'] or 'pays non précisé'}")
            return
        DialogueGererListe(
            self.root, "Gérer le corpus multi-source", en_attente,
            libelle=lambda t: f"[{t['source']}] {t['reference'] or 'sans référence'} ({t['pays'] or 'pays non précisé'})\n{t['contenu'][:150]}",
            sur_valider=lambda t: db.valider_texte_corpus(t["id"]),
            sur_rejeter=lambda t: db.rejeter_texte_corpus(t["id"]),
        )

    # ---------- Le Carnet ----------
    def _action_consulter_notes(self):
        self._afficher_vue_sortie()
        self._effacer_sortie()
        notes = db.get_notes_dossier(self.dossier_actuel["id"])
        if not notes:
            self._afficher(f"Aucune note enregistrée pour « {self.dossier_actuel['nom']} ».")
            return
        self._afficher(f"=== NOTES — {self.dossier_actuel['nom']} ===\n", "titre")
        for n in notes:
            self._afficher(f"--- {n['date_creation']} ---", "titre")
            self._afficher(n["note_structuree"] or n["note_brute"])
            if n["actions"]:
                self._afficher("Actions :")
                for a in n["actions"]:
                    self._afficher(f"  ☐ {a}")
            self._afficher("")

    def _action_note_client(self):
        dossier = self.dossier_actuel
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher("Rédaction de la note client en cours...\n")
        self.ecran_actuel = "note_client"
        contexte = self._contexte_dossier()

        def tache():
            return analyse.rediger_note_client(contexte)

        def afficher(texte):
            self._effacer_sortie()
            self._afficher("=== NOTE CLIENT (langage simple) ===\n", "titre")
            self._afficher(texte)

        self._lancer_generation(dossier, "note_client", "Note client", tache, None, afficher)

    def _action_chronologie(self):
        dossier = self.dossier_actuel
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher("Construction de la chronologie en cours...\n")
        self.ecran_actuel = "chronologie"
        contexte = self._contexte_dossier()

        def tache():
            return analyse.construire_chronologie(contexte)

        def afficher(result):
            self._effacer_sortie()
            self._afficher(f"📅 Période couverte : {result.get('periode_couverte', 'non déterminée')}\n", "titre")
            for ev in result.get("evenements", []):
                self._afficher(f"  {ev.get('date', '?')} — {ev.get('evenement', '')}")
            if result.get("elements_manquants"):
                self._afficher("\nÉléments manquants :", "attention")
                for e in result["elements_manquants"]:
                    self._afficher(f"  - {e}")

        self._lancer_generation(dossier, "chronologie", "Chronologie de l'affaire", tache, None, afficher)

    def _action_extraction_document(self):
        dialogue = DialogueTexteLong(self.root, "Extraction d'éléments clés", "Veuillez transmettre le texte du document :")
        self.root.wait_window(dialogue)
        if not dialogue.resultat:
            return
        texte = dialogue.resultat
        # besoin_dossier=False : extraction sur un texte collé, indépendante de tout dossier.
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher("Extraction en cours...\n")
        self.ecran_actuel = "extraction_document"

        def tache():
            return analyse.extraire_elements_cles(texte)

        def afficher(result):
            self._effacer_sortie()
            self._afficher("=== ÉLÉMENTS CLÉS EXTRAITS ===\n", "titre")
            for cle, libelle in [("dates", "Dates"), ("personnes_et_parties", "Personnes et parties"),
                                  ("references", "Références"), ("demandes", "Demandes"), ("decisions", "Décisions")]:
                self._afficher(f"{libelle} :", "titre")
                valeurs = result.get(cle, [])
                if valeurs:
                    for v in valeurs:
                        self._afficher(f"  • {v}")
                else:
                    self._afficher("  (aucun élément identifié)")
                self._afficher("")

        self._lancer_generation(None, "extraction_document", "Extraction d'éléments clés", tache, None, afficher)

    def _action_classement_document(self):
        dialogue = DialogueTexteLong(self.root, "Classement automatique", "Veuillez transmettre le texte du document :")
        self.root.wait_window(dialogue)
        if not dialogue.resultat:
            return
        texte = dialogue.resultat
        # besoin_dossier=False : classement d'un texte collé, indépendant de tout dossier.
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher("Classement en cours...\n")
        self.ecran_actuel = "classement_document"

        def tache():
            return analyse.classifier_document(texte)

        def afficher(result):
            self._effacer_sortie()
            self._afficher(f"📂 Nature : {result.get('nature', 'autre')}\n", "titre")
            self._afficher(f"   Confiance : {result.get('confiance', 'Faible')}")
            self._afficher(f"   Justification : {result.get('justification', '')}")

        self._lancer_generation(None, "classement_document", "Classement automatique", tache, None, afficher)

    def _action_analyser_requisitoire(self):
        dialogue = DialogueTexteLong(self.root, "Analyser un réquisitoire", "Veuillez transmettre le texte du réquisitoire :")
        self.root.wait_window(dialogue)
        if not dialogue.resultat:
            return
        texte = dialogue.resultat
        # besoin_dossier=False : analyse d'un texte collé, indépendante de tout dossier.
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher("Analyse du réquisitoire en cours...\n")
        self.ecran_actuel = "analyser_requisitoire"

        def tache():
            return analyse.analyser_requisitoire(texte)

        def afficher(result):
            self._effacer_sortie()
            self._afficher("=== RÉQUISITOIRE — ÉLÉMENTS STRUCTURÉS ===\n", "titre")
            self._afficher(f"Qualification retenue : {result.get('qualification_retenue', '') or '(non précisée)'}\n")
            for cle, libelle in [
                ("faits_et_elements_invoques", "Faits et éléments invoqués"),
                ("circonstances_aggravantes", "Circonstances aggravantes"),
                ("circonstances_attenuantes", "Circonstances atténuantes"),
            ]:
                valeurs = result.get(cle, [])
                if valeurs:
                    self._afficher(f"{libelle} :", "titre")
                    for v in valeurs:
                        self._afficher(f"  • {v}")
                    self._afficher("")
            self._afficher(f"Peine requise : {result.get('peine_requise', 'non précisée')}\n")
            if result.get("points_attention"):
                self._afficher("Points d'attention :", "attention")
                for p in result["points_attention"]:
                    self._afficher(f"  - {p}")

        self._lancer_generation(None, "analyser_requisitoire", "Analyse du réquisitoire", tache, None, afficher)

    def _action_rapport_instruction(self):
        dialogue = DialogueTexteLong(self.root, "Rapport d'instruction", "Veuillez transmettre le texte du rapport d'instruction :")
        self.root.wait_window(dialogue)
        if not dialogue.resultat:
            return
        texte = dialogue.resultat
        # besoin_dossier=False : analyse d'un texte collé, indépendante de tout dossier.
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher("Analyse du rapport d'instruction en cours...\n")
        self.ecran_actuel = "rapport_instruction"

        def tache():
            return analyse.analyser_rapport_instruction(texte)

        def afficher(result):
            self._effacer_sortie()
            self._afficher("=== RAPPORT D'INSTRUCTION — ÉLÉMENTS STRUCTURÉS ===\n", "titre")
            for cle, libelle in [
                ("actes_instruction", "Actes d'instruction"),
                ("elements_a_charge", "Éléments à charge"),
                ("elements_a_decharge", "Éléments à décharge"),
                ("mesures_ordonnees", "Mesures ordonnées"),
            ]:
                valeurs = result.get(cle, [])
                if valeurs:
                    self._afficher(f"{libelle} :", "titre")
                    for v in valeurs:
                        self._afficher(f"  • {v}")
                    self._afficher("")
            self._afficher(f"Sens proposé : {result.get('sens_propose', 'non précisé')}\n")
            if result.get("points_attention"):
                self._afficher("Points d'attention :", "attention")
                for p in result["points_attention"]:
                    self._afficher(f"  - {p}")

        self._lancer_generation(None, "rapport_instruction", "Rapport d'instruction", tache, None, afficher)

    def _action_rechercher_transversal(self):
        terme = simpledialog.askstring("Recherche transversale", "Terme à rechercher dans toutes les affaires :")
        if not terme:
            return
        self._afficher_vue_sortie()
        self._effacer_sortie()
        resultats = db.rechercher_dans_dossiers(terme)
        if not resultats:
            self._afficher(f"Aucune affaire ne contient « {terme} ».")
            return
        self._afficher(f"=== RECHERCHE : « {terme} » ===\n", "titre")
        for r in resultats:
            self._afficher(f"📁 {r['dossier']['nom']}", "titre")
            for champ, extrait in r["extraits"]:
                self._afficher(f"   [{champ}] {extrait}")
            self._afficher("")

    def _action_pv_audience(self):
        dialogue = DialogueTexteLong(self.root, "Procès-verbal d'audience", "Veuillez transmettre ou saisir les notes prises pendant l'audience :")
        self.root.wait_window(dialogue)
        if not dialogue.resultat:
            return
        notes = dialogue.resultat
        # besoin_dossier=False : rédaction à partir de notes libres, indépendante de tout dossier.
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher("Rédaction de la première version du PV en cours...\n")
        self.ecran_actuel = "pv_audience"

        def tache():
            return analyse.rediger_pv(notes)

        def afficher(pv):
            self._effacer_sortie()
            self._afficher("=== PREMIÈRE VERSION DU PV — à relire et compléter ===\n", "titre")
            self._afficher(pv)

        self._lancer_generation(None, "pv_audience", "Procès-verbal d'audience", tache, None, afficher)

    def _action_verification_procedurale(self):
        dossier = self.dossier_actuel
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher("Vérification procédurale en cours...\n")
        self.ecran_actuel = "verification_procedurale"
        contexte = self._contexte_dossier()

        def tache():
            return analyse.verifier_procedure(contexte)

        def afficher(result):
            self._effacer_sortie()
            if result.get("echeances_identifiees"):
                self._afficher("📅 Échéances identifiées :", "titre")
                for ech in result["echeances_identifiees"]:
                    self._afficher(f"  [{ech.get('statut', '?')}] {ech.get('echeance', '')} — {ech.get('date', 'date non précisée')}")
                self._afficher("")
            if result.get("actes_potentiellement_manquants"):
                self._afficher("⚠️ Actes potentiellement manquants :", "attention")
                for a in result["actes_potentiellement_manquants"]:
                    self._afficher(f"  • {a}")
                self._afficher("")
            if result.get("points_attention"):
                self._afficher("🔍 Points d'attention :", "titre")
                for p in result["points_attention"]:
                    self._afficher(f"  - {p}")
            if not any([result.get("echeances_identifiees"), result.get("actes_potentiellement_manquants"), result.get("points_attention")]):
                self._afficher("Aucune échéance ni anomalie identifiée dans le contenu disponible.")

        self._lancer_generation(dossier, "verification_procedurale", "Vérification procédurale", tache, None, afficher)

    def _action_controle_coherence(self):
        documents = []
        while True:
            dialogue = DialogueTexteLong(
                self.root, f"Document {len(documents) + 1}",
                f"Collez le texte du document {len(documents) + 1} (au moins 2 documents nécessaires) :",
            )
            self.root.wait_window(dialogue)
            if not dialogue.resultat:
                if len(documents) < 2:
                    messagebox.showwarning("Documents insuffisants", "Au moins deux documents sont requis pour procéder à un contrôle de cohérence.")
                break
            nom = simpledialog.askstring("Nom du document", f"Nom/référence pour ce document {len(documents) + 1} :") or f"Document {len(documents) + 1}"
            try:
                elements = analyse.extraire_elements_cles(dialogue.resultat)
            except Exception as e:
                messagebox.showerror("Erreur d'extraction", str(e))
                continue
            documents.append({"nom_document": nom, "elements": elements})
            if len(documents) >= 2 and not messagebox.askyesno("Continuer ?", "Souhaitez-vous ajouter un autre document ?"):
                break

        if len(documents) < 2:
            return

        # besoin_dossier=False : comparaison de textes collés, indépendante de tout dossier.
        self._afficher_vue_sortie()
        self._effacer_sortie()
        self._afficher(f"Comparaison de {len(documents)} documents en cours...\n")
        self.ecran_actuel = "controle_coherence"

        def tache():
            return analyse.controler_coherence(documents)

        def afficher(result):
            self._effacer_sortie()
            if result.get("contradictions"):
                self._afficher("⚠️ Contradictions détectées :", "attention")
                for c in result["contradictions"]:
                    self._afficher(f"\n  [{c.get('gravite', '?')}] {c.get('sujet', '')}")
                    self._afficher(f"     → {c.get('document_1', '')}")
                    self._afficher(f"     → {c.get('document_2', '')}")
                self._afficher("")
            else:
                self._afficher("✅ Aucune contradiction détectée entre les éléments extraits.\n", "titre")
            if result.get("elements_coherents"):
                self._afficher("Éléments cohérents entre documents :", "titre")
                for e in result["elements_coherents"]:
                    self._afficher(f"  • {e}")
            if result.get("limites_analyse"):
                self._afficher(f"\n⚡ Limites de cette analyse : {result['limites_analyse']}", "attention")

        self._lancer_generation(None, "controle_coherence", "Contrôle de cohérence entre documents", tache, None, afficher)

    def _construire_panneau_intelligence_vide(self):
        """(Re)construit le panneau « Intelligence juridique » à droite du
        chat, dans son état initial avant toute réponse."""
        for widget in self.panneau_intelligence.winfo_children():
            widget.destroy()
        tk.Label(
            self.panneau_intelligence, text="INTELLIGENCE JURIDIQUE", font=("Segoe UI", 9, "bold"),
            fg=GRAY, bg="#EEF1F6", wraplength=190, justify="left",
        ).pack(anchor="w", padx=14, pady=(16, 10))
        tk.Label(
            self.panneau_intelligence, text="S'actualise après chaque réponse de l'agent.",
            font=("Segoe UI", 9), fg=GRAY, bg="#EEF1F6", wraplength=190, justify="left",
        ).pack(anchor="w", padx=14)

    def _mettre_a_jour_panneau_intelligence(self, reponse, recherche_live, n_articles=0, n_jurisprudence=0):
        """Met à jour le panneau à droite du chat avec des faits vérifiables
        sur la dernière réponse — pas une auto-évaluation du modèle, mais
        des éléments qu'on peut réellement compter : sources effectivement
        trouvées en direct, nombre de balises [VERIF:...] (voir
        analyse.REGLE_BALISAGE_CITATIONS) dans la réponse. Un compteur élevé
        est un signal de prudence honnête, pas un défaut à cacher."""
        for widget in self.panneau_intelligence.winfo_children():
            widget.destroy()

        tk.Label(
            self.panneau_intelligence, text="INTELLIGENCE JURIDIQUE", font=("Segoe UI", 9, "bold"),
            fg=GRAY, bg="#EEF1F6", wraplength=190, justify="left",
        ).pack(anchor="w", padx=14, pady=(16, 10))

        def ligne(symbole, texte, couleur):
            tk.Label(
                self.panneau_intelligence, text=f"{symbole}  {texte}", font=("Segoe UI", 9),
                fg=couleur, bg="#EEF1F6", wraplength=190, justify="left", anchor="w",
            ).pack(anchor="w", padx=14, pady=3)

        if recherche_live:
            if n_articles > 0:
                ligne("✓", f"{n_articles} article(s) de loi trouvé(s)", "#3D8B5A")
            else:
                ligne("○", "Aucun article de loi trouvé en direct", GRAY)
            if n_jurisprudence > 0:
                ligne("✓", f"{n_jurisprudence} décision(s) de jurisprudence trouvée(s)", "#3D8B5A")
            else:
                ligne("○", "Aucune jurisprudence trouvée en direct", GRAY)
        else:
            ligne("○", "Recherche live désactivée pour cette question", GRAY)

        nb_a_verifier = len(_RE_TAG_VERIF.findall(reponse)) + reponse.count("À VÉRIFIER")
        if nb_a_verifier == 0:
            ligne("✓", "Aucune balise [VERIF:...] dans la réponse", "#3D8B5A")
        else:
            pluriel = "s" if nb_a_verifier > 1 else ""
            ligne("⚠", f"{nb_a_verifier} point{pluriel} « À VÉRIFIER » — à contrôler avant usage", "#B3261E")

        tk.Frame(self.panneau_intelligence, bg="#EEF1F6", height=8).pack()
        tk.Label(
            self.panneau_intelligence,
            text="Ces indicateurs sont calculés à partir du contenu réel de la réponse, "
                 "pas d'une auto-évaluation du modèle.",
            font=("Segoe UI", 8), fg=GRAY, bg="#EEF1F6", wraplength=190, justify="left",
        ).pack(anchor="w", padx=14, pady=(10, 0))

    def _nouvelle_conversation(self):
        """Réinitialise explicitement le fil de discussion — comme ouvrir un
        nouveau chat sur Claude.ai. La conversation précédente reste
        enregistrée telle quelle (sauvegarde déjà faite au fil de l'eau),
        retrouvable depuis « Historique des conversations »."""
        self.historique_question = []
        self.conversation_chat_id = None
        self._effacer_sortie(widget=self.zone_chat)
        self._construire_panneau_intelligence_vide()
        self._afficher(
            "Formulez votre question ci-dessous. La conversation demeure active tant que "
            "vous ne cliquez pas sur « Nouvelle conversation ».\n",
            "titre", widget=self.zone_chat,
        )
        self.entree_chat.focus_set()

    def _sauvegarder_conversation_chat(self):
        """Sauvegarde silencieuse de la conversation en cours — appelée
        après chaque réponse de l'agent, sans action de l'avocat, comme
        Claude.ai enregistre chaque discussion automatiquement."""
        if not self.historique_question:
            return
        if self.conversation_chat_id is None:
            premier_message_utilisateur = next(
                (m["content"] for m in self.historique_question if m["role"] == "user"), ""
            )
            titre = premier_message_utilisateur.strip().replace("\n", " ")[:60]
            if len(premier_message_utilisateur.strip()) > 60:
                titre += "…"
            titre = titre or "Conversation sans titre"
            self.conversation_chat_id = db.creer_conversation_chat(titre, self.historique_question)
        else:
            db.mettre_a_jour_conversation_chat(self.conversation_chat_id, self.historique_question)

    def _action_historique_conversations(self):
        """Ouvre la liste des conversations enregistrées — rouvrir ou
        supprimer, comme la liste des discussions passées sur Claude.ai."""
        conversations = db.lister_conversations_chat()
        if not conversations:
            messagebox.showinfo("Historique des conversations", "Aucune conversation enregistrée pour l'instant.")
            return

        taille = db.taille_base_octets()
        taille_lisible = f"{taille / 1024:.0f} Ko" if taille < 1024 * 1024 else f"{taille / (1024 * 1024):.1f} Mo"

        def libelle(c):
            date_aff = c["date_modification"][:16].replace("T", " ")
            return f"{c['titre']}\n{date_aff}"

        def ouvrir(c):
            enregistree = db.get_conversation_chat(c["id"])
            if not enregistree:
                return
            self.historique_question = enregistree["historique"]
            self.conversation_chat_id = enregistree["id"]
            self._afficher_vue_chat()
            self._effacer_sortie(widget=self.zone_chat)
            self._construire_panneau_intelligence_vide()
            for message in self.historique_question:
                if message["role"] == "user":
                    self._afficher(f"Vous : {message['content']}\n", "titre", widget=self.zone_chat)
                else:
                    self._afficher("Assistant :", "titre", widget=self.zone_chat)
                    self._afficher(message["content"] + "\n", widget=self.zone_chat)

        def supprimer(c):
            db.supprimer_conversation_chat(c["id"])
            if self.conversation_chat_id == c["id"]:
                self.conversation_chat_id = None

        DialogueHistoriqueConversations(
            self.root, f"Historique des conversations — base : {taille_lisible}",
            conversations, libelle=libelle, sur_ouvrir=ouvrir, sur_supprimer=supprimer,
        )

    def _action_question(self):
        """Bascule vers la vue chat. Si aucune conversation n'est en cours,
        on affiche le message d'accueil ; sinon on retrouve le fil déjà là."""
        self._afficher_vue_chat()
        if not self.historique_question:
            self._afficher(
                "Formulez votre question ci-dessous. La conversation demeure active tant que "
                "vous ne cliquez pas sur « Nouvelle conversation ».\n",
                "titre", widget=self.zone_chat,
            )

    def _coller_texte_long_chat(self):
        """Ouvre une grande zone de saisie — avec import de fichier ou
        collage de texte — pour envoyer un texte long dans le chat
        (réquisitoire, conclusions, jugement...), la barre de saisie en
        une ligne n'étant pas adaptée à ça."""
        dialogue = DialogueTexteLong(
            self.root, "Importer ou coller un texte long",
            "Importez un fichier ou collez ici le texte à analyser (réquisitoire, "
            "conclusions, jugement...) — il sera envoyé comme message dans la conversation :",
        )
        self.root.wait_window(dialogue)
        if not dialogue.resultat:
            return
        self._afficher_vue_chat()
        self.chat_var.set(dialogue.resultat)
        self._envoyer_message_chat()

    def _envoyer_message_chat(self):
        if getattr(self, "_chat_stream_en_cours", False):
            return  # Une réponse est déjà en cours de génération.

        question = self.chat_var.get().strip()
        if not question:
            return

        self.chat_var.set("")
        self.historique_question.append({"role": "user", "content": question})
        self._afficher(f"Vous : {question}\n", "titre", widget=self.zone_chat)
        self._afficher("Assistant :", "titre", widget=self.zone_chat)

        # Snapshot de l'historique au moment de l'envoi, pour que la tâche
        # en arrière-plan ne soit pas affectée si l'utilisateur relance vite.
        historique_envoi = list(self.historique_question)
        fragments_recus = []
        # Petit tampon pour ne jamais couper une balise [ART:...]/
        # [JURISPRUDENCE:...]/[VERIF:...] (voir analyse.REGLE_BALISAGE_CITATIONS)
        # entre deux fragments reçus du flux (ce qui empêcherait son rendu
        # dédié dans _afficher). On ne libère à l'affichage que ce qui est
        # certainement "sûr" : si le texte reçu se termine par un "[" sans
        # "]" après lui, tout à partir de ce "[" reste en réserve jusqu'au
        # fragment suivant -- une balise ne peut pas être reconnue tant
        # qu'elle n'est pas complète. Le même tampon retient aussi l'état
        # "en gras" (**...**) d'un fragment à l'autre, puisqu'un passage en
        # gras peut s'étaler sur plusieurs fragments reçus successivement.
        tampon = {"texte": "", "gras": False}

        self._chat_stream_en_cours = True
        self.entree_chat.config(state="disabled")
        recherche_live = self.recherche_live_var.get()
        compteurs = {"n_articles": 0, "n_jurisprudence": 0}

        def flush_tampon(force=False):
            texte = tampon["texte"]
            if force:
                a_afficher, reste = texte, ""
            else:
                pos_ouverture = texte.rfind("[")
                if pos_ouverture != -1 and "]" not in texte[pos_ouverture:]:
                    a_afficher, reste = texte[:pos_ouverture], texte[pos_ouverture:]
                else:
                    a_afficher, reste = texte, ""
            tampon["texte"] = reste
            if a_afficher:
                # Interprète les marqueurs **gras** du markdown plutôt que
                # de les afficher tels quels — l'état bascule à chaque
                # occurrence et persiste correctement entre deux appels.
                morceaux = a_afficher.split("**")
                for i, morceau in enumerate(morceaux):
                    if morceau:
                        tag = "gras" if tampon["gras"] else None
                        self._afficher(morceau, tag=tag, widget=self.zone_chat, saut_ligne=False)
                    if i < len(morceaux) - 1:
                        tampon["gras"] = not tampon["gras"]

        def travail():
            try:
                source_active = getattr(self, "source_juridique_active", "Légifrance (France)")
                contexte_recherche = (
                    f"\n\nContexte juridictionnel par défaut réglé par l'avocat dans les paramètres : {source_active}. "
                    "Utilise ce cadre par défaut pour répondre si la question ne précise rien d'autre. "
                    "Mais si la question mentionne clairement un autre pays ou système juridique, "
                    "privilégie ce que la question indique explicitement plutôt que ce réglage par défaut."
                )
                if recherche_live:
                    self.root.after(0, lambda: self._afficher(
                        "🔍 Recherche en direct sur Légifrance et Judilibre...\n", widget=self.zone_chat
                    ))
                    import recherche_juridique as rj
                    contexte_live = rj.rechercher_contexte_juridique(question)
                    contexte_recherche += "\n\n" + rj.formater_contexte_pour_prompt(contexte_live)
                    n_articles = len(contexte_live.get("articles_loi", []))
                    n_jurisprudence = len(contexte_live.get("jurisprudence", []))
                    compteurs["n_articles"] = n_articles
                    compteurs["n_jurisprudence"] = n_jurisprudence
                    self.root.after(0, lambda: self._afficher(
                        f"  → {n_articles} article(s) de loi, {n_jurisprudence} décision(s) trouvés.\n",
                        widget=self.zone_chat,
                    ))

                for fragment in analyse.repondre_conversation_stream(historique_envoi, contexte_recherche=contexte_recherche):
                    fragments_recus.append(fragment)
                    tampon["texte"] += fragment
                    self.root.after(0, flush_tampon)
                self.root.after(0, lambda: (flush_tampon(force=True), self._fin_streaming_chat(
                    "".join(fragments_recus), recherche_live=recherche_live, compteurs=compteurs,
                )))
            except Exception as e:
                # Même précaution que dans _lancer_tache : `e` est supprimée
                # par Python à la sortie du except, donc on la recopie avant
                # que le lambda (exécuté plus tard) n'essaie d'y accéder.
                err = e
                self.root.after(0, lambda err=err: (flush_tampon(force=True), self._fin_streaming_chat(None, erreur=err)))

        threading.Thread(target=travail, daemon=True).start()

    def _fin_streaming_chat(self, reponse, erreur=None, recherche_live=False, compteurs=None):
        self._chat_stream_en_cours = False
        self.entree_chat.config(state="normal")
        self.entree_chat.focus_set()
        if erreur:
            messagebox.showerror("Une erreur est survenue", str(erreur))
            self._afficher(f"\n⚠ Erreur : {erreur}\n", "attention", widget=self.zone_chat)
            return
        self._afficher("\n", widget=self.zone_chat)
        self.historique_question.append({"role": "assistant", "content": reponse})
        self._sauvegarder_conversation_chat()
        compteurs = compteurs or {}
        self._mettre_a_jour_panneau_intelligence(
            reponse, recherche_live,
            n_articles=compteurs.get("n_articles", 0),
            n_jurisprudence=compteurs.get("n_jurisprudence", 0),
        )


def main():
    db.init_db()
    # Toute génération restée 'en_cours' en base ne peut venir que d'un
    # arrêt brutal de l'app lors d'un lancement précédent -- voir
    # db.marquer_generations_en_cours_comme_interrompues (aucun thread ne
    # peut légitimement y travailler encore, le processus vient de démarrer).
    db.marquer_generations_en_cours_comme_interrompues()
    root = tk.Tk()
    app = PlaidIAApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
