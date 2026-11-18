from django.http import FileResponse


class PDFResponse(FileResponse):
    """Une réponse PDF peut être fermée par le serveur puis par son appelant."""

    def close(self):
        if not self.closed:
            super().close()
