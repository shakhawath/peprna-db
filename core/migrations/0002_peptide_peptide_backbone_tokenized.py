# Generated for RNA Delivery DB importer updates.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="peptide",
            name="peptide_backbone_tokenized",
            field=models.TextField(blank=True, null=True),
        ),
    ]
