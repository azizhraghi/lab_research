from app.services.llm_client import evaluer_projet

projet_test = {
    "id": "proj_001",
    "nom": "Étude sur les réseaux de neurones bayésiens",
    "budget": 15000,
    "budget_utilise": 14800,
    "avancement": "en retard de 3 semaines",
    "equipe_taille": 4
}

resultat = evaluer_projet(projet_test)

print(resultat)