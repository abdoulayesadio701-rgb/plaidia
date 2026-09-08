# Audit et infrastructure import/export — Plaid'IA

Audit complet des fonctionnalités pouvant bénéficier d'import/export de
fichiers, puis implémentation progressive d'une infrastructure réutilisable
(§10 de la demande initiale : « éviter de créer six systèmes différents »).

## Ce qui existait déjà (avant ce chantier)

- `extract.py` : extraction de texte PDF/DOCX/XLSX/images, détection de PDF
  scanné (`DocumentNumeriseError`).
- `backend/app/routers/dossiers.py::_extraire_texte_upload` (désormais
  `app.deps.extraire_texte_upload`, voir §Architecture) : validation
  extension/taille (20 Mo), fichier temporaire, extraction, nettoyage.
- Import dupliqué à l'identique dans 6 pages (même constante
  `EXTENSIONS_ACCEPTEES`, même bouton 📎) : Analyser conclusions, Analyse
  stylistique, Classement, Cohérence, Extraction, PV d'audience.
- `PreparerDossierPage` : le prototype le plus abouti (drag & drop,
  multi-fichiers, progression réelle, suivi par fichier) — base de
  l'extraction en composants réutilisables.
- Export Word/PDF pour conclusions, rapport complet, note client, faits
  bruts, PV d'audience. Aucun export CSV, aucune fonctionnalité tabulaire
  exportée en tableur.

## Classification (A/B/C/D)

**A. Nécessitaient clairement l'import** — Chat juridique (pièce jointe),
Gérer le corpus (fichier au lieu de texte collé), Traduire un texte (P1,
non fait dans cette passe), Consulter la jurisprudence (P2, non fait).

**B. Nécessitaient clairement l'export** — Simulateur d'objections,
Chronologie automatique, Vérification procédurale, Analyse stylistique (P2,
non fait).

**C. Bénéficieraient des deux** — Traduire un texte (P1, non fait).

**D. Import/export inutile** — Parcourir mes dossiers, Collecter/Gérer la
jurisprudence, Prendre une note, Rechercher dans toutes les affaires,
Classement automatique (résultat non exportable en soi).

## Architecture mise en place

**Frontend** (`frontend/src/lib/fichiers.ts`, `components/FileDropZone.tsx`,
`hooks/useImportFichiers.ts`, `components/FileImportListe.tsx`) : une seule
zone de dépôt réutilisable (variante complète pour un import mis en avant,
compacte pour un bouton secondaire à côté d'un textarea), un seul hook pour
le suivi multi-fichiers avec progression, une seule constante
`EXTENSIONS_DOCUMENT`. `PreparerDossierPage` (le prototype d'origine) et les
6 pages qui dupliquaient l'import ont été refaites dessus — comportement
inchangé, code centralisé.

**Backend** (`backend/app/deps.py::extraire_texte_upload`) : la logique de
validation/extraction, déplacée de `routers/dossiers.py` (où elle était
privée) vers `deps.py` (partagé), pour être réutilisée par le corpus
juridique sans dupliquer la validation MIME/taille/format. `export.py::
exporter_csv` : nouvelle fonction générique pour les résultats tabulaires,
même convention que `exporter_texte_libre_word`.

## Implémenté dans cette passe (dans l'ordre)

1. **Infrastructure générique** — composants/hooks ci-dessus, aucune
   fonctionnalité cassée (comportement byte-identique vérifié).
2. **Chat juridique — pièce jointe** (P0) : bouton « 📎 Joindre un
   fichier », chips avant envoi, texte extrait injecté dans le message
   envoyé sous un en-tête `--- Document joint : X ---` (même convention que
   `construire_contexte_dossier`/`controler_coherence`) — le contenu reste
   une DONNÉE, jamais une instruction. Si un dossier est actif, réutilise
   `importerDocument` (le texte est aussi ajouté aux faits, comme partout
   ailleurs) ; sinon `extraireFichier`.
3. **Corpus juridique — import de fichier** (P0) : nouvel endpoint
   `POST /api/jurisprudence/corpus/importer-fichier` (multipart), bascule
   « Coller le texte » / « Importer un fichier » dans `GererCorpusPage`.
4. **Exports manquants** (P1) : Simulateur d'objections (Word), Chronologie
   (CSV, nouveau `exporter_csv`), Vérification procédurale (Word).

## Non fait dans cette passe (recommandations)

- Import/export sur Traduire un texte (P1) et Consulter la jurisprudence
  (P2) — reportés, l'infrastructure réutilisable les rend maintenant peu
  coûteux à ajouter quand le besoin se confirme.
- Export CSV/DOCX sur Analyse stylistique, Extraction d'éléments clés,
  Contrôle de cohérence, Historique du dossier, Consulter les notes (P2).

## Tests

`backend/tests/test_corpus_fichier.py` (import de corpus par fichier :
métadonnées, référence par défaut, source manquante, PDF scanné) et
`backend/tests/test_exports_manquants.py` (les 3 nouveaux exports) —
85 tests backend + 15 tests racine, tous verts ; `tsc --noEmit` et
`vite build` propres.
