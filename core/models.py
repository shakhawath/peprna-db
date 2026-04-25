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
    peptide_backbone_tokenized = models.TextField(blank=True, null=True)
    sequence_engineering_extracted = models.TextField(blank=True, null=True)
    stereochemistry_detected = models.CharField(max_length=100, blank=True, null=True)
    peptide_modifications = models.TextField(blank=True, null=True)
    sequence_length = models.IntegerField(blank=True, null=True)
    has_noncanonical_residues = models.BooleanField(blank=True, null=True)
    noncanonical_residues = models.TextField(blank=True, null=True)

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
