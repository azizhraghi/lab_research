import os
import json
from dotenv import load_dotenv
from mistralai.client import Mistral
from app.schemas.qualite import EvaluationIA
from app.schemas.orchestrateur import DecisionRoutageIA

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

def evaluer_projet(projet_data: dict) -> EvaluationIA:
    prompt = f"""Tu es un expert en évaluation qualité de projets de recherche scientifique.

Voici les données du projet à évaluer :
{json.dumps(projet_data, indent=2, ensure_ascii=False)}

Analyse ce projet et réponds UNIQUEMENT avec un JSON valide, sans aucun texte avant ou après, respectant exactement cette structure :
{{
  "forces": ["force 1", "force 2"],
  "faiblesses": ["faiblesse 1", "faiblesse 2"],
  "risques": ["risque 1", "risque 2"],
  "niveau_risque": "faible" | "modere" | "eleve" | "critique",
  "recommandation": "une recommandation concrète",
  "resume": "un résumé en 2-3 phrases"
}}"""

    
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

   

    contenu_brut = response.choices[0].message.content
    contenu_nettoye = contenu_brut.strip()
    if contenu_nettoye.startswith("```"):
        contenu_nettoye = contenu_nettoye.split("```")[1]
        if contenu_nettoye.startswith("json"):
            contenu_nettoye = contenu_nettoye[4:]
    contenu_nettoye = contenu_nettoye.strip()

    try:
        donnees_json = json.loads(contenu_nettoye)

        return EvaluationIA(
            projet_id=projet_data.get("id", "inconnu"),
            forces=donnees_json["forces"],
            faiblesses=donnees_json["faiblesses"],
            risques=donnees_json["risques"],
            niveau_risque=donnees_json["niveau_risque"],
            recommandation=donnees_json["recommandation"],
            resume=donnees_json["resume"]
        )

    except (json.JSONDecodeError, KeyError) as erreur:
        return EvaluationIA(
            projet_id=projet_data.get("id", "inconnu"),
            forces=[],
            faiblesses=[],
            risques=["Erreur lors de l'analyse IA : réponse du LLM non exploitable"],
            niveau_risque="critique",
            recommandation="Réessayer l'évaluation ou vérifier manuellement le projet",
            resume=f"L'évaluation automatique a échoué ({type(erreur).__name__})"
        )
    

AGENTS_VALIDES = [
    "MIS", "VeilleScientifique", "Bibliometrie",
    "Simulation", "Optimisation", "Qualite",
    "Orchestrateur", "aucune_action"
]


def decider_routage_ia(type_evenement: str, source_agent: str, payload: dict) -> DecisionRoutageIA:
    prompt = f"""Tu es le module de décision de l'Orchestrateur d'un système multi-agents de gestion de laboratoire de recherche.

Un événement a été reçu mais ne correspond à AUCUNE règle de routage connue :

Type d'événement : {type_evenement}
Agent source : {source_agent}
Payload : {json.dumps(payload, indent=2, ensure_ascii=False)}

Voici la liste FERMÉE des agents/actions valides du système. Tu DOIS choisir "agent_ou_action_recommande" UNIQUEMENT parmi cette liste, sans exception :
{", ".join(AGENTS_VALIDES)}

Analyse cet événement et réponds UNIQUEMENT avec un JSON valide, sans aucun texte avant ou après, respectant exactement cette structure :
{{
  "agent_ou_action_recommande": "un choix parmi la liste fermée ci-dessus",
  "niveau_urgence": "info" | "orange" | "rouge" | "critique",
  "justification": "explication concise de la décision",
  "necessite_intervention_humaine": true | false
}}"""

    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    contenu_brut = response.choices[0].message.content
    contenu_nettoye = contenu_brut.strip()
    if contenu_nettoye.startswith("```"):
        contenu_nettoye = contenu_nettoye.split("```")[1]
        if contenu_nettoye.startswith("json"):
            contenu_nettoye = contenu_nettoye[4:]
    contenu_nettoye = contenu_nettoye.strip()

    try:
        donnees_json = json.loads(contenu_nettoye)
        agent_choisi = donnees_json["agent_ou_action_recommande"]

        if agent_choisi not in AGENTS_VALIDES:
            agent_choisi = "aucune_action"

        return DecisionRoutageIA(
            type_evenement=type_evenement,
            agent_ou_action_recommande=agent_choisi,
            niveau_urgence=donnees_json["niveau_urgence"],
            justification=donnees_json["justification"],
            necessite_intervention_humaine=donnees_json["necessite_intervention_humaine"]
        )

    except (json.JSONDecodeError, KeyError) as erreur:
        return DecisionRoutageIA(
            type_evenement=type_evenement,
            agent_ou_action_recommande="aucune_action",
            niveau_urgence="critique",
            justification=f"Échec de la décision IA ({type(erreur).__name__}) — intervention humaine requise",
            necessite_intervention_humaine=True
        )