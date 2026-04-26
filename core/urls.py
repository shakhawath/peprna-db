from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("browse/", views.browse, name="browse"),
    path("downloads/", views.downloads_page, name="downloads"),
    path("downloads/<str:kind>/", views.download_dataset, name="download_dataset"),
    path("faq/", views.faq_page, name="faq"),
    path("help/", views.help_page, name="help"),
    path("about/", views.about_page, name="about"),
    path("contact/", views.contact_page, name="contact"),
    path("experiment/<int:experiment_id>/", views.experiment_detail, name="experiment_detail"),
    path("rna/<int:experiment_id>/", views.rna_detail, name="rna_detail"),
    path("peptide/<int:peptide_id>/", views.peptide_detail, name="peptide_detail"),
    path("paper/<int:paper_id>/", views.paper_detail, name="paper_detail"),
]
