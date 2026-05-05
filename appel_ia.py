import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generer_tour_ia(etat_jeu_complet, actions_joueur, nom_joueur):
    monde = etat_jeu_complet["monde"]
    tour = etat_jeu_complet["tour"]

    # On prépare une consigne ultra-stricte
    prompt_systeme = f"""
Tu es le moteur d'intelligence stratégique de GeoStrat. 
Tour actuel : {tour}. Joueur humain : {nom_joueur}.

ÉTAT DU MONDE (Source de vérité) :
{json.dumps(monde, indent=2, ensure_ascii=False)}

MISSION :
Génère les actions diplomatiques et militaires des IA.

⚠️ PROTOCOLE DE VÉRIFICATION OBLIGATOIRE (AVANT CHAQUE ACTION) :
Pour chaque pays émetteur "A" voulant agir vers une cible "B" :

1. SI l'action est "ALLIANCE" :
   - VÉRIFIE : Est-ce que "B" est déjà dans la liste 'alliances' de "A" ? 
     -> SI OUI : ACTION INTERDITE. Ne génère rien pour ce duo.
   - VÉRIFIE : Est-ce que "B" est dans la liste 'en_guerre_contre' de "A" ?
     -> SI OUI : ACTION INTERDITE (On ne s'allie pas avec un ennemi actif).
   - CAS SPÉCIAL : Si "B" est dans 'alliances_en_attente' de "A", l'action "ALLIANCE" signifie "ACCEPTER la proposition".

2. SI l'action est "ATTAQUE" :
   - VÉRIFIE : Est-ce que "B" est un allié ? 
     -> SI OUI : Tu dois d'abord faire "ROMPRE_ALLIANCE" (ou faire les deux si tu es agressif).

RÈGLES DE SORTIE :
- Ne génère QUE les actions qui changent l'état (pas de doublons, pas de propositions inutiles).
- Format JSON pur uniquement.

Format attendu : 
{{
  "CODE_EMETTEUR": {{
    "CODE_CIBLE": "ACTION"
  }}
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite", 
            contents=prompt_systeme,
            config={'response_mime_type': 'application/json'}
        )

        actions_ia = json.loads(response.text)
        
        # Fusion avec les actions du joueur
        actions_ia[nom_joueur] = actions_joueur 
        
        # --- ON CREE LA STRUCTURE AVEC LES CLES ---
        donnees_finales = {
            "metadata": {
                "tour": tour,
                "nom_joueur": nom_joueur
            },
            "actions": actions_ia
        }
        
        chemin_sauvegarde = os.path.join(os.path.dirname(__file__), "data", "actions_tour.json")
        with open(chemin_sauvegarde, "w", encoding="utf-8") as f:
            # On enregistre 'donnees_finales' et non 'actions_ia' directement
            json.dump(donnees_finales, f, indent=4, ensure_ascii=False)
            
        return True
    except Exception as e:
        print(f"❌ Erreur IA : {e}")
        return False