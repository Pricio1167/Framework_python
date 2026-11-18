"use strict";
const donnees = document.getElementById("evolution-ventes");
const graphique = document.getElementById("graphique-ventes");
if (donnees && graphique && typeof Chart !== "undefined") {
  const points = JSON.parse(donnees.textContent);
  new Chart(graphique, {
    type: "line",
    data: {
      labels: points.map((point) => point.date),
      datasets: [
        {label: "Chiffre d’affaires brut", data: points.map((point) => Number(point.brut)), borderColor: "#2857a4", backgroundColor: "#2857a410", fill: true, tension: .3, pointRadius: 3},
        {label: "Chiffre d’affaires net des retours", data: points.map((point) => Number(point.net)), borderColor: "#138573", borderDash: [5, 4], tension: .3, pointRadius: 3},
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? false : undefined,
      interaction: {intersect: false, mode: "index"},
      plugins: {legend: {position: "bottom", labels: {usePointStyle: true, padding: 22}}},
      scales: {y: {beginAtZero: true, ticks: {callback: (valeur) => new Intl.NumberFormat("fr-FR").format(valeur) + " Ar"}}, x: {grid: {display: false}}},
    },
  });
}
