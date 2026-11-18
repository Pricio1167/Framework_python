FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-production.txt ./
RUN pip install --no-cache-dir -r requirements-production.txt
RUN useradd --create-home --uid 1000 pharmacie
COPY --chown=pharmacie:pharmacie . /app
RUN mkdir -p /app/media /app/staticfiles && chown -R pharmacie:pharmacie /app/media /app/staticfiles
USER pharmacie
EXPOSE 8000
CMD ["sh", "deploy/demarrer.sh"]
