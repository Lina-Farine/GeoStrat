import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

COMMERCE_CONFIG = {
    "nourriture": {
        "taille_petit_lot": 200000,
        "taille_gros_lot": 600000,
        "prix_petit_lot": 25,
        "prix_gros_lot": 60,
        "ratio_gros_petit": 3,
        "seuil_surplus_petit": 1.2,  # doit avoir 20% de plus que sa conso
        "seuil_surplus_gros": 1.5,
        "consommation_par_habitant": 0.1,
    },
    "petrole": {
        "taille_petit_lot": 100,
        "taille_gros_lot": 400,
        "prix_petit_lot": 30,
        "prix_gros_lot": 100,
        "ratio_gros_petit": 4,
        "seuil_surplus_petit": 1.3,
        "seuil_surplus_gros": 2.0,
        "consommation_par_habitant": 0.05,
    }
}



def formater_marche_pour_ia(vendeurs_disponibles):
    lignes = ["MARCHÉ MONDIAL - OFFRES DISPONIBLES CE TOUR :"]
    cfg_N = COMMERCE_CONFIG["nourriture"]
    cfg_P = COMMERCE_CONFIG["petrole"]

    if vendeurs_disponibles["nourriture"]:
        lignes.append("\n  NOURRITURE :")
        for pays, offre in vendeurs_disponibles["nourriture"].items():
            lignes.append(
                f"  - {pays} : jusqu'à {offre['lots_petits']} petit(s) lot(s) "
                f"({cfg_N['taille_petit_lot']:,} tonnes, coût {cfg_N['prix_petit_lot']} Mrd$) "
                f"OU jusqu'à {offre['lots_gros']} gros lot(s) "
                f"({cfg_N['taille_gros_lot']:,} tonnes, coût {cfg_N['prix_gros_lot']} Mrd$). "
                f"Total disponible : {offre['total_unites']} petits lots équivalents."
            )
    else:
        lignes.append("\n  NOURRITURE : aucun vendeur disponible ce tour.")

    if vendeurs_disponibles["petrole"]:
        lignes.append("\n  PÉTROLE :")
        for pays, offre in vendeurs_disponibles["petrole"].items():
            lignes.append(
                f"  - {pays} : jusqu'à {offre['lots_petits']} petit(s) lot(s) "
                f"({cfg_P['taille_petit_lot']:,} k barils, coût {cfg_P['prix_petit_lot']} Mrd$) "
                f"OU jusqu'à {offre['lots_gros']} gros lot(s) "
                f"({cfg_P['taille_gros_lot']:,} k barils, coût {cfg_P['prix_gros_lot']} Mrd$). "
                f"Total disponible : {offre['total_unites']} petits lots équivalents."
            )
    else:
        lignes.append("\n  PÉTROLE : aucun vendeur disponible ce tour.")

    return "\n".join(lignes)


def generer_tour_ia(etat_jeu_complet, actions_joueur, nom_joueur, vendeurs_disponibles):
    monde = etat_jeu_complet["monde"]
    tour = etat_jeu_complet["tour"]
    marche_formate = formater_marche_pour_ia(vendeurs_disponibles)

    prompt_systeme = f"""
Tu es le moteur d'intelligence stratégique de GeoStrat.
Tour actuel : {tour}. Joueur humain : {nom_joueur}.

ÉTAT DU MONDE :
{json.dumps(monde, indent=2, ensure_ascii=False)}

{marche_formate}

RÈGLES D'ACHAT STRICTES :
1. Tu ne peux proposer d'acheter QU'À des pays présents dans la liste ci-dessus.
2. Pour la nourriture : 1 gros lot = {COMMERCE_CONFIG['nourriture']['ratio_gros_petit']} petits lots dans le total disponible du vendeur.
3. Pour le pétrole : 1 gros lot = {COMMERCE_CONFIG['petrole']['ratio_gros_petit']} petits lots dans le total disponible du vendeur.
4. Vérifie que l'acheteur a assez d'argent (ressource "A") pour payer.
   - Petit lot nourriture : {COMMERCE_CONFIG['nourriture']['prix_petit_lot']} Mrd$
   - Gros lot nourriture  : {COMMERCE_CONFIG['nourriture']['prix_gros_lot']} Mrd$
   - Petit lot pétrole    : {COMMERCE_CONFIG['petrole']['prix_petit_lot']} Mrd$
   - Gros lot pétrole     : {COMMERCE_CONFIG['petrole']['prix_gros_lot']} Mrd$

MISSION :
Génère les actions diplomatiques, militaires et commerciales des pays IA (tout sauf {nom_joueur}).

VALEURS AUTORISÉES pour "ACTION" :
- "ATTAQUE"
- "PROPOSE_ALLIANCE"
- "ROMPRE_ALLIANCE"
- "PROPOSE_PAIX"
- "PROPOSE_GROS_ACHAT_NOURRITURE"
- "PROPOSE_PETIT_ACHAT_NOURRITURE"
- "PROPOSE_GROS_ACHAT_PETROLE"
- "PROPOSE_PETIT_ACHAT_PETROLE"
⚠️ Toute autre valeur est INTERDITE.

PROTOCOLE DE VÉRIFICATION OBLIGATOIRE (AVANT CHAQUE ACTION) :
1. ALLIANCE :
   - INTERDIT si "B" est déjà dans 'alliances' de "A".
   - INTERDIT si "B" est dans 'en_guerre_contre' de "A".
2. ATTAQUE :
   - Si "B" est un allié, faire d'abord "ROMPRE_ALLIANCE".
3. ACHAT :
   - INTERDIT si le vendeur n'est pas dans le marché ci-dessus.
   - INTERDIT si le vendeur n'a plus assez de lots disponibles.
   - INTERDIT si l'acheteur n'a pas assez d'argent.
   - INTERDIT si le vendeur est dans 'en_guerre_contre' de l'acheteur

RÈGLES DE SORTIE :
- Ne génère QUE les actions qui changent l'état.
- Format JSON pur uniquement.

FORMAT ATTENDU :
{{
  "CODE_EMETTEUR": {{
    "CODE_CIBLE": "ACTION"
  }}
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_systeme,
            config={'response_mime_type': 'application/json'}
        )

        actions_ia = json.loads(response.text)
        actions_ia[nom_joueur] = actions_joueur

        donnees_finales = {
            "metadata": {"tour": tour, "nom_joueur": nom_joueur},
            "actions": actions_ia
        }

        chemin_sauvegarde = os.path.join(os.path.dirname(__file__), "data", "actions_tour.json")
        with open(chemin_sauvegarde, "w", encoding="utf-8") as f:
            json.dump(donnees_finales, f, indent=4, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"❌ Erreur IA : {e}")
        return False


def traitement_propositions_ia(etat_jeu_complet, propositions_du_tour, vendeurs_disponibles):
    monde = etat_jeu_complet["monde"]
    tour = etat_jeu_complet["tour"]
    marche_formate = formater_marche_pour_ia(vendeurs_disponibles)

    prompt_systeme = f"""
Tu es le module de décision diplomatique et commerciale de GeoStrat.
Tour actuel : {tour}.

ÉTAT DU MONDE ACTUEL :
{json.dumps(monde, indent=2, ensure_ascii=False)}

{marche_formate}

PRIX DES LOTS (pour évaluer si l'acheteur peut payer) :
- Petit lot nourriture : {COMMERCE_CONFIG['nourriture']['prix_petit_lot']} Mrd$  ({COMMERCE_CONFIG['nourriture']['taille_petit_lot']:,} tonnes)
- Gros lot nourriture  : {COMMERCE_CONFIG['nourriture']['prix_gros_lot']} Mrd$  ({COMMERCE_CONFIG['nourriture']['taille_gros_lot']:,} tonnes)
- Petit lot pétrole    : {COMMERCE_CONFIG['petrole']['prix_petit_lot']} Mrd$  ({COMMERCE_CONFIG['petrole']['taille_petit_lot']:,} k barils)
- Gros lot pétrole     : {COMMERCE_CONFIG['petrole']['prix_gros_lot']} Mrd$  ({COMMERCE_CONFIG['petrole']['taille_gros_lot']:,} k barils)

LES PROPOSITIONS À TRAITER CE TOUR :
{json.dumps(propositions_du_tour, indent=2, ensure_ascii=False)}

MISSION :
Pour chaque proposition, mets-toi à la place du pays CIBLE et décide d'ACCEPTER ou REFUSER.

CRITÈRES DE DÉCISION :
1. PROPOSE_ALLIANCE : Accepte si pas en guerre avec l'émetteur et intérêt stratégique.
2. PROPOSE_PAIX : Accepte si en position de faiblesse, refuse si en position de force.
3. PROPOSE_GROS/PETIT_ACHAT_NOURRITURE : 
   - Accepte si tu as le surplus disponible dans le marché ci-dessus.
   - Refuse si tu n'as plus de lots disponibles (quelqu'un d'autre a déjà tout acheté).
   - Refuse si l'acheteur semble insolvable (ressource "A" insuffisante).
4. PROPOSE_GROS/PETIT_ACHAT_PETROLE : même logique que nourriture.

FORMAT ATTENDU (JSON pur uniquement) :
{{
  "CODE_EMETTEUR": {{
    "CODE_CIBLE": ["ACTION", "ACCEPTE" ou "REFUSE"]
  }}
}}

⚠️ RÈGLE ABSOLUE : JSON strict, aucun texte avant ou après.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_systeme,
            config={'response_mime_type': 'application/json'}
        )

        decisions_ia = json.loads(response.text)
        if isinstance(decisions_ia, list):
            decisions_ia = {k: v for d in decisions_ia for k, v in d.items()}

        resultats_final = {
            "metadata": {"tour": tour, "type": "resolutions_diplomatiques"},
            "decisions": decisions_ia
        }

        chemin_sauvegarde = os.path.join(os.path.dirname(__file__), "data", "retours_propositions.json")
        with open(chemin_sauvegarde, "w", encoding="utf-8") as f:
            json.dump(resultats_final, f, indent=4, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"❌ Erreur IA lors de l'arbitrage : {e}")
        return False