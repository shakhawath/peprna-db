# PepRNA-DB

**PepRNA-DB** is a curated, experiment-resolved database of peptide-based nucleic-acid
delivery. It links peptide sequence and chemistry, nucleic-acid cargo identity,
formulation context, and biological model to four independently annotated delivery
outcomes: cellular uptake, in vitro functional activity, endosomal escape evidence,
and in vivo delivery success.

- **Live site:** https://peprna-db.se
- **Dataset (versioned snapshot, CC BY 4.0):** https://doi.org/10.6084/m9.figshare.32658174

This repository contains the source code of the PepRNA-DB web platform (a Django
application) and the data-curation and relevance-scoring workflow.

## Repository layout

| Path | Contents |
|------|----------|
| `core/` | Main Django app: models, views, templates, and the `import_excel` management command |
| `rnadb/` | Django project settings and configuration |
| `manage.py` | Django management entry point |
| `requirements.txt` | Python dependencies |
| `rnadb_schema_and_django_starter.md` | Database schema and field definitions |
| `Figshare/` | Files prepared for the figshare dataset snapshot |

### Curation

Each publication was processed one at a time with GPT-5.2, following fixed evidence-label
definitions and row-construction rules, then manually reviewed, corrected, and
standardized. The evidence-label definitions and positive-annotation criteria are given
in the associated publication (Methods and Table 1), and every curated field is available
in the downloadable dataset (website Downloads page and the figshare snapshot).

## Requirements

- Python 3.11+
- The packages listed in `requirements.txt` (Django, pandas, openpyxl, psycopg, etc.)

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py migrate

# 4. (Optional) load the curated dataset from an Excel export
python manage.py import_excel path/to/apr_25.xlsx
#   use --dry-run to validate the file without writing to the database

# 5. Run the development server
python manage.py runserver
```

The site is then available at http://127.0.0.1:8000/.

## Data

All curated records can be exported in bulk, machine-readable format from the
[Downloads page](https://peprna-db.se) of the live site, or obtained from the
archived figshare snapshot (DOI above).

## Licensing

- **Source code** (this repository): [MIT License](LICENSE).
- **Curated dataset** (on the website and figshare): Creative Commons Attribution
  4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)),
  which permits reuse, including commercial reuse, with attribution.

## Citation

If you use PepRNA-DB, please cite:

- **Article:** Zhu X, Hossain S. *PepRNA-DB: An experiment-resolved database of
  peptide-based nucleic-acid delivery.* Journal of Cheminformatics (2026).
  [DOI to be added on publication]
- **Dataset:** Zhu X, Hossain S. *PepRNA-DB curated dataset and relevance-scoring
  code.* figshare (2026). https://doi.org/10.6084/m9.figshare.32658174
