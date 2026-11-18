# Déploiement avec HTTPS et PostgreSQL

Cette configuration conserve la base SQLite locale. Docker Compose utilise un
volume PostgreSQL séparé, sans publier le port SQL ni le port de l'application.

Sur un serveur Docker dont le domaine DNS pointe vers ce serveur :

1. Définir dans un `.env` non versionné `SECRET_KEY`, `DB_PASSWORD` et
   `PHARMAGEST_DOMAIN` avec le vrai domaine. Générer deux secrets longs et différents.
2. Ouvrir les ports TCP 80 et 443 pour Caddy. Ne pas publier PostgreSQL.
3. Sauvegarder les données existantes avant tout changement de version.
4. Lancer `docker compose up -d --build`.
5. Créer le premier compte avec `docker compose exec app python manage.py createsuperuser`.
6. Contrôler `docker compose logs`, la connexion et les parcours métier HTTPS.

Caddy obtient et renouvelle le certificat pour le domaine réel. Le proxy est le
seul point d'entrée de l'application ; Waitress reçoit les en-têtes du proxy
sur le réseau interne Docker. `TRUST_PROXY=true` se justifie uniquement
dans ce réseau contrôlé. Ne pas exposer directement l'application avec cette option.

Sauvegarder PostgreSQL avec `pg_dump` en format custom, et copier séparément le
volume `medias`, les secrets et la version du code. Tester régulièrement
`pg_restore` dans une autre base avant d'envisager une restauration active.
Ne pas exécuter `docker compose down -v` : cela supprime les volumes de données.

Le script `scripts/verifier_postgresql.py` teste les migrations, la concurrence,
le transfert d'une copie SQLite et un cycle pg_dump/pg_restore sur une instance
isolée locale. Il ne remplace pas le suivi, les sauvegardes hors serveur ou les
informations réelles de votre hébergement.
