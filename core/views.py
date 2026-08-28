import json
from io import BytesIO
from pathlib import Path

from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
import pandas as pd

from .models import Experiment, Paper, Peptide


def yes_no_blank(value, blank_as_no=False):
    if value is None or value == "":
        return "no" if blank_as_no else ""
    if value is True or value == 1 or str(value).strip().lower() in {"1", "true", "yes"}:
        return "yes"
    if value is False or value == 0 or str(value).strip().lower() in {"0", "false", "no"}:
        return "no"
    return value


def canonical_peptide_name(value):
    if value is None:
        return ""
    name = str(value).strip()
    if name.lower() in {"599 peptide", "599"}:
        return "INF7-G4-R9-K"
    return name


def normalized_signature_part(value):
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def normalized_sequence_part(value):
    return normalized_signature_part(value).upper()


SEQUENCE_PLACEHOLDERS = {
    "",
    "not reported",
    "not clearly reported",
    "not provided",
    "not available",
    "na",
    "n/a",
    "none",
    "nan",
    "unknown",
}


RNA_TYPE_EXCLUDE_FROM_FILTER = {
    "not reported",
    "rna unspecified",
    "rna, unspecified",
}


def has_real_sequence_text(value):
    normalized = normalized_signature_part(value)
    if not normalized:
        return False
    return normalized.lower() not in SEQUENCE_PLACEHOLDERS


def peptide_signature(experiment):
    peptide = experiment.peptide
    return (
        normalized_signature_part(peptide.peptide_backbone_clean),
        normalized_signature_part(peptide.peptide_backbone_tokenized),
        normalized_signature_part(peptide.peptide_sequence_raw),
        normalized_signature_part(peptide.sequence_engineering_extracted),
        normalized_signature_part(peptide.stereochemistry_detected),
        normalized_signature_part(peptide.peptide_modifications),
        normalized_signature_part(peptide.noncanonical_residues),
    )


def peptide_backbone_sequence_signature(experiment):
    return normalized_sequence_part(experiment.peptide.peptide_backbone_clean)


def has_peptide_backbone_sequence(experiment):
    return has_real_sequence_text(experiment.peptide.peptide_backbone_clean)


def has_peptide_sequence_information(experiment):
    peptide = experiment.peptide
    return any(
        has_real_sequence_text(value)
        for value in [
            peptide.peptide_sequence_raw,
            peptide.peptide_backbone_clean,
            peptide.peptide_backbone_tokenized,
        ]
    )


def rna_signature(experiment):
    return (
        normalized_signature_part(experiment.rna_type),
        normalized_signature_part(experiment.rna_payload_or_target),
        normalized_signature_part(experiment.target_gene_or_transcript),
        normalized_signature_part(experiment.rna_sequence),
        normalized_signature_part(experiment.sense_strand),
        normalized_signature_part(experiment.antisense_strand),
        normalized_signature_part(experiment.rna_modifications),
    )


def nucleic_acid_strand_signature(experiment):
    return (
        normalized_sequence_part(experiment.sense_strand),
        normalized_sequence_part(experiment.antisense_strand),
    )


def has_nucleic_acid_strand_information(experiment):
    return (
        has_real_sequence_text(experiment.sense_strand)
        or has_real_sequence_text(experiment.antisense_strand)
    )


def has_rna_sequence_information(experiment):
    return any(
        has_real_sequence_text(value)
        for value in [
            experiment.rna_sequence,
            experiment.sense_strand,
            experiment.antisense_strand,
        ]
    )


DISPLAY_AS_YES_NO = {
    "delivery_success_class": False,
    "in_vivo_flag": True,
    "uptake_confirmed": True,
    "in_vitro_functional_effect": False,
    "endosomal_escape_evidence": False,
}


def model_field_rows(instance):
    rows = []
    hidden_fields = {
        "id",
        "raw_row_hash",
        "created_at",
        "updated_at",
        "rna_type",
        "rna_payload_or_target",
        "target_gene_or_transcript",
        "rna_sequence",
        "sense_strand",
        "antisense_strand",
        "rna_modifications",
    }
    for field in instance._meta.fields:
        if field.name in hidden_fields:
            continue
        value = getattr(instance, field.name)
        if field.name in DISPLAY_AS_YES_NO:
            value = yes_no_blank(value, blank_as_no=DISPLAY_AS_YES_NO[field.name])
        rows.append(
            {
                "name": field.verbose_name.title(),
                "value": value,
            }
        )
    return rows


def home(request):
    experiments = list(
        Experiment.objects.select_related("peptide").all()
    )
    peptide_backbone_sequences = {
        peptide_backbone_sequence_signature(experiment)
        for experiment in experiments
        if has_peptide_backbone_sequence(experiment)
    }
    strand_informed_experiments = [
        experiment for experiment in experiments if has_nucleic_acid_strand_information(experiment)
    ]
    nucleic_acid_sequences = {
        nucleic_acid_strand_signature(experiment)
        for experiment in strand_informed_experiments
    }
    peptide_cargo_sequence_combinations = {
        (
            peptide_backbone_sequence_signature(experiment),
            nucleic_acid_strand_signature(experiment),
        )
        for experiment in experiments
        if has_peptide_backbone_sequence(experiment)
        and has_nucleic_acid_strand_information(experiment)
    }
    cargo_class_count = len(
        {
            normalized_signature_part(experiment.rna_type)
            for experiment in experiments
            if normalized_signature_part(experiment.rna_type)
            and normalized_signature_part(experiment.rna_type).lower()
            not in RNA_TYPE_EXCLUDE_FROM_FILTER
        }
    )
    stats = {
        "experiment_count": len(experiments),
        "peptide_count": len(peptide_backbone_sequences),
        "paper_count": Paper.objects.count(),
        "in_vivo_count": sum(1 for experiment in experiments if experiment.in_vivo_flag is True),
        "sequence_peptide_system_count": len(peptide_backbone_sequences),
        "rna_system_count": len(nucleic_acid_sequences),
        "peptide_rna_system_count": len(peptide_cargo_sequence_combinations),
        "cargo_class_count": cargo_class_count,
    }
    return render(request, "core/home.html", {"stats": stats})


def rna_type_filter_options():
    return [
        value
        for value in Experiment.objects.exclude(rna_type__isnull=True)
        .exclude(rna_type="")
        .order_by("rna_type")
        .values_list("rna_type", flat=True)
        .distinct()
        if normalized_signature_part(value).lower() not in RNA_TYPE_EXCLUDE_FROM_FILTER
    ]


def filtered_experiments_from_request(request):
    experiments = (
        Experiment.objects.select_related("paper", "peptide")
        .order_by("experiment_id")
    )
    q = request.GET.get("q", "").strip()
    rna_type = request.GET.get("rna_type", "").strip()
    uptake_confirmed = request.GET.get("uptake_confirmed", "").strip()
    in_vitro_functional_effect = request.GET.get("in_vitro_functional_effect", "").strip()
    endosomal_escape_evidence = request.GET.get("endosomal_escape_evidence", "").strip()
    in_vivo_flag = request.GET.get("in_vivo_flag", "").strip()
    delivery_success_class = request.GET.get("delivery_success_class", "").strip()
    per_page = request.GET.get("per_page", "100").strip()
    if per_page not in {"50", "100", "200"}:
        per_page = "100"

    if q:
        experiments = experiments.filter(
            Q(experiment_id__icontains=q)
            | Q(paper__paper_id__icontains=q)
            | Q(paper__title__icontains=q)
            | Q(paper__doi__icontains=q)
            | Q(paper__pmid__icontains=q)
            | Q(peptide__peptide_id__icontains=q)
            | Q(peptide__peptide_name__icontains=q)
            | Q(peptide__peptide_sequence_raw__icontains=q)
            | Q(rna_type__icontains=q)
            | Q(rna_payload_or_target__icontains=q)
            | Q(target_gene_or_transcript__icontains=q)
            | Q(rna_sequence__icontains=q)
            | Q(sense_strand__icontains=q)
            | Q(antisense_strand__icontains=q)
            | Q(rna_modifications__icontains=q)
            | Q(output_value__icontains=q)
        )

    if rna_type:
        experiments = experiments.filter(rna_type__iexact=rna_type)

    if uptake_confirmed == "yes":
        experiments = experiments.filter(uptake_confirmed=True)
    elif uptake_confirmed == "no":
        experiments = experiments.filter(
            Q(uptake_confirmed=False) | Q(uptake_confirmed__isnull=True)
        )

    if in_vitro_functional_effect == "yes":
        experiments = experiments.filter(in_vitro_functional_effect__in=["1", 1, True, "true", "yes"])
    elif in_vitro_functional_effect == "no":
        experiments = experiments.filter(in_vitro_functional_effect__in=["0", 0, False, "false", "no"])
    elif in_vitro_functional_effect == "blank":
        experiments = experiments.filter(
            Q(in_vitro_functional_effect__isnull=True) | Q(in_vitro_functional_effect="")
        )

    if endosomal_escape_evidence == "yes":
        experiments = experiments.filter(endosomal_escape_evidence__in=["1", 1, True, "true", "yes"])
    elif endosomal_escape_evidence == "no":
        experiments = experiments.filter(endosomal_escape_evidence__in=["0", 0, False, "false", "no"])
    elif endosomal_escape_evidence == "blank":
        experiments = experiments.filter(
            Q(endosomal_escape_evidence__isnull=True) | Q(endosomal_escape_evidence="")
        )

    if in_vivo_flag == "yes":
        experiments = experiments.filter(in_vivo_flag=True)
    elif in_vivo_flag == "no":
        experiments = experiments.filter(Q(in_vivo_flag=False) | Q(in_vivo_flag__isnull=True))

    if delivery_success_class == "yes":
        experiments = experiments.filter(
            delivery_success_class__in=["1", 1, True, "true", "yes"]
        )
    elif delivery_success_class == "no":
        experiments = experiments.filter(
            delivery_success_class__in=["0", 0, False, "false", "no"]
        )
    elif delivery_success_class == "blank":
        experiments = experiments.filter(
            Q(delivery_success_class__isnull=True) | Q(delivery_success_class="")
        )

    filters = {
        "q": q,
        "rna_type": rna_type,
        "uptake_confirmed": uptake_confirmed,
        "in_vitro_functional_effect": in_vitro_functional_effect,
        "endosomal_escape_evidence": endosomal_escape_evidence,
        "in_vivo_flag": in_vivo_flag,
        "delivery_success_class": delivery_success_class,
        "per_page": per_page,
    }
    return experiments, filters


def browse(request):
    experiments, filters = filtered_experiments_from_request(request)
    q = filters["q"]
    rna_type = filters["rna_type"]
    uptake_confirmed = filters["uptake_confirmed"]
    in_vitro_functional_effect = filters["in_vitro_functional_effect"]
    endosomal_escape_evidence = filters["endosomal_escape_evidence"]
    in_vivo_flag = filters["in_vivo_flag"]
    delivery_success_class = filters["delivery_success_class"]
    per_page = filters["per_page"]
    rna_type_options = rna_type_filter_options()

    paginator = Paginator(experiments, int(per_page))
    page_obj = paginator.get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)
    query_string = query_params.urlencode()
    page_numbers = []
    total_pages = paginator.num_pages
    current_page = page_obj.number
    if total_pages <= 7:
        page_numbers = list(range(1, total_pages + 1))
    else:
        page_numbers.append(1)
        start_page = max(2, current_page - 2)
        end_page = min(total_pages - 1, current_page + 2)
        if start_page > 2:
            page_numbers.append("...")
        page_numbers.extend(range(start_page, end_page + 1))
        if end_page < total_pages - 1:
            page_numbers.append("...")
        page_numbers.append(total_pages)

    experiment_rows = []
    for experiment in page_obj:
        experiment_rows.append(
            {
                "experiment": experiment,
                "peptide_name": canonical_peptide_name(experiment.peptide.peptide_name),
                "delivery_success_class": yes_no_blank(experiment.delivery_success_class),
                "in_vivo_flag": yes_no_blank(experiment.in_vivo_flag, blank_as_no=True),
                "uptake_confirmed": yes_no_blank(
                    experiment.uptake_confirmed, blank_as_no=True
                ),
                "in_vitro_functional_effect": yes_no_blank(
                    experiment.in_vitro_functional_effect
                ),
                "endosomal_escape_evidence": yes_no_blank(
                    experiment.endosomal_escape_evidence
                ),
            }
        )
    return render(
        request,
        "core/browse.html",
        {
            "experiment_rows": experiment_rows,
            "page_obj": page_obj,
            "q": q,
            "rna_type": rna_type,
            "rna_type_options": rna_type_options,
            "in_vivo_flag": in_vivo_flag,
            "uptake_confirmed": uptake_confirmed,
            "in_vitro_functional_effect": in_vitro_functional_effect,
            "endosomal_escape_evidence": endosomal_escape_evidence,
            "delivery_success_class": delivery_success_class,
            "per_page": per_page,
            "query_string": query_string,
            "page_numbers": page_numbers,
        },
    )


def experiment_detail(request, experiment_id):
    experiment = get_object_or_404(
        Experiment.objects.select_related("paper", "peptide"),
        pk=experiment_id,
    )
    return render(
        request,
        "core/experiment_detail.html",
        {
            "experiment": experiment,
            "experiment_fields": model_field_rows(experiment),
        },
    )


def rna_detail(request, experiment_id):
    experiment = get_object_or_404(
        Experiment.objects.select_related("paper", "peptide"),
        pk=experiment_id,
    )
    return render(
        request,
        "core/rna_detail.html",
        {
            "experiment": experiment,
            "sequence_reported_in_source": has_rna_sequence_information(experiment),
        },
    )


def peptide_detail(request, peptide_id):
    peptide = get_object_or_404(Peptide, pk=peptide_id)
    experiments = peptide.experiments.select_related("paper").order_by(
        "-paper__year", "experiment_id"
    )
    return render(
        request,
        "core/peptide_detail.html",
        {"peptide": peptide, "experiments": experiments},
    )


def paper_detail(request, paper_id):
    paper = get_object_or_404(Paper, pk=paper_id)
    experiments = paper.experiments.select_related("peptide").order_by("experiment_id")
    return render(
        request,
        "core/paper_detail.html",
        {"paper": paper, "experiments": experiments},
    )


def help_page(request):
    return render(request, "core/help.html")


def about_page(request):
    return render(request, "core/about.html")


def contact_page(request):
    return render(request, "core/contact.html")


def faq_page(request):
    faq_path = Path(__file__).resolve().parent / "content" / "faqs.json"
    with faq_path.open("r", encoding="utf-8") as handle:
        faqs = json.load(handle)
    return render(request, "core/faq.html", {"faqs": faqs})


def downloads_page(request):
    downloads = [
        {
            "label": "Full curated dataset",
            "kind": "full",
            "filename": "PepRNA-DB_full_dataset.xlsx",
        },
        {
            "label": "Experiments table",
            "kind": "experiments",
            "filename": "PepRNA-DB_experiments.xlsx",
        },
        {
            "label": "Peptides table",
            "kind": "peptides",
            "filename": "PepRNA-DB_peptides.xlsx",
        },
        {
            "label": "RNA and nucleic-acid systems table",
            "kind": "rna",
            "filename": "PepRNA-DB_RNA_nucleic_acid_systems.xlsx",
        },
        {
            "label": "Papers table",
            "kind": "papers",
            "filename": "PepRNA-DB_papers.xlsx",
        },
    ]
    return render(request, "core/downloads.html", {"downloads": downloads})


def full_dataset_rows(experiments=None):
    if experiments is None:
        experiments = Experiment.objects.select_related("paper", "peptide").order_by("experiment_id")
    rows = []
    for experiment in experiments:
        rows.append(
            {
                "Experimental_ID": experiment.experiment_id,
                "paper_id": experiment.paper.paper_id,
                "title": experiment.paper.title,
                "doi": experiment.paper.doi,
                "journal": experiment.paper.journal,
                "pmid": experiment.paper.pmid,
                "year": experiment.paper.year,
                "peptide_id": experiment.peptide.peptide_id,
                "peptide_name": canonical_peptide_name(experiment.peptide.peptide_name),
                "peptide_sequence_raw": experiment.peptide.peptide_sequence_raw,
                "peptide_backbone_clean": experiment.peptide.peptide_backbone_clean,
                "peptide_backbone_tokenized": experiment.peptide.peptide_backbone_tokenized,
                "sequence_engineering_extracted": experiment.peptide.sequence_engineering_extracted,
                "stereochemistry_detected": experiment.peptide.stereochemistry_detected,
                "peptide_modifications": experiment.peptide.peptide_modifications,
                "noncanonical_residues": experiment.peptide.noncanonical_residues,
                "delivery_success_class": yes_no_blank(experiment.delivery_success_class),
                "in_vivo_flag": yes_no_blank(experiment.in_vivo_flag, blank_as_no=True),
                "uptake_confirmed": yes_no_blank(experiment.uptake_confirmed, blank_as_no=True),
                "label_confidence": experiment.label_confidence,
                "in_vitro_functional_effect": yes_no_blank(
                    experiment.in_vitro_functional_effect
                ),
                "endosomal_escape_evidence": yes_no_blank(
                    experiment.endosomal_escape_evidence
                ),
                "rna_type": experiment.rna_type,
                "rna_payload_or_target": experiment.rna_payload_or_target,
                "target_gene_or_transcript": experiment.target_gene_or_transcript,
                "rna_sequence": experiment.rna_sequence,
                "sense_strand": experiment.sense_strand,
                "antisense_strand": experiment.antisense_strand,
                "rna_modifications": experiment.rna_modifications,
                "peptide_concentration": experiment.peptide_concentration,
                "rna_concentration": experiment.rna_concentration,
                "mixing_ratio": experiment.mixing_ratio,
                "formulation_format": experiment.formulation_format,
                "formulation_components": experiment.formulation_components,
                "size_nm": experiment.size_nm,
                "zeta_mV": experiment.zeta_mv,
                "model_scope": experiment.model_scope,
                "model_type": experiment.model_type,
                "cell_lines_or_primary_cells": experiment.cell_lines_or_primary_cells,
                "animal_model": experiment.animal_model,
                "administration_route": experiment.administration_route,
                "output_type": experiment.output_type,
                "output_value": experiment.output_value,
                "output_units": experiment.output_units,
                "output_notes": experiment.output_notes,
                "toxicity_notes": experiment.toxicity_notes,
            }
        )
    return rows


def download_filtered_experiments(request):
    experiments, _ = filtered_experiments_from_request(request)
    dataframe = pd.DataFrame(full_dataset_rows(experiments))
    dataframe = normalize_export_yes_no_blank(dataframe)
    return export_dataframe_response(
        dataframe,
        "PepRNA-DB_filtered_experiments.xlsx",
    )


def export_dataframe_response(dataframe, filename):
    buffer = BytesIO()
    dataframe.to_excel(buffer, index=False)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=filename)


def normalize_export_yes_no_blank(dataframe):
    conversions = {
        "delivery_success_class": yes_no_blank,
        "in_vivo_flag": lambda value: yes_no_blank(value, blank_as_no=True),
        "uptake_confirmed": lambda value: yes_no_blank(value, blank_as_no=True),
        "in_vitro_functional_effect": yes_no_blank,
        "endosomal_escape_evidence": yes_no_blank,
    }
    for column, converter in conversions.items():
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].map(converter)
    return dataframe


def rna_system_rows():
    rows_by_signature = {}
    experiments = Experiment.objects.select_related("paper", "peptide").order_by("experiment_id")
    for experiment in experiments:
        signature = rna_signature(experiment)
        if not any(signature):
            continue

        key = signature
        row = rows_by_signature.setdefault(
            key,
            {
                "rna_type": experiment.rna_type,
                "rna_payload_or_target": experiment.rna_payload_or_target,
                "target_gene_or_transcript": experiment.target_gene_or_transcript,
                "rna_sequence": experiment.rna_sequence,
                "sense_strand": experiment.sense_strand,
                "antisense_strand": experiment.antisense_strand,
                "rna_modifications": experiment.rna_modifications,
                "has_sequence_information": "yes"
                if has_rna_sequence_information(experiment)
                else "no",
                "experiment_count": 0,
                "example_experiment_id": experiment.experiment_id,
            },
        )
        row["experiment_count"] += 1

    return list(rows_by_signature.values())


def download_dataset(request, kind):
    if kind == "full":
        dataframe = pd.DataFrame(full_dataset_rows())
        filename = "PepRNA-DB_full_dataset.xlsx"
    elif kind == "experiments":
        dataframe = pd.DataFrame(
            list(
                Experiment.objects.order_by("experiment_id").values(
                    "experiment_id",
                    "paper_id",
                    "peptide_id",
                    "delivery_success_class",
                    "in_vivo_flag",
                    "uptake_confirmed",
                    "label_confidence",
                    "in_vitro_functional_effect",
                    "endosomal_escape_evidence",
                    "rna_type",
                    "rna_payload_or_target",
                    "target_gene_or_transcript",
                    "rna_sequence",
                    "sense_strand",
                    "antisense_strand",
                    "rna_modifications",
                    "peptide_concentration",
                    "rna_concentration",
                    "mixing_ratio",
                    "formulation_format",
                    "formulation_components",
                    "size_nm",
                    "zeta_mv",
                    "model_scope",
                    "model_type",
                    "cell_lines_or_primary_cells",
                    "animal_model",
                    "administration_route",
                    "output_type",
                    "output_value",
                    "output_units",
                    "output_notes",
                    "toxicity_notes",
                )
            )
        )
        dataframe = normalize_export_yes_no_blank(dataframe)
        filename = "PepRNA-DB_experiments.xlsx"
    elif kind == "peptides":
        dataframe = pd.DataFrame(
            list(
                Peptide.objects.order_by("peptide_id").values(
                    "peptide_id",
                    "peptide_name",
                    "peptide_sequence_raw",
                    "peptide_backbone_clean",
                    "peptide_backbone_tokenized",
                    "sequence_engineering_extracted",
                    "stereochemistry_detected",
                    "peptide_modifications",
                    "sequence_length",
                    "noncanonical_residues",
                )
            )
        )
        dataframe["peptide_name"] = dataframe["peptide_name"].map(canonical_peptide_name)
        filename = "PepRNA-DB_peptides.xlsx"
    elif kind == "rna":
        dataframe = pd.DataFrame(rna_system_rows())
        filename = "PepRNA-DB_RNA_nucleic_acid_systems.xlsx"
    elif kind == "papers":
        dataframe = pd.DataFrame(
            list(
                Paper.objects.order_by("paper_id").values(
                    "paper_id",
                    "title",
                    "doi",
                    "pmid",
                    "journal",
                    "year",
                    "source_url",
                )
            )
        )
        filename = "PepRNA-DB_papers.xlsx"
    else:
        raise Http404("File not found.")

    dataframe = normalize_export_yes_no_blank(dataframe)
    return export_dataframe_response(dataframe, filename)
