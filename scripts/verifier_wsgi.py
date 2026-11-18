"""Essai HTTP du serveur WSGI de production sur la base de contrôle fictive."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
revue = ROOT / "tmp" / "revue"
acces = json.loads((revue / "acces.json").read_text(encoding="utf-8"))
os.environ.update({"DJANGO_SETTINGS_MODULE": "config.settings", "DB_ENGINE": "sqlite",
    "SQLITE_PATH": str(revue / "revue.sqlite3"), "DEBUG": "false", "TRUST_PROXY": "true",
    "SECRET_KEY": acces["secret"], "ALLOWED_HOSTS": "127.0.0.1", "PYTHONUTF8": "1"})
import django
django.setup()
from django.contrib.auth import get_user_model, SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore
from django.conf import settings

acteur = get_user_model().objects.get(username="revue_locale")
session = SessionStore()
session[SESSION_KEY] = str(acteur.pk)
session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
session[HASH_SESSION_KEY] = acteur.get_session_auth_hash()
session.save()
with socket.socket() as controle:
    controle.bind(("127.0.0.1", 0))
    port = controle.getsockname()[1]
processus = subprocess.Popen([sys.executable, "-m", "waitress", f"--listen=127.0.0.1:{port}",
    "--trusted-proxy=127.0.0.1", "--trusted-proxy-headers=x-forwarded-proto", "config.wsgi:application"],
    cwd=ROOT, env=os.environ.copy(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for tentative in range(60):
        if processus.poll() is not None:
            raise RuntimeError("Le serveur WSGI s’est arrêté.")
        try:
            with urlopen(Request(f"http://127.0.0.1:{port}/connexion/", headers={"X-Forwarded-Proto": "https"}), timeout=2) as reponse:
                assert reponse.status == 200
                assert "Secure" in reponse.headers.get("Set-Cookie", "")
                assert reponse.headers.get("Strict-Transport-Security")
            break
        except URLError:
            time.sleep(.25)
    else:
        raise RuntimeError("Le serveur WSGI ne répond pas.")
    routes = ["/", "/gestion/medicaments/", "/gestion/achats/", "/gestion/stocks/", "/gestion/ventes/",
              "/rapports/", "/utilisateurs/", "/parametres/", "/ventes/nouvelle/"]
    from ventes.models import Vente
    from medicaments.models import Medicament
    from fournisseurs.models import Fournisseur
    from clients.models import Client
    from achats.models import CommandeAchat, ReceptionAchat
    medicament = Medicament.objects.first()
    routes += [f"/ventes/{Vente.objects.first().pk}/", f"/fiches/medicaments/{medicament.pk}/",
               f"/fiches/categories/{medicament.categorie_id}/", f"/fiches/fournisseurs/{Fournisseur.objects.first().pk}/",
               f"/fiches/clients/{Client.objects.first().pk}/", f"/gestion/achats/{CommandeAchat.objects.first().pk}/",
               f"/gestion/receptions/{ReceptionAchat.objects.first().pk}/", "/compte/mot-de-passe/", "/compte/reinitialiser/"]
    for route in routes:
        requete = Request(f"http://127.0.0.1:{port}{route}", headers={
            "X-Forwarded-Proto": "https", "Cookie": f"{settings.SESSION_COOKIE_NAME}={session.session_key}"})
        with urlopen(requete, timeout=15) as reponse:
            assert reponse.status == 200, route
            assert reponse.headers.get("X-Content-Type-Options") == "nosniff"
    print(f"WSGI de production : {len(routes)} pages authentifiées et cookies HTTPS vérifiés.")
    (revue / "resultat-wsgi.json").write_text(json.dumps({"pages": len(routes), "statut": "OK"}), encoding="utf-8")
finally:
    processus.terminate()
    processus.wait(timeout=15)
    session.delete()
