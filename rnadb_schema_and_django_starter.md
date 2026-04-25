# RNA Delivery Database: Field-by-Field Schema and Starter Django Skeleton

This document turns the current spreadsheet into a practical first-release database resource.

---

## 1) Field-by-field schema table

### Core design

The production schema is split into these main tables:
- `papers`
- `peptides`
- `experiments`
- `vocab_terms`
- `dataset_releases` (optional but recommended)

The `experiments` table is the main evidence table. One row = one curated experimental record.

---

## Table: `papers`

| Field name | Type | Required | Unique | Example | Notes |
|---|---|---:|---:|---|---|
| id | bigint PK | yes | yes | 1 | Internal DB primary key |
| paper_id | varchar(100) | yes | yes | P000123 | Stable internal identifier |
| title | text | yes | no | Peptide-mediated siRNA delivery... | Full paper title |
| doi | varchar(255) | no | no | 10.1093/nar/gk... | Normalize lowercase, strip URL prefix |
| pmid | varchar(50) | no | no | 12345678 | Optional external ID |
| journal | varchar(255) | no | no | J Control Release | Optional for v1 |
| year | integer | yes | no | 2024 | Publication year |
| paper_file | varchar(255) | no | no | smith2024.pdf | Source spreadsheet field |
| source_url | text | no | no | https://doi.org/... | Optional convenience link |
| abstract | text | no | no | ... | Optional later |
| created_at | datetime | yes | no | auto | Auto timestamp |
| updated_at | datetime | yes | no | auto | Auto timestamp |

Validation rules:
- `paper_id` should be stable and never change.
- If DOI exists, store canonical DOI only, not full `https://doi.org/...`.
- `year` should be between 1900 and current year.

---

## Table: `peptides`

| Field name | Type | Required | Unique | Example | Notes |
|---|---|---:|---:|---|---|
| id | bigint PK | yes | yes | 1 | Internal PK |
| peptide_id | varchar(100) | yes | yes | PEP000321 | Stable internal identifier |
| peptide_name | varchar(255) | no | no | R9 | Common peptide label |
| peptide_sequence_raw | text | yes | no | RRRRRRRRR | Original sequence text |
| peptide_backbone_clean | text | no | no | RRRRRRRRR | Normalized sequence backbone |
| sequence_engineering_extracted | text | no | no | stearyl-R8, cyclic, etc. | Parsed engineering info |
| stereochemistry_detected | varchar(100) | no | no | D, L, mixed, unknown | Standardized |
| peptide_modifications | text | no | no | stearylation; PEGylation | Human-readable summary |
| sequence_length | integer | no | no | 9 | Computed from cleaned sequence when possible |
| has_noncanonical_residues | boolean | no | no | true | Computed/annotated |
| created_at | datetime | yes | no | auto | Auto timestamp |
| updated_at | datetime | yes | no | auto | Auto timestamp |

Validation rules:
- `peptide_sequence_raw` is required.
- `sequence_length` should be computed during import if possible.
- Distinguish raw sequence from normalized backbone.

---

## Table: `experiments`

| Field name | Type | Required | Unique | Example | Notes |
|---|---|---:|---:|---|---|
| id | bigint PK | yes | yes | 1 | Internal PK |
| experiment_id | varchar(100) | yes | yes | EXP000001 | Stable public-facing identifier |
| paper_id | FK -> papers.id | yes | no | 1 | Linked paper |
| peptide_id | FK -> peptides.id | yes | no | 2 | Linked peptide |
| delivery_success_class | varchar(100) | no | no | successful | Controlled vocabulary recommended |
| in_vivo_flag | boolean | no | no | true | Normalize from raw field |
| uptake_confirmed | boolean | no | no | true | Standardized boolean |
| label_confidence | varchar(50) | no | no | high | Controlled vocabulary |
| in_vitro_functional_effect | text | no | no | knockdown observed | Free text or normalized later |
| endosomal_escape_evidence | text | no | no | co-localization decrease | Sparse but useful |
| rna_type | varchar(100) | no | no | siRNA | Controlled vocabulary |
| rna_payload_or_target | text | no | no | PLK1 siRNA | Target/cargo detail |
| rna_modifications | text | no | no | 2'-OMe | Optional |
| peptide_concentration | varchar(100) | no | no | 10 uM | Preserve raw if unit parsing incomplete |
| rna_concentration | varchar(100) | no | no | 50 nM | Preserve raw |
| mixing_ratio | varchar(100) | no | no | N/P 5 | Preserve raw first |
| formulation_format | varchar(255) | no | no | nanoparticle | Standardize later |
| formulation_components | text | no | no | peptide + siRNA + helper lipid | Composition notes |
| size_nm | decimal(8,2) | no | no | 123.40 | Numeric where possible |
| zeta_mv | decimal(8,2) | no | no | 18.20 | Numeric where possible |
| model_scope | varchar(50) | no | no | in_vivo | Recommended split from model_type |
| model_type | varchar(255) | no | no | xenograft mouse model | Detailed system label |
| cell_lines_or_primary_cells | text | no | no | HeLa | Optional detailed field |
| animal_model | text | no | no | BALB/c mouse | Optional detailed field |
| administration_route | varchar(255) | no | no | intravenous | Controlled vocabulary |
| output_type | varchar(255) | no | no | gene_silencing | Controlled vocabulary |
| output_value | text | no | no | 65% knockdown | Keep raw unless parsed |
| output_units | varchar(100) | no | no | % | Optional parsed unit |
| output_notes | text | no | no | normalized to control | Context notes |
| toxicity_notes | text | no | no | no significant toxicity | Safety annotation |
| raw_row_hash | varchar(64) | no | yes | sha256... | Useful for deduplication |
| curation_notes | text | no | no | ambiguous route in paper | Internal annotation |
| created_at | datetime | yes | no | auto | Auto timestamp |
| updated_at | datetime | yes | no | auto | Auto timestamp |

Validation rules:
- `experiment_id` should be stable.
- `paper_id` and `peptide_id` are required.
- `size_nm` and `zeta_mv` must be numeric if populated.
- `label_confidence` should come from a controlled set.
- `model_scope` should be one of: `in_vitro`, `ex_vivo`, `in_vivo`, `in_silico`, `unknown`.

---

## Table: `vocab_terms`

Use this to normalize messy spreadsheet values.

| Field name | Type | Required | Unique | Example | Notes |
|---|---|---:|---:|---|---|
| id | bigint PK | yes | yes | 1 | Internal PK |
| field_name | varchar(100) | yes | no | label_confidence | Which field this maps |
| raw_value | varchar(255) | yes | no | High | Original spreadsheet value |
| normalized_value | varchar(255) | yes | no | high | Canonical value |
| display_label | varchar(255) | no | no | High | UI label |
| definition | text | no | no | High-confidence manual annotation | Help page content |
| is_active | boolean | yes | no | true | Allows deprecating terms |

Suggested controlled vocabularies:
- `label_confidence`: low, medium, high, very_high, unknown
- `model_scope`: in_vitro, ex_vivo, in_vivo, in_silico, unknown
- `administration_route`: intravenous, intratumoral, intranasal, oral, topical, subcutaneous, intraperitoneal, not_reported
- `output_type`: uptake, gene_silencing, protein_expression, biodistribution, viability, toxicity, endosomal_escape, other
- `rna_type`: siRNA, mRNA, miRNA, sgRNA, saRNA, antisense_oligo, plasmid, other

---

## Table: `dataset_releases` (recommended)

| Field name | Type | Required | Unique | Example | Notes |
|---|---|---:|---:|---|---|
| id | bigint PK | yes | yes | 1 | Internal PK |
| version | varchar(50) | yes | yes | v1.0.0 | Public release version |
| release_date | date | yes | yes | 2026-04-20 | Release date |
| record_count | integer | yes | no | 2576 | Snapshot summary |
| notes | text | no | no | initial public release | Changelog text |
| download_url | text | no | no | /downloads/... | Optional |

---

## Import mapping from current spreadsheet

Recommended mapping from current workbook columns into production fields:

| Spreadsheet column | Production field |
|---|---|
| paper_id | papers.paper_id |
| paper_file | papers.paper_file |
| title | papers.title |
| year | papers.year |
| doi | papers.doi |
| peptide_name | peptides.peptide_name |
| peptide_sequence_raw | peptides.peptide_sequence_raw |
| peptide_backbone_clean | peptides.peptide_backbone_clean |
| sequence_engineering_extracted | peptides.sequence_engineering_extracted |
| stereochemistry_detected | peptides.stereochemistry_detected |
| peptide_modifications | peptides.peptide_modifications |
| delivery_success_class | experiments.delivery_success_class |
| in_vivo_flag | experiments.in_vivo_flag |
| uptake_confirmed | experiments.uptake_confirmed |
| label_confidence | experiments.label_confidence |
| in_vitro_functional_effect | experiments.in_vitro_functional_effect |
| endosomal_escape_evidence | experiments.endosomal_escape_evidence |
| rna_type | experiments.rna_type |
| rna_payload_or_target | experiments.rna_payload_or_target |
| rna_modifications | experiments.rna_modifications |
| peptide_concentration | experiments.peptide_concentration |
| rna_concentration | experiments.rna_concentration |
| mixing_ratio | experiments.mixing_ratio |
| formulation_format | experiments.formulation_format |
| formulation_components | experiments.formulation_components |
| size_nm | experiments.size_nm |
| zeta_mV | experiments.zeta_mv |
| model_type | experiments.model_type + infer experiments.model_scope |
| cell_lines_or_primary_cells | experiments.cell_lines_or_primary_cells |
| animal_model | experiments.animal_model |
| administration_route | experiments.administration_route |
| output_type | experiments.output_type |
| output_value | experiments.output_value |
| output_notes | experiments.output_notes |
| toxicity_notes | experiments.toxicity_notes |

---

## Suggested indexing

Add DB indexes on:
- `papers.paper_id`
- `papers.doi`
- `papers.year`
- `peptides.peptide_id`
- `peptides.peptide_name`
- `experiments.experiment_id`
- `experiments.rna_type`
- `experiments.model_scope`
- `experiments.administration_route`
- `experiments.output_type`
- `experiments.label_confidence`

---

## 2) Starter Django code skeleton

Below is a production-lean but simple Django starter you can build from immediately.

---

## Project structure

```text
rnadb/
├── manage.py
├── requirements.txt
├── .env.example
├── rnadb/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── filters.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   ├── services.py
│   ├── tests.py
│   ├── migrations/
│   └── management/
│       └── commands/
│           └── import_excel.py
├── templates/
│   ├── base.html
│   └── core/
│       ├── home.html
│       ├── browse.html
│       ├── experiment_detail.html
│       ├── peptide_detail.html
│       ├── paper_detail.html
│       ├── downloads.html
│       ├── help.html
│       └── about.html
├── static/
│   └── css/
│       └── app.css
└── data/
    └── complete_data_sequence_restructured_apr20.xlsx
```

---

## `requirements.txt`

```txt
Django>=5.0,<6.0
django-filter>=24.0
psycopg[binary]>=3.1
pandas>=2.2
openpyxl>=3.1
python-dotenv>=1.0
```

---

## `.env.example`

```env
DEBUG=True
SECRET_KEY=change-me
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_NAME=rnadb
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=127.0.0.1
DATABASE_PORT=5432
```

---

## `rnadb/settings.py`

```python
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "rnadb.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "rnadb.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DATABASE_NAME", "rnadb"),
        "USER": os.getenv("DATABASE_USER", "postgres"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "postgres"),
        "HOST": os.getenv("DATABASE_HOST", "127.0.0.1"),
        "PORT": os.getenv("DATABASE_PORT", "5432"),
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

---

## `rnadb/urls.py`

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
]
```

---

## `core/models.py`

```python
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Paper(TimeStampedModel):
    paper_id = models.CharField(max_length=100, unique=True, db_index=True)
    title = models.TextField()
    doi = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    pmid = models.CharField(max_length=50, blank=True, null=True)
    journal = models.CharField(max_length=255, blank=True, null=True)
    year = models.IntegerField(db_index=True)
    paper_file = models.CharField(max_length=255, blank=True, null=True)
    source_url = models.TextField(blank=True, null=True)
    abstract = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-year", "title"]

    def __str__(self):
        return self.title[:100]


class Peptide(TimeStampedModel):
    peptide_id = models.CharField(max_length=100, unique=True, db_index=True)
    peptide_name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    peptide_sequence_raw = models.TextField()
    peptide_backbone_clean = models.TextField(blank=True, null=True)
    sequence_engineering_extracted = models.TextField(blank=True, null=True)
    stereochemistry_detected = models.CharField(max_length=100, blank=True, null=True)
    peptide_modifications = models.TextField(blank=True, null=True)
    sequence_length = models.IntegerField(blank=True, null=True)
    has_noncanonical_residues = models.BooleanField(blank=True, null=True)

    class Meta:
        ordering = ["peptide_name", "peptide_id"]

    def __str__(self):
        return self.peptide_name or self.peptide_id


class VocabTerm(TimeStampedModel):
    field_name = models.CharField(max_length=100, db_index=True)
    raw_value = models.CharField(max_length=255)
    normalized_value = models.CharField(max_length=255, db_index=True)
    display_label = models.CharField(max_length=255, blank=True, null=True)
    definition = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("field_name", "raw_value")
        ordering = ["field_name", "normalized_value"]

    def __str__(self):
        return f"{self.field_name}: {self.raw_value} -> {self.normalized_value}"


class Experiment(TimeStampedModel):
    experiment_id = models.CharField(max_length=100, unique=True, db_index=True)
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name="experiments")
    peptide = models.ForeignKey(Peptide, on_delete=models.CASCADE, related_name="experiments")

    delivery_success_class = models.CharField(max_length=100, blank=True, null=True)
    in_vivo_flag = models.BooleanField(blank=True, null=True)
    uptake_confirmed = models.BooleanField(blank=True, null=True)
    label_confidence = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    in_vitro_functional_effect = models.TextField(blank=True, null=True)
    endosomal_escape_evidence = models.TextField(blank=True, null=True)

    rna_type = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    rna_payload_or_target = models.TextField(blank=True, null=True)
    rna_modifications = models.TextField(blank=True, null=True)

    peptide_concentration = models.CharField(max_length=100, blank=True, null=True)
    rna_concentration = models.CharField(max_length=100, blank=True, null=True)
    mixing_ratio = models.CharField(max_length=100, blank=True, null=True)

    formulation_format = models.CharField(max_length=255, blank=True, null=True)
    formulation_components = models.TextField(blank=True, null=True)
    size_nm = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    zeta_mv = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    model_scope = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    model_type = models.CharField(max_length=255, blank=True, null=True)
    cell_lines_or_primary_cells = models.TextField(blank=True, null=True)
    animal_model = models.TextField(blank=True, null=True)
    administration_route = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    output_type = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    output_value = models.TextField(blank=True, null=True)
    output_units = models.CharField(max_length=100, blank=True, null=True)
    output_notes = models.TextField(blank=True, null=True)
    toxicity_notes = models.TextField(blank=True, null=True)

    raw_row_hash = models.CharField(max_length=64, blank=True, null=True, unique=True)
    curation_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["experiment_id"]

    def __str__(self):
        return self.experiment_id


class DatasetRelease(TimeStampedModel):
    version = models.CharField(max_length=50, unique=True)
    release_date = models.DateField()
    record_count = models.IntegerField()
    notes = models.TextField(blank=True, null=True)
    download_url = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-release_date"]

    def __str__(self):
        return self.version
```

---

## `core/admin.py`

```python
from django.contrib import admin
from .models import DatasetRelease, Experiment, Paper, Peptide, VocabTerm


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ("paper_id", "year", "title", "doi")
    search_fields = ("paper_id", "title", "doi", "pmid")
    list_filter = ("year",)


@admin.register(Peptide)
class PeptideAdmin(admin.ModelAdmin):
    list_display = ("peptide_id", "peptide_name", "sequence_length", "stereochemistry_detected")
    search_fields = ("peptide_id", "peptide_name", "peptide_sequence_raw", "peptide_backbone_clean")


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = (
        "experiment_id",
        "paper",
        "peptide",
        "rna_type",
        "model_scope",
        "administration_route",
        "output_type",
        "label_confidence",
    )
    search_fields = (
        "experiment_id",
        "paper__title",
        "paper__doi",
        "peptide__peptide_name",
        "peptide__peptide_sequence_raw",
        "rna_payload_or_target",
        "formulation_components",
        "model_type",
        "output_value",
    )
    list_filter = (
        "rna_type",
        "model_scope",
        "administration_route",
        "output_type",
        "label_confidence",
        "in_vivo_flag",
        "uptake_confirmed",
    )
    autocomplete_fields = ("paper", "peptide")


@admin.register(VocabTerm)
class VocabTermAdmin(admin.ModelAdmin):
    list_display = ("field_name", "raw_value", "normalized_value", "is_active")
    list_filter = ("field_name", "is_active")
    search_fields = ("raw_value", "normalized_value", "display_label")


@admin.register(DatasetRelease)
class DatasetReleaseAdmin(admin.ModelAdmin):
    list_display = ("version", "release_date", "record_count")
```

---

## `core/filters.py`

```python
import django_filters
from .models import Experiment


class ExperimentFilter(django_filters.FilterSet):
    paper_year = django_filters.NumberFilter(field_name="paper__year")
    peptide_name = django_filters.CharFilter(field_name="peptide__peptide_name", lookup_expr="icontains")
    rna_type = django_filters.CharFilter(field_name="rna_type", lookup_expr="iexact")
    model_scope = django_filters.CharFilter(field_name="model_scope", lookup_expr="iexact")
    administration_route = django_filters.CharFilter(field_name="administration_route", lookup_expr="iexact")
    output_type = django_filters.CharFilter(field_name="output_type", lookup_expr="iexact")
    label_confidence = django_filters.CharFilter(field_name="label_confidence", lookup_expr="iexact")
    in_vivo_flag = django_filters.BooleanFilter(field_name="in_vivo_flag")
    uptake_confirmed = django_filters.BooleanFilter(field_name="uptake_confirmed")

    class Meta:
        model = Experiment
        fields = [
            "paper_year",
            "peptide_name",
            "rna_type",
            "model_scope",
            "administration_route",
            "output_type",
            "label_confidence",
            "in_vivo_flag",
            "uptake_confirmed",
        ]
```

---

## `core/forms.py`

```python
from django import forms


class GlobalSearchForm(forms.Form):
    q = forms.CharField(required=False, label="Search")
```

---

## `core/services.py`

```python
from django.db.models import Q
from .models import Experiment


def apply_global_search(queryset, q: str):
    if not q:
        return queryset
    return queryset.filter(
        Q(experiment_id__icontains=q)
        | Q(paper__title__icontains=q)
        | Q(paper__doi__icontains=q)
        | Q(peptide__peptide_name__icontains=q)
        | Q(peptide__peptide_sequence_raw__icontains=q)
        | Q(peptide__peptide_backbone_clean__icontains=q)
        | Q(rna_payload_or_target__icontains=q)
        | Q(model_type__icontains=q)
        | Q(output_value__icontains=q)
        | Q(formulation_components__icontains=q)
    ).distinct()


def home_stats():
    qs = Experiment.objects.select_related("paper", "peptide")
    return {
        "experiment_count": qs.count(),
        "paper_count": qs.values("paper_id").distinct().count(),
        "peptide_count": qs.values("peptide_id").distinct().count(),
        "in_vivo_count": qs.filter(in_vivo_flag=True).count(),
        "rna_type_count": qs.exclude(rna_type__isnull=True).exclude(rna_type="").values("rna_type").distinct().count(),
    }
```

---

## `core/views.py`

```python
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .filters import ExperimentFilter
from .forms import GlobalSearchForm
from .models import Experiment, Paper, Peptide
from .services import apply_global_search, home_stats


def home(request):
    form = GlobalSearchForm(request.GET or None)
    context = {
        "stats": home_stats(),
        "form": form,
    }
    return render(request, "core/home.html", context)


def browse(request):
    qs = Experiment.objects.select_related("paper", "peptide").all()
    q = request.GET.get("q", "").strip()
    qs = apply_global_search(qs, q)
    f = ExperimentFilter(request.GET, queryset=qs)
    paginator = Paginator(f.qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "core/browse.html",
        {
            "filter": f,
            "page_obj": page_obj,
            "q": q,
        },
    )


def experiment_detail(request, experiment_id):
    experiment = get_object_or_404(
        Experiment.objects.select_related("paper", "peptide"),
        experiment_id=experiment_id,
    )
    return render(request, "core/experiment_detail.html", {"experiment": experiment})


def peptide_detail(request, peptide_id):
    peptide = get_object_or_404(Peptide, peptide_id=peptide_id)
    experiments = peptide.experiments.select_related("paper").all()
    return render(
        request,
        "core/peptide_detail.html",
        {"peptide": peptide, "experiments": experiments},
    )


def paper_detail(request, paper_id):
    paper = get_object_or_404(Paper, paper_id=paper_id)
    experiments = paper.experiments.select_related("peptide").all()
    return render(
        request,
        "core/paper_detail.html",
        {"paper": paper, "experiments": experiments},
    )


def downloads(request):
    return render(request, "core/downloads.html")


def help_page(request):
    return render(request, "core/help.html")


def about(request):
    return render(request, "core/about.html")
```

---

## `core/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("browse/", views.browse, name="browse"),
    path("experiment/<str:experiment_id>/", views.experiment_detail, name="experiment_detail"),
    path("peptide/<str:peptide_id>/", views.peptide_detail, name="peptide_detail"),
    path("paper/<str:paper_id>/", views.paper_detail, name="paper_detail"),
    path("downloads/", views.downloads, name="downloads"),
    path("help/", views.help_page, name="help"),
    path("about/", views.about, name="about"),
]
```

---

## Import command: `core/management/commands/import_excel.py`

```python
import hashlib
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Experiment, Paper, Peptide


def clean_str(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    return value if value else None


def clean_bool(value):
    if pd.isna(value):
        return None
    text = str(value).strip().lower()
    true_values = {"1", "true", "yes", "y", "confirmed", "high"}
    false_values = {"0", "false", "no", "n"}
    if text in true_values:
        return True
    if text in false_values:
        return False
    return None


def clean_decimal(value):
    if pd.isna(value):
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def normalize_doi(value):
    value = clean_str(value)
    if not value:
        return None
    value = value.lower().replace("https://doi.org/", "").replace("http://doi.org/", "")
    return value.strip()


def infer_model_scope(model_type, in_vivo_flag):
    mt = (model_type or "").lower()
    if in_vivo_flag is True:
        return "in_vivo"
    if "mouse" in mt or "rat" in mt or "xenograft" in mt or "in vivo" in mt:
        return "in_vivo"
    if "organoid" in mt or "ex vivo" in mt:
        return "ex_vivo"
    if mt:
        return "in_vitro"
    return None


def compute_row_hash(row_dict):
    text = "|".join([str(row_dict.get(k, "")) for k in sorted(row_dict.keys())])
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Command(BaseCommand):
    help = "Import curated RNA delivery data from Excel"

    def add_arguments(self, parser):
        parser.add_argument("excel_path", type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        excel_path = Path(options["excel_path"])
        if not excel_path.exists():
            raise CommandError(f"File not found: {excel_path}")

        df = pd.read_excel(excel_path, sheet_name=0)
        df = df.where(pd.notnull(df), None)

        paper_counter = 0
        peptide_counter = 0
        experiment_counter = 0

        for i, row in df.iterrows():
            row_data = row.to_dict()

            paper_id = clean_str(row_data.get("paper_id")) or f"P{i+1:06d}"
            peptide_name = clean_str(row_data.get("peptide_name"))
            peptide_seq = clean_str(row_data.get("peptide_sequence_raw"))
            if not peptide_seq:
                self.stdout.write(self.style.WARNING(f"Skipping row {i+2}: missing peptide_sequence_raw"))
                continue

            paper_defaults = {
                "title": clean_str(row_data.get("title")) or f"Untitled paper {paper_id}",
                "doi": normalize_doi(row_data.get("doi")),
                "year": int(row_data.get("year")) if row_data.get("year") else 1900,
                "paper_file": clean_str(row_data.get("paper_file")),
            }
            paper, created = Paper.objects.get_or_create(paper_id=paper_id, defaults=paper_defaults)
            if created:
                paper_counter += 1

            peptide_key = peptide_name or peptide_seq
            peptide_id = f"PEP{abs(hash(peptide_key)) % 10**8:08d}"
            peptide_defaults = {
                "peptide_name": peptide_name,
                "peptide_sequence_raw": peptide_seq,
                "peptide_backbone_clean": clean_str(row_data.get("peptide_backbone_clean")),
                "sequence_engineering_extracted": clean_str(row_data.get("sequence_engineering_extracted")),
                "stereochemistry_detected": clean_str(row_data.get("stereochemistry_detected")),
                "peptide_modifications": clean_str(row_data.get("peptide_modifications")),
                "sequence_length": len(peptide_seq.replace(" ", "")) if peptide_seq else None,
            }
            peptide, created = Peptide.objects.get_or_create(peptide_id=peptide_id, defaults=peptide_defaults)
            if created:
                peptide_counter += 1

            in_vivo_flag = clean_bool(row_data.get("in_vivo_flag"))
            model_type = clean_str(row_data.get("model_type"))

            experiment_payload = {
                "paper": paper,
                "peptide": peptide,
                "delivery_success_class": clean_str(row_data.get("delivery_success_class")),
                "in_vivo_flag": in_vivo_flag,
                "uptake_confirmed": clean_bool(row_data.get("uptake_confirmed")),
                "label_confidence": clean_str(row_data.get("label_confidence")),
                "in_vitro_functional_effect": clean_str(row_data.get("in_vitro_functional_effect")),
                "endosomal_escape_evidence": clean_str(row_data.get("endosomal_escape_evidence")),
                "rna_type": clean_str(row_data.get("rna_type")),
                "rna_payload_or_target": clean_str(row_data.get("rna_payload_or_target")),
                "rna_modifications": clean_str(row_data.get("rna_modifications")),
                "peptide_concentration": clean_str(row_data.get("peptide_concentration")),
                "rna_concentration": clean_str(row_data.get("rna_concentration")),
                "mixing_ratio": clean_str(row_data.get("mixing_ratio")),
                "formulation_format": clean_str(row_data.get("formulation_format")),
                "formulation_components": clean_str(row_data.get("formulation_components")),
                "size_nm": clean_decimal(row_data.get("size_nm")),
                "zeta_mv": clean_decimal(row_data.get("zeta_mV")),
                "model_scope": infer_model_scope(model_type, in_vivo_flag),
                "model_type": model_type,
                "cell_lines_or_primary_cells": clean_str(row_data.get("cell_lines_or_primary_cells")),
                "animal_model": clean_str(row_data.get("animal_model")),
                "administration_route": clean_str(row_data.get("administration_route")),
                "output_type": clean_str(row_data.get("output_type")),
                "output_value": clean_str(row_data.get("output_value")),
                "output_notes": clean_str(row_data.get("output_notes")),
                "toxicity_notes": clean_str(row_data.get("toxicity_notes")),
            }

            row_hash = compute_row_hash({k: v for k, v in row_data.items()})
            experiment_payload["raw_row_hash"] = row_hash
            experiment_id = f"EXP{i+1:06d}"

            obj, created = Experiment.objects.get_or_create(
                raw_row_hash=row_hash,
                defaults={"experiment_id": experiment_id, **experiment_payload},
            )
            if created:
                experiment_counter += 1

        self.stdout.write(self.style.SUCCESS(
            f"Imported: {paper_counter} new papers, {peptide_counter} new peptides, {experiment_counter} new experiments"
        ))
```

---

## `templates/base.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}RNA Delivery DB{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-light bg-light border-bottom mb-4">
  <div class="container">
    <a class="navbar-brand" href="/">RNA Delivery DB</a>
    <div class="navbar-nav">
      <a class="nav-link" href="/browse/">Browse</a>
      <a class="nav-link" href="/downloads/">Downloads</a>
      <a class="nav-link" href="/help/">Help</a>
      <a class="nav-link" href="/about/">About</a>
    </div>
  </div>
</nav>

<div class="container">
  {% block content %}{% endblock %}
</div>
</body>
</html>
```

---

## `templates/core/home.html`

```html
{% extends "base.html" %}
{% block title %}Home - RNA Delivery DB{% endblock %}
{% block content %}
<h1>RNA Delivery DB</h1>
<p class="lead">A curated database of peptide-mediated RNA delivery evidence.</p>

<div class="row mb-4">
  <div class="col-md-3"><div class="card card-body"><strong>{{ stats.experiment_count }}</strong><br>Experiments</div></div>
  <div class="col-md-3"><div class="card card-body"><strong>{{ stats.paper_count }}</strong><br>Papers</div></div>
  <div class="col-md-3"><div class="card card-body"><strong>{{ stats.peptide_count }}</strong><br>Peptides</div></div>
  <div class="col-md-3"><div class="card card-body"><strong>{{ stats.in_vivo_count }}</strong><br>In vivo entries</div></div>
</div>

<form method="get" action="/browse/" class="mb-4">
  <input type="text" name="q" class="form-control" placeholder="Search peptide, sequence, paper, DOI, target...">
</form>
{% endblock %}
```

---

## `templates/core/browse.html`

```html
{% extends "base.html" %}
{% block title %}Browse - RNA Delivery DB{% endblock %}
{% block content %}
<h1>Browse experiments</h1>

<form method="get" class="row g-2 mb-4">
  <div class="col-md-4">
    <input type="text" name="q" value="{{ q }}" class="form-control" placeholder="Keyword search">
  </div>
  <div class="col-md-2">
    <input type="text" name="rna_type" value="{{ request.GET.rna_type }}" class="form-control" placeholder="RNA type">
  </div>
  <div class="col-md-2">
    <input type="text" name="model_scope" value="{{ request.GET.model_scope }}" class="form-control" placeholder="Model scope">
  </div>
  <div class="col-md-2">
    <input type="text" name="administration_route" value="{{ request.GET.administration_route }}" class="form-control" placeholder="Route">
  </div>
  <div class="col-md-2">
    <button class="btn btn-primary w-100">Filter</button>
  </div>
</form>

<table class="table table-striped table-sm">
  <thead>
    <tr>
      <th>ID</th>
      <th>Peptide</th>
      <th>RNA</th>
      <th>Model</th>
      <th>Route</th>
      <th>Output</th>
      <th>Paper</th>
    </tr>
  </thead>
  <tbody>
    {% for obj in page_obj %}
    <tr>
      <td><a href="{% url 'experiment_detail' obj.experiment_id %}">{{ obj.experiment_id }}</a></td>
      <td><a href="{% url 'peptide_detail' obj.peptide.peptide_id %}">{{ obj.peptide.peptide_name|default:obj.peptide.peptide_id }}</a></td>
      <td>{{ obj.rna_type }}</td>
      <td>{{ obj.model_scope }}</td>
      <td>{{ obj.administration_route }}</td>
      <td>{{ obj.output_type }}</td>
      <td><a href="{% url 'paper_detail' obj.paper.paper_id %}">{{ obj.paper.title|truncatechars:70 }}</a></td>
    </tr>
    {% empty %}
    <tr><td colspan="7">No records found.</td></tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}
```

---

## `templates/core/experiment_detail.html`

```html
{% extends "base.html" %}
{% block title %}{{ experiment.experiment_id }} - RNA Delivery DB{% endblock %}
{% block content %}
<h1>{{ experiment.experiment_id }}</h1>
<p><strong>Paper:</strong> <a href="{% url 'paper_detail' experiment.paper.paper_id %}">{{ experiment.paper.title }}</a></p>
<p><strong>Peptide:</strong> <a href="{% url 'peptide_detail' experiment.peptide.peptide_id %}">{{ experiment.peptide.peptide_name|default:experiment.peptide.peptide_id }}</a></p>

<table class="table table-bordered">
  <tr><th>RNA type</th><td>{{ experiment.rna_type }}</td></tr>
  <tr><th>RNA target/payload</th><td>{{ experiment.rna_payload_or_target }}</td></tr>
  <tr><th>Model scope</th><td>{{ experiment.model_scope }}</td></tr>
  <tr><th>Model type</th><td>{{ experiment.model_type }}</td></tr>
  <tr><th>Administration route</th><td>{{ experiment.administration_route }}</td></tr>
  <tr><th>Output type</th><td>{{ experiment.output_type }}</td></tr>
  <tr><th>Output value</th><td>{{ experiment.output_value }}</td></tr>
  <tr><th>Uptake confirmed</th><td>{{ experiment.uptake_confirmed }}</td></tr>
  <tr><th>Confidence</th><td>{{ experiment.label_confidence }}</td></tr>
  <tr><th>Toxicity notes</th><td>{{ experiment.toxicity_notes }}</td></tr>
</table>
{% endblock %}
```

---

## `templates/core/peptide_detail.html`

```html
{% extends "base.html" %}
{% block title %}{{ peptide.peptide_name|default:peptide.peptide_id }} - RNA Delivery DB{% endblock %}
{% block content %}
<h1>{{ peptide.peptide_name|default:peptide.peptide_id }}</h1>
<p><strong>Sequence:</strong> {{ peptide.peptide_sequence_raw }}</p>
<p><strong>Backbone:</strong> {{ peptide.peptide_backbone_clean }}</p>
<p><strong>Modifications:</strong> {{ peptide.peptide_modifications }}</p>

<h2>Experiments</h2>
<ul>
  {% for exp in experiments %}
  <li><a href="{% url 'experiment_detail' exp.experiment_id %}">{{ exp.experiment_id }}</a> — {{ exp.rna_type }} — {{ exp.output_type }}</li>
  {% endfor %}
</ul>
{% endblock %}
```

---

## `templates/core/paper_detail.html`

```html
{% extends "base.html" %}
{% block title %}{{ paper.title|truncatechars:50 }} - RNA Delivery DB{% endblock %}
{% block content %}
<h1>{{ paper.title }}</h1>
<p><strong>Year:</strong> {{ paper.year }}</p>
<p><strong>DOI:</strong> {{ paper.doi }}</p>

<h2>Curated experiments</h2>
<ul>
  {% for exp in experiments %}
  <li><a href="{% url 'experiment_detail' exp.experiment_id %}">{{ exp.experiment_id }}</a> — {{ exp.peptide.peptide_name|default:exp.peptide.peptide_id }} — {{ exp.rna_type }}</li>
  {% endfor %}
</ul>
{% endblock %}
```

---

## First run commands

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
createdb rnadb
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py import_excel data/complete_data_sequence_restructured_apr20.xlsx
python manage.py runserver
```

---

## Immediate next improvements

1. Add mapping dictionaries for normalized vocabularies.
2. Replace hash-derived `peptide_id` with a deterministic registry.
3. Add validation reports for missing/ambiguous entries.
4. Add CSV download views.
5. Add tests for import behavior.
6. Add an API later.

---

## Recommended v1 launch checklist

- Public site loads without login
- Browse and search pages work
- Entry pages open reliably
- DOI, year, peptide, RNA, and route are visible
- Help page defines fields and missingness
- Download page provides current release file
- About page shows update date and contact email

This is enough for a real first database release and a serious NAR-style pre-submission stage.

