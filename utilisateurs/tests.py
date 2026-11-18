from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from .roles import configurer_roles


class ComptesMetierTests(TestCase):
    def test_creation_et_connexion_caissier(self):
        configurer_roles()
        modele = get_user_model()
        admin = modele.objects.create_superuser(username="admin-test", password="Admin-test-642!")
        caissier = Group.objects.get(name="Caissier")
        mot_de_passe = "Horizon-731!Violet"
        self.client.force_login(admin)
        creation = reverse("utilisateur_creation")
        self.assertContains(self.client.get(creation), 'type="checkbox" name="groups"')
        reponse = self.client.post(creation, {
            "username": "caisse-test",
            "password1": mot_de_passe,
            "password2": mot_de_passe,
            "groups": [caissier.pk],
        })
        self.assertRedirects(
            reponse, reverse("utilisateurs_liste"),
            msg_prefix=str(reponse.context["form"].errors) if reponse.status_code == 200 else "",
        )
        compte = modele.objects.get(username="caisse-test")
        self.assertFalse(compte.is_staff)
        self.assertEqual(list(compte.groups.all()), [caissier])
        self.client.logout()
        reponse = self.client.post(reverse("login"), {
            "username": compte.username,
            "password": mot_de_passe,
        })
        self.assertRedirects(reponse, reverse("dashboard:accueil"))
        self.assertEqual(self.client.get(reverse("vente_creation")).status_code, 200)
        self.assertEqual(self.client.get(reverse("utilisateurs_liste")).status_code, 403)
