# -*- coding: utf-8 -*-
"""LLM Client – Mistral AI integration with domain-specific functions.

Original: async chat + embeddings.
Added: evaluer_projet() and decider_routage_ia() from Friend 2 (converted to async).
"""
import os
import json
from typing import List, Optional

from mistralai.client import Mistral
from shared.config import settings


class LLMClient:
    def __init__(self):
        api_key = settings.MISTRAL_API_KEY or os.environ.get("MISTRAL_API_KEY", "")
        self.client = Mistral(api_key=api_key)

    async def chat(self, messages: List[dict], model: str = "mistral-small-latest", temperature: float = 0.7) -> str:
        """
        Send a chat completion request to Mistral AI.
        messages format: [{"role": "user", "content": "Hello"}]
        """
        response = await self.client.chat.complete_async(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content

    async def generate_embeddings(self, texts: List[str], model: str = "mistral-embed") -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        response = await self.client.embeddings.create_async(
            model=model,
            inputs=texts,
        )
        return [data.embedding for data in response.data]

    # ── Domain-specific LLM functions (from Friend 2) ─────────────────

    async def evaluer_projet(self, projet_data: dict) -> dict:
        """AI-powered project quality evaluation (from Friend 2, converted to async).

        Returns an EvaluationIA-compatible dict with forces, faiblesses, risques, etc.
        """
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

        try:
            response = await self.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            contenu = response.strip()
            if contenu.startswith("```"):
                contenu = contenu.split("```")[1]
                if contenu.startswith("json"):
                    contenu = contenu[4:]
            contenu = contenu.strip()

            return json.loads(contenu)

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            return {
                "forces": [],
                "faiblesses": [],
                "risques": [f"Erreur lors de l'analyse IA : {type(e).__name__}"],
                "niveau_risque": "critique",
                "recommandation": "Réessayer l'évaluation ou vérifier manuellement le projet",
                "resume": f"L'évaluation automatique a échoué ({type(e).__name__})",
            }

    async def decider_routage_ia(self, type_evenement: str, source_agent: str, payload: dict) -> dict:
        """AI-powered routing decision for unmatched events (from Friend 2, converted to async).

        Returns a DecisionRoutageIA-compatible dict.
        """
        agents_valides = [
            "MIS", "VeilleScientifique", "Bibliometrie",
            "Simulation", "Optimisation", "Qualite",
            "Orchestrateur", "aucune_action",
        ]

        prompt = f"""Tu es le module de décision de l'Orchestrateur d'un système multi-agents de gestion de laboratoire de recherche.

Un événement a été reçu mais ne correspond à AUCUNE règle de routage connue :

Type d'événement : {type_evenement}
Agent source : {source_agent}
Payload : {json.dumps(payload, indent=2, ensure_ascii=False)}

Voici la liste FERMÉE des agents/actions valides du système. Tu DOIS choisir "agent_ou_action_recommande" UNIQUEMENT parmi cette liste, sans exception :
{", ".join(agents_valides)}

Analyse cet événement et réponds UNIQUEMENT avec un JSON valide, sans aucun texte avant ou après, respectant exactement cette structure :
{{
  "agent_ou_action_recommande": "un choix parmi la liste fermée ci-dessus",
  "niveau_urgence": "info" | "orange" | "rouge" | "critique",
  "justification": "explication concise de la décision",
  "necessite_intervention_humaine": true | false
}}"""

        try:
            response = await self.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            contenu = response.strip()
            if contenu.startswith("```"):
                contenu = contenu.split("```")[1]
                if contenu.startswith("json"):
                    contenu = contenu[4:]
            contenu = contenu.strip()

            result = json.loads(contenu)
            if result.get("agent_ou_action_recommande") not in agents_valides:
                result["agent_ou_action_recommande"] = "aucune_action"
            return result

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            return {
                "type_evenement": type_evenement,
                "agent_ou_action_recommande": "aucune_action",
                "niveau_urgence": "critique",
                "justification": f"Échec de la décision IA ({type(e).__name__}) — intervention humaine requise",
                "necessite_intervention_humaine": True,
            }


llm_client = LLMClient()
