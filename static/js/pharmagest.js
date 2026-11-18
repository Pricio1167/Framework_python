"use strict";
const boutonMenu = document.getElementById("menu-toggle");
function fermerMenu() {
  document.body.classList.remove("nav-open");
  if (boutonMenu) boutonMenu.setAttribute("aria-expanded", "false");
}
if (boutonMenu) {
  boutonMenu.addEventListener("click", () => {
    const ouvert = document.body.classList.toggle("nav-open");
    boutonMenu.setAttribute("aria-expanded", String(ouvert));
    boutonMenu.setAttribute("aria-label", ouvert ? "Fermer le menu" : "Ouvrir le menu");
    if (ouvert) document.querySelector("#navigation-principale a")?.focus();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && document.body.classList.contains("nav-open")) {
      fermerMenu();
      boutonMenu.focus();
    }
  });
  document.addEventListener("click", (event) => {
    if (!event.target.closest("#navigation-principale") && !event.target.closest("#menu-toggle")) fermerMenu();
  });
}
document.querySelectorAll('form[method="post"]').forEach((form) => {
  form.addEventListener("submit", (event) => {
    const confirmation = form.dataset.confirm;
    if (confirmation && !window.confirm(confirmation)) {
      event.preventDefault();
      return;
    }
    if (form.dataset.submitting === "true") {
      event.preventDefault();
      return;
    }
    form.dataset.submitting = "true";
    form.setAttribute("aria-busy", "true");
    form.querySelectorAll('button[type="submit"],button:not([type])').forEach((button) => {
      button.disabled = true;
      button.textContent = "Traitement…";
    });
  });
});
window.addEventListener("pageshow", (event) => {
  if (event.persisted) window.location.reload();
});
