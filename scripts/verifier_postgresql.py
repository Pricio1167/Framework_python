"""Vérifie PostgreSQL sur un cluster jetable, sans modifier la base de travail."""
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent


def run(args, env, **kwargs):
    subprocess.run([str(arg) for arg in args], cwd=ROOT, env=env, check=True, **kwargs)


def normaliser(path):
    donnees = json.loads(path.read_text(encoding="utf-8"))
    for objet in donnees:
        for champ, valeur in objet["fields"].items():
            if isinstance(valeur, list):
                objet["fields"][champ] = sorted(valeur, key=lambda v: json.dumps(v, sort_keys=True))
    return sorted(donnees, key=lambda v: (v["model"], str(v.get("pk")), json.dumps(v, sort_keys=True)))


def main():
    executable = shutil.which("initdb")
    if not executable:
        raise SystemExit("initdb introuvable : ajouter PostgreSQL/bin au PATH.")
    bin_dir = Path(executable).parent
    (ROOT / "tmp").mkdir(exist_ok=True)
    dossier = Path(tempfile.mkdtemp(prefix="verification-pg-", dir=ROOT / "tmp"))
    cluster = dossier / "cluster"
    mot_de_passe = secrets.token_urlsafe(40)
    fichier_mdp = dossier / "initialisation.pw"
    fichier_mdp.write_text(mot_de_passe, encoding="ascii")
    with socket.socket() as connexion:
        connexion.bind(("127.0.0.1", 0))
        port = connexion.getsockname()[1]
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "PGPASSWORD": mot_de_passe, "PGHOST": "127.0.0.1",
           "PGPORT": str(port), "PGUSER": "verification", "DEBUG": "true",
           "SECRET_KEY": secrets.token_urlsafe(60), "DB_ENGINE": "postgresql",
           "DB_NAME": "pharmagest_verification", "DB_USER": "verification",
           "DB_PASSWORD": mot_de_passe, "DB_HOST": "127.0.0.1", "DB_PORT": str(port)}
    demarre = False
    try:
        run([bin_dir / "initdb.exe", "-D", cluster, "-U", "verification", "--auth=scram-sha-256",
             "--pwfile", fichier_mdp, "--encoding=UTF8", "--locale=C"], env)
        fichier_mdp.unlink()
        run([bin_dir / "pg_ctl.exe", "-D", cluster, "-l", dossier / "postgresql.log",
             "-o", f"-h 127.0.0.1 -p {port}", "-w", "start"], env)
        demarre = True
        run([bin_dir / "createdb.exe", env["DB_NAME"]], env)
        manage = [sys.executable, "manage.py"]
        run([*manage, "migrate", "--noinput"], env)
        journal = dossier / "tests.log"
        print(f"Journal des tests : {journal}", flush=True)
        with journal.open("w", encoding="utf-8") as sortie:
            run([*manage, "test", "--noinput", *sys.argv[1:]], env,
                stdout=sortie, stderr=subprocess.STDOUT)
        print("Tests PostgreSQL réussis.", flush=True)

        # L'export porte sur une copie SQLite cohérente, jamais sur une base modifiée.
        copie = dossier / "source.sqlite3"
        with sqlite3.connect((ROOT / "db.sqlite3").as_uri() + "?mode=ro", uri=True) as source:
            with sqlite3.connect(copie) as destination:
                source.backup(destination)
                assert destination.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        env_sqlite = {**env, "DB_ENGINE": "sqlite", "SQLITE_PATH": str(copie)}
        run([*manage, "migrate", "--noinput"], env_sqlite)
        sauvegardes_sqlite = dossier / "sauvegardes-sqlite"
        run([*manage, "sauvegarder_sqlite", "--destination", sauvegardes_sqlite], env_sqlite)
        sauvegarde_sqlite = next(sauvegardes_sqlite.glob("*.sqlite3"))
        restauration_sqlite = dossier / "restauration.sqlite3"
        shutil.copyfile(sauvegarde_sqlite, restauration_sqlite)
        with sqlite3.connect(copie) as origine, sqlite3.connect(restauration_sqlite) as restauree:
            assert restauree.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert list(origine.iterdump()) == list(restauree.iterdump()), "Restauration SQLite différente."
        options = ["--natural-foreign", "--natural-primary", "--exclude", "contenttypes",
                   "--exclude", "auth.permission", "--exclude", "sessions"]
        export = dossier / "source.json"
        transfert = dossier / "transfert.json"
        run([*manage, "dumpdata", *options, "--output", export], env_sqlite)
        run([*manage, "loaddata", export], env)
        run([*manage, "dumpdata", *options, "--output", transfert], env)
        assert normaliser(export) == normaliser(transfert), "Le transfert des données diffère de SQLite."

        # Sauvegarde logique et restauration dans une seconde base isolée.
        sauvegarde = dossier / "sauvegarde.dump"
        run([bin_dir / "pg_dump.exe", "--format=custom", "--file", sauvegarde, env["DB_NAME"]], env)
        run([bin_dir / "createdb.exe", "pharmagest_restauration"], env)
        run([bin_dir / "pg_restore.exe", "--exit-on-error", "--dbname", "pharmagest_restauration", sauvegarde], env)
        restaure = dossier / "restaure.json"
        run([*manage, "dumpdata", *options, "--output", restaure], {**env, "DB_NAME": "pharmagest_restauration"})
        assert normaliser(transfert) == normaliser(restaure), "La restauration diffère de la sauvegarde."
        resultat = {"tests_postgresql": "OK", "transfert_sqlite": "OK", "restauration_sqlite": "OK",
                    "restauration_postgresql": "OK", "objets_transferes": len(normaliser(export))}
        (dossier / "resultat.json").write_text(json.dumps(resultat, indent=2), encoding="utf-8")
        print(json.dumps(resultat, ensure_ascii=False))
        print(f"Rapport de vérification : {dossier / 'resultat.json'}")
    finally:
        if fichier_mdp.exists():
            fichier_mdp.unlink()
        if demarre:
            run([bin_dir / "pg_ctl.exe", "-D", cluster, "-m", "fast", "-w", "stop"], env)


if __name__ == "__main__":
    main()
