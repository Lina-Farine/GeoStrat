import json
import os

def resoudre_tour(etat_du_monde, chemin_actions):
    """
    Lit actions_tour.json et met à jour l'état du monde.
    """
    if not os.path.exists(chemin_actions):
        return etat_du_monde

    with open(chemin_actions, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # IMPORTANT : On ne prend que la partie "actions" pour la boucle
        toutes_les_actions = data.get("actions", {})

    # Initialisation des clés de stockage si absentes
    for pays in etat_du_monde:
        if "alliances_en_attente" not in etat_du_monde[pays]:
            etat_du_monde[pays]["alliances_en_attente"] = []

    # --- ÉTAPE 1 : TRAITEMENT DES RUPTURES ET PAIX (Immédiat) ---
    for emetteur, ordres in toutes_les_actions.items():
        for cible, action in ordres.items():
            if action == "ROMPRE_ALLIANCE":
                if cible in etat_du_monde[emetteur]["alliances"]:
                    etat_du_monde[emetteur]["alliances"].remove(cible)
                if emetteur in etat_du_monde[cible]["alliances"]:
                    etat_du_monde[cible]["alliances"].remove(emetteur)
                print(f"💔 {emetteur} a rompu son alliance avec {cible}.")

            elif action == "PAIX":
                if cible in etat_du_monde[emetteur]["en_guerre_contre"]:
                    etat_du_monde[emetteur]["en_guerre_contre"].remove(cible)
                if emetteur in etat_du_monde[cible]["en_guerre_contre"]:
                    etat_du_monde[cible]["en_guerre_contre"].remove(emetteur)
                print(f"🕊️ Paix signée entre {emetteur} et {cible}.")

    # --- ÉTAPE 2 : TRAITEMENT DES ATTAQUES (Priorité sur l'alliance) ---
    for emetteur, ordres in toutes_les_actions.items():
        for cible, action in ordres.items():
            if action == "ATTAQUE":
                # La guerre annule toute tentative d'alliance
                if emetteur not in etat_du_monde[cible]["en_guerre_contre"]:
                    etat_du_monde[emetteur]["en_guerre_contre"].append(cible)
                    etat_du_monde[cible]["en_guerre_contre"].append(emetteur)
                    # On retire des alliances si existantes
                    if cible in etat_du_monde[emetteur]["alliances"]:
                        etat_du_monde[emetteur]["alliances"].remove(cible)
                        etat_du_monde[cible]["alliances"].remove(emetteur)
                    print(f"⚔️ {emetteur} attaque {cible} !")
                # La guerre annule les accords commerciaux
                for ressource in ["vend_nourriture_a", "achete_nourriture_a", "vend_petrole_a", "achete_petrole_a"]:
                    if emetteur in etat_du_monde[cible][ressource]:
                        etat_du_monde[cible][ressource].remove(emetteur)
                    if cible in etat_du_monde[emetteur][ressource]:
                        etat_du_monde[emetteur][ressource].remove(cible)
                
                print(f"⚔️ {emetteur} attaque {cible} ! Les routes commerciales sont coupées.")

    # --- ÉTAPE 3 : TRAITEMENT DES ALLIANCES (Logique complexe) ---
    for emetteur, ordres in toutes_les_actions.items():
        for cible, action in ordres.items():
            if action == "ALLIANCE":
                # Cas 1 : Déjà en guerre ou déjà allié
                if cible in etat_du_monde[emetteur]["alliances"]:
                    continue # On ignore simplement sans rien afficher

                # Cas 2 : La cible attaque l'émetteur au même tour
                cible_action_vers_emetteur = toutes_les_actions.get(cible, {}).get(emetteur)
                if cible_action_vers_emetteur == "ATTAQUE":
                    print(f"🚫 Alliance échouée : {cible} a choisi d'attaquer {emetteur} !")
                    continue

                # Cas 3 : La cible propose AUSSI une alliance (Création immédiate)
                if cible_action_vers_emetteur == "ALLIANCE":
                    if cible not in etat_du_monde[emetteur]["alliances"]:
                        etat_du_monde[emetteur]["alliances"].append(cible)
                        etat_du_monde[cible]["alliances"].append(emetteur)
                        print(f"🤝 ALLIANCE RÉCIPROQUE : {emetteur} et {cible} s'unissent !")
                
                # Cas 4 : La cible n'a pas réagi (Attente tour n+1)
                else:
                    if emetteur not in etat_du_monde[cible]["alliances_en_attente"]:
                        etat_du_monde[cible]["alliances_en_attente"].append(emetteur)
                        print(f"📩 {emetteur} propose une alliance à {cible} (Réponse au tour suivant).")

    # --- ETAPE 4 : TRAITEMENT DU COMMERCE
    #relou attendre de savoir si autre pays accepte = attendre appel IA

# A MODIF!!!
    # --- ÉTAPE 4 : MISE À JOUR ÉCONOMIQUE ---
    # (Garder ta logique de revenus passifs et malus de guerre ici)
    for pays, data in etat_du_monde.items():
        if len(data["en_guerre_contre"]) > 0:
            data["ressources"]["S"] -= 2
            data["ressources"]["A"] -= 50

    return etat_du_monde