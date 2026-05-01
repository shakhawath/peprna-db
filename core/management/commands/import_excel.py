from pathlib import Path
from contextlib import nullcontext
from decimal import Decimal, InvalidOperation
import hashlib
import math
import re

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Experiment, Paper, Peptide


TRUE_VALUES = {"1", "1.0", "true", "t", "yes", "y", "on", "confirmed"}
FALSE_VALUES = {"0", "0.0", "false", "f", "no", "n", "off", "not confirmed", "unconfirmed"}
TWO_DECIMAL_PLACES = Decimal("0.01")


def clean_value(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def row_value(row, *names):
    for name in names:
        if name in row:
            value = clean_value(row[name])
            if value is not None:
                return value
        for key in row:
            if key.lower() == name.lower():
                value = clean_value(row[key])
                if value is not None:
                    return value
    return None


def as_string(value):
    value = clean_value(value)
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def as_int(value):
    value = clean_value(value)
    if value is None:
        return None
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def as_bool(value):
    value = clean_value(value)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value == 1:
            return True
        if value == 0:
            return False
    text = str(value).strip().lower()
    if text in TRUE_VALUES:
        return True
    if text in FALSE_VALUES:
        return False
    return None


def as_presence_bool(value):
    value = clean_value(value)
    if value is None:
        return None
    parsed = as_bool(value)
    if parsed is not None:
        return parsed
    return True


def as_decimal(value):
    value = clean_value(value)
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    match = re.search(r"[-+]?\d*\.?\d+", text)
    number = match.group(0) if match else ""
    if not number or number in {"-", ".", "-."}:
        return None
    try:
        return Decimal(number).quantize(TWO_DECIMAL_PLACES)
    except InvalidOperation:
        return None


def normalize_doi(value):
    value = as_string(value)
    if not value:
        return None
    value = value.strip().lower()
    prefixes = (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
    )
    for prefix in prefixes:
        if value.startswith(prefix):
            value = value[len(prefix) :]
            break
    return value.strip() or None


def infer_model_scope(model_type, in_vivo_flag):
    model_type = as_string(model_type)
    text = (model_type or "").lower()
    if in_vivo_flag is True:
        return "in_vivo"
    if any(word in text for word in ["in vivo", "mouse", "mice", "rat", "zebrafish", "xenograft"]):
        return "in_vivo"
    if any(word in text for word in ["ex vivo", "organoid", "tissue", "primary tissue"]):
        return "ex_vivo"
    if text:
        return "in_vitro"
    return None


def short_hash(*parts, length=12):
    joined = "|".join(as_string(part) or "" for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:length]


def row_hash(row):
    parts = []
    for key in sorted(row.keys()):
        parts.append(f"{key}={as_string(row[key]) or ''}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


class Command(BaseCommand):
    help = "Import curated RNA delivery data from Excel"

    def add_arguments(self, parser):
        parser.add_argument("excel_path", type=str)
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Read and validate the Excel file, but roll back all database changes.",
        )

    def handle(self, *args, **options):
        excel_path = Path(options["excel_path"])
        dry_run = options["dry_run"]
        if not excel_path.exists():
            raise CommandError(f"File not found: {excel_path}")

        df = pd.read_excel(excel_path, sheet_name=0)
        df = df.where(pd.notna(df), None)

        rows_imported = 0
        papers_created = 0
        papers_updated = 0
        peptides_created = 0
        peptides_updated = 0
        experiments_created = 0
        experiments_updated = 0
        skipped_missing_sequence = 0
        missing_counts = {
            "paper_id": 0,
            "title": 0,
            "year": 0,
            "rna_type": 0,
            "model_type": 0,
            "output_type": 0,
        }
        invalid_counts = {
            "in_vivo_flag": 0,
            "uptake_confirmed": 0,
            "size_nm": 0,
            "zeta_mV": 0,
        }

        import_context = nullcontext() if dry_run else transaction.atomic()
        with import_context:
            for index, raw_row in df.iterrows():
                row = raw_row.to_dict()
                peptide_sequence = as_string(row_value(row, "peptide_sequence_raw", "sequence"))
                if not peptide_sequence:
                    skipped_missing_sequence += 1
                    continue

                paper_id = as_string(row_value(row, "paper_id"))
                title = as_string(row_value(row, "title", "paper_title"))
                doi = normalize_doi(row_value(row, "doi"))
                pmid = as_string(row_value(row, "pmid"))
                journal = as_string(row_value(row, "journal"))
                year = as_int(row_value(row, "year", "publication_year"))

                if not paper_id:
                    missing_counts["paper_id"] += 1
                    paper_id = f"paper_{short_hash(doi, title, year)}"
                if not title:
                    missing_counts["title"] += 1
                    title = "Untitled paper"
                if year is None:
                    missing_counts["year"] += 1
                    year = 0

                paper_defaults = {
                    "title": title,
                    "doi": doi,
                    "pmid": pmid,
                    "journal": journal,
                    "year": year,
                    "paper_file": as_string(row_value(row, "paper_file")),
                    "source_url": as_string(row_value(row, "source_url", "url")),
                    "abstract": as_string(row_value(row, "abstract")),
                }
                if dry_run:
                    paper_was_created = not Paper.objects.filter(paper_id=paper_id).exists()
                    paper = Paper(paper_id=paper_id, **paper_defaults)
                else:
                    paper, paper_was_created = Paper.objects.update_or_create(
                        paper_id=paper_id,
                        defaults=paper_defaults,
                    )
                if paper_was_created:
                    papers_created += 1
                else:
                    papers_updated += 1

                peptide_id = as_string(row_value(row, "peptide_id"))
                if not peptide_id:
                    peptide_id = f"pep_{short_hash(peptide_sequence)}"

                peptide_defaults = {
                    "peptide_name": as_string(row_value(row, "peptide_name", "name")),
                    "peptide_sequence_raw": peptide_sequence,
                    "peptide_backbone_clean": as_string(row_value(row, "peptide_backbone_clean")),
                    "peptide_backbone_tokenized": as_string(
                        row_value(row, "peptide_backbone_tokenized")
                    ),
                    "sequence_engineering_extracted": as_string(
                        row_value(row, "sequence_engineering_extracted")
                    ),
                    "stereochemistry_detected": as_string(
                        row_value(row, "stereochemistry_detected")
                    ),
                    "peptide_modifications": as_string(row_value(row, "peptide_modifications")),
                    "sequence_length": as_int(row_value(row, "sequence_length")),
                    "has_noncanonical_residues": as_presence_bool(
                        row_value(row, "has_noncanonical_residues")
                    ),
                    "noncanonical_residues": as_string(
                        row_value(row, "noncanonical_residues", "has_noncanonical_residues")
                    ),
                }
                if peptide_defaults["sequence_length"] is None:
                    backbone = peptide_defaults["peptide_backbone_clean"]
                    peptide_defaults["sequence_length"] = len(backbone or peptide_sequence)

                if dry_run:
                    peptide_was_created = not Peptide.objects.filter(peptide_id=peptide_id).exists()
                    peptide = Peptide(peptide_id=peptide_id, **peptide_defaults)
                else:
                    peptide, peptide_was_created = Peptide.objects.update_or_create(
                        peptide_id=peptide_id,
                        defaults=peptide_defaults,
                    )
                if peptide_was_created:
                    peptides_created += 1
                else:
                    peptides_updated += 1

                in_vivo_source = row_value(row, "in_vivo_flag")
                uptake_source = row_value(row, "uptake_confirmed")
                size_source = row_value(row, "size_nm")
                zeta_source = row_value(row, "zeta_mv", "zeta_mV", "zeta_mvolt")

                in_vivo_flag = as_bool(in_vivo_source)
                uptake_confirmed = as_bool(uptake_source)
                size_nm = as_decimal(size_source)
                zeta_mv = as_decimal(zeta_source)

                if in_vivo_source is not None and in_vivo_flag is None:
                    invalid_counts["in_vivo_flag"] += 1
                if uptake_source is not None and uptake_confirmed is None:
                    invalid_counts["uptake_confirmed"] += 1
                if size_source is not None and size_nm is None:
                    invalid_counts["size_nm"] += 1
                if zeta_source is not None and zeta_mv is None:
                    invalid_counts["zeta_mV"] += 1

                model_type = as_string(row_value(row, "model_type"))
                model_scope = as_string(row_value(row, "model_scope")) or infer_model_scope(
                    model_type, in_vivo_flag
                )
                rna_type = as_string(row_value(row, "rna_type_final", "rna_type"))
                output_type = as_string(row_value(row, "output_type"))

                if not rna_type:
                    missing_counts["rna_type"] += 1
                if not model_type:
                    missing_counts["model_type"] += 1
                if not output_type:
                    missing_counts["output_type"] += 1

                raw_hash = row_hash(row)
                experiment_id = as_string(row_value(row, "experiment_id", "Experimental_ID"))
                if not experiment_id:
                    experiment_id = f"exp_{short_hash(raw_hash)}"

                experiment_defaults = {
                    "paper": paper,
                    "peptide": peptide,
                    "delivery_success_class": as_string(row_value(row, "delivery_success_class")),
                    "in_vivo_flag": in_vivo_flag,
                    "uptake_confirmed": uptake_confirmed,
                    "label_confidence": as_string(row_value(row, "label_confidence")),
                    "in_vitro_functional_effect": as_string(
                        row_value(row, "in_vitro_functional_effect")
                    ),
                    "endosomal_escape_evidence": as_string(
                        row_value(row, "endosomal_escape_evidence")
                    ),
                    "rna_type": rna_type,
                    "rna_payload_or_target": as_string(
                        row_value(
                            row,
                            "rna_name_or_payload_final",
                            "rna_payload_or_target",
                        )
                    ),
                    "target_gene_or_transcript": as_string(
                        row_value(
                            row,
                            "target_gene_or_target_final",
                            "target_gene_or_transcript",
                        )
                    ),
                    "rna_sequence": as_string(
                        row_value(row, "rna_sequence_final", "rna_sequence")
                    ),
                    "sense_strand": as_string(
                        row_value(row, "sense_strand_final", "sense_strand")
                    ),
                    "antisense_strand": as_string(
                        row_value(row, "antisense_strand_final", "antisense_strand")
                    ),
                    "rna_modifications": as_string(
                        row_value(
                            row,
                            "rna_chemistry_or_modification_final",
                            "rna_modifications",
                        )
                    ),
                    "peptide_concentration": as_string(row_value(row, "peptide_concentration")),
                    "rna_concentration": as_string(row_value(row, "rna_concentration")),
                    "mixing_ratio": as_string(row_value(row, "mixing_ratio")),
                    "formulation_format": as_string(row_value(row, "formulation_format")),
                    "formulation_components": as_string(row_value(row, "formulation_components")),
                    "size_nm": size_nm,
                    "zeta_mv": zeta_mv,
                    "model_scope": model_scope,
                    "model_type": model_type,
                    "cell_lines_or_primary_cells": as_string(
                        row_value(row, "cell_lines_or_primary_cells")
                    ),
                    "animal_model": as_string(row_value(row, "animal_model")),
                    "administration_route": as_string(row_value(row, "administration_route")),
                    "output_type": output_type,
                    "output_value": as_string(row_value(row, "output_value")),
                    "output_units": as_string(row_value(row, "output_units")),
                    "output_notes": as_string(row_value(row, "output_notes")),
                    "toxicity_notes": as_string(row_value(row, "toxicity_notes")),
                    "raw_row_hash": raw_hash,
                    "curation_notes": as_string(row_value(row, "curation_notes")),
                }

                if dry_run:
                    experiment_was_created = not Experiment.objects.filter(
                        experiment_id=experiment_id
                    ).exists()
                else:
                    _, experiment_was_created = Experiment.objects.update_or_create(
                        experiment_id=experiment_id,
                        defaults=experiment_defaults,
                    )
                if experiment_was_created:
                    experiments_created += 1
                else:
                    experiments_updated += 1
                rows_imported += 1

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run complete. No database changes were saved."))
        else:
            self.stdout.write(self.style.SUCCESS("Import complete"))
        self.stdout.write(f"Rows read: {len(df)}")
        self.stdout.write(f"Rows imported: {rows_imported}")
        self.stdout.write(f"Rows skipped without peptide_sequence_raw: {skipped_missing_sequence}")
        self.stdout.write(f"Papers created: {papers_created}")
        self.stdout.write(f"Papers updated: {papers_updated}")
        self.stdout.write(f"Peptides created: {peptides_created}")
        self.stdout.write(f"Peptides updated: {peptides_updated}")
        self.stdout.write(f"Experiments created: {experiments_created}")
        self.stdout.write(f"Experiments updated: {experiments_updated}")
        self.stdout.write("Missing field counts:")
        for field_name, count in missing_counts.items():
            self.stdout.write(f"  {field_name}: {count}")
        self.stdout.write("Invalid parse counts:")
        for field_name, count in invalid_counts.items():
            self.stdout.write(f"  {field_name}: {count}")
