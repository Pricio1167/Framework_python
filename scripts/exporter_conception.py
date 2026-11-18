"""Exporte la structure des modèles, sans lire les données métier."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.apps import apps

dossier = ROOT / "docs" / "conception"
dossier.mkdir(parents=True, exist_ok=True)
applications = {"utilisateurs", "medicaments", "clients", "fournisseurs", "achats", "stock", "ventes", "dashboard"}
modeles = [m for m in apps.get_models() if m._meta.app_label in applications]
schema = []
mld = ["# Modèle logique des données", "", "Structure générée depuis les modèles Django. Aucune donnée métier n’est exportée.", ""]
uml = ["classDiagram"]
for model in modeles:
    meta = model._meta
    entree = {"modele": meta.label, "table": meta.db_table, "champs": [], "relations_n_n": [], "contraintes": []}
    mld += [f"## {meta.label} — `{meta.db_table}`", "", "| Colonne | Type | Clé / relation | Null autorisé |", "| --- | --- | --- | --- |"]
    uml.append(f"  class {model.__name__} {{")
    for champ in meta.fields:
        type_champ = champ.get_internal_type()
        if getattr(champ, "decimal_places", None) is not None:
            type_champ += f"({champ.max_digits},{champ.decimal_places})"
        elif getattr(champ, "max_length", None):
            type_champ += f"({champ.max_length})"
        cible = champ.related_model._meta.label if champ.is_relation else None
        suppression = getattr(getattr(champ, "remote_field", None), "on_delete", None)
        relation = f"FK → {cible} ({suppression.__name__})" if cible else "PK" if champ.primary_key else ""
        entree["champs"].append({"nom": champ.name, "colonne": champ.column, "type": champ.get_internal_type(),
                                 "cle_primaire": champ.primary_key, "unique": champ.unique, "null": champ.null, "cible": cible,
                                 "max_length": getattr(champ, "max_length", None), "max_digits": getattr(champ, "max_digits", None),
                                 "decimal_places": getattr(champ, "decimal_places", None), "choix": list(champ.choices or [])})
        mld.append(f"| {champ.column} | {type_champ} | {relation} | {'Oui' if champ.null else 'Non'} |")
        uml.append(f"    {champ.get_internal_type()} {champ.name}")
    uml.append("  }")
    for champ in meta.local_many_to_many:
        entree["relations_n_n"].append({"champ": champ.name, "table_intermediaire": champ.remote_field.through._meta.db_table,
                                        "cible": champ.related_model._meta.label})
        mld += ["", f"Relation N–N `{champ.name}` vers `{champ.related_model._meta.label}` par `{champ.remote_field.through._meta.db_table}`."]
    for contrainte in meta.constraints:
        entree["contraintes"].append({"nom": contrainte.name, "type": type(contrainte).__name__})
        mld += ["", f"Contrainte : `{contrainte.name}` ({type(contrainte).__name__})."]
    mld.append("")
    schema.append(entree)
for model in modeles:
    for champ in model._meta.fields:
        if champ.is_relation and champ.related_model in modeles:
            cardinalite = "0..1" if champ.null else "1"
            uml.append(f'  {champ.related_model.__name__} "{cardinalite}" <-- "0..*" {model.__name__} : {champ.name}')
(dossier / "schema.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
(dossier / "MLD.md").write_text("\n".join(mld)+"\n", encoding="utf-8")
(dossier / "UML_classes.mmd").write_text("\n".join(uml)+"\n", encoding="utf-8")
print(f"Conception exportée : {len(modeles)} modèles, sans données métier.")
