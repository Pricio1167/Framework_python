from django.core.exceptions import PermissionDenied


def exiger_permission(utilisateur, permission):
    if not utilisateur or not utilisateur.is_active or not utilisateur.has_perm(permission):
        raise PermissionDenied("Vous ne disposez pas des droits nécessaires.")
