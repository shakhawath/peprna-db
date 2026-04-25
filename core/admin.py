from django.contrib import admin

from .models import Experiment, Paper, Peptide, VocabTerm


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ("paper_id", "title", "year", "doi", "journal")
    search_fields = ("paper_id", "title", "doi", "pmid", "journal")
    list_filter = ("year", "journal")


@admin.register(Peptide)
class PeptideAdmin(admin.ModelAdmin):
    list_display = ("peptide_id", "peptide_name", "sequence_length", "noncanonical_residues")
    search_fields = (
        "peptide_id",
        "peptide_name",
        "peptide_sequence_raw",
        "peptide_backbone_clean",
        "peptide_backbone_tokenized",
        "noncanonical_residues",
    )
    list_filter = ("stereochemistry_detected",)


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = (
        "experiment_id",
        "paper",
        "peptide",
        "rna_type",
        "delivery_success_class",
        "in_vivo_flag",
        "uptake_confirmed",
    )
    search_fields = (
        "experiment_id",
        "paper__title",
        "paper__paper_id",
        "peptide__peptide_name",
        "peptide__peptide_sequence_raw",
        "rna_payload_or_target",
    )
    list_filter = (
        "delivery_success_class",
        "in_vivo_flag",
        "uptake_confirmed",
        "rna_type",
        "model_scope",
        "administration_route",
    )
    autocomplete_fields = ("paper", "peptide")


@admin.register(VocabTerm)
class VocabTermAdmin(admin.ModelAdmin):
    list_display = ("field_name", "raw_value", "normalized_value", "is_active")
    search_fields = ("field_name", "raw_value", "normalized_value", "display_label")
    list_filter = ("field_name", "is_active")
