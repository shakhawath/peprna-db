# Generated for RNA Delivery DB peptide residue annotations.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_peptide_peptide_backbone_tokenized"),
    ]

    operations = [
        migrations.AddField(
            model_name="peptide",
            name="noncanonical_residues",
            field=models.TextField(blank=True, null=True),
        ),
    ]
