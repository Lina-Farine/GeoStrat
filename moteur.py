import random

def resoudre_tour(actions_joueur, etat_du_monde, nom_joueur):
    """
    Prend l'état actuel du monde, calcule les conséquences des actions,
    et renvoie le nouvel état du monde mis à jour.
    """
    
    # ÉTAPE 1 : Appel à l'IA
    actions_ia = simulation_appel_ia(etat_du_monde, nom_joueur)
    
    # Fusion des actions
    toutes_les_actions = {nom_joueur: actions_joueur}
    toutes_les_actions.update(actions_ia)

    # ÉTAPE 2 : Diplomatie et Guerres
    for attaquant, ordres in toutes_les_actions.items():
        for cible, action in ordres.items():
            
            # Si A veut s'allier à B, mais B attaque A
            if action == "ALLIANCE" and toutes_les_actions.get(cible, {}).get(attaquant) == "ATTAQUE":
                print(f"🚫 L'alliance entre {attaquant} et {cible} a échoué : la guerre a éclaté !")
                del ordres[cible] # On annule la demande d'alliance

            if action == "ATTAQUE":
                if cible not in etat_du_monde[attaquant]["en_guerre_contre"]:
                    etat_du_monde[attaquant]["en_guerre_contre"].append(cible)
                if attaquant not in etat_du_monde[cible]["en_guerre_contre"]:
                    etat_du_monde[cible]["en_guerre_contre"].append(attaquant)
                    print(f"⚔️ GUERRE DÉCLARÉE : {attaquant} attaque {cible} !")
                    
            elif action == "ALLIANCE":
                if cible not in etat_du_monde[attaquant]["alliances"]:
                    etat_du_monde[attaquant]["alliances"].append(cible)
                    # L'alliance est réciproque
                    if attaquant not in etat_du_monde[cible]["alliances"]:
                        etat_du_monde[cible]["alliances"].append(attaquant)
                    print(f"🤝 ALLIANCE CONCLUE : {attaquant} s'allie avec {cible} !")

            # --- NOUVELLES ACTIONS CI-DESSOUS ---
            elif action == "ROMPRE_ALLIANCE":
                if cible in etat_du_monde[attaquant]["alliances"]:
                    etat_du_monde[attaquant]["alliances"].remove(cible)
                if attaquant in etat_du_monde[cible]["alliances"]:
                    etat_du_monde[cible]["alliances"].remove(attaquant)
                print(f"💔 ALLIANCE ROMPUE : {attaquant} trahit {cible} !")

            elif action == "PAIX":
                # Dans un jeu simple, la paix proposée est automatiquement acceptée
                if cible in etat_du_monde[attaquant]["en_guerre_contre"]:
                    etat_du_monde[attaquant]["en_guerre_contre"].remove(cible)
                if attaquant in etat_du_monde[cible]["en_guerre_contre"]:
                    etat_du_monde[cible]["en_guerre_contre"].remove(attaquant)
                print(f"🕊️ PAIX SIGNÉE : Fin du conflit entre {attaquant} et {cible}.")

    # ÉTAPE 3 : Calcul Mensuel des Ressources
    for pays, data in etat_du_monde.items():
        stats = data["ressources"]
        
        # Revenu passif (10% de l'argent divisé par 12 mois)
        revenu_argent = int((stats["A"] * 0.10) / 12) 
        stats["A"] += revenu_argent
        
        # Modificateurs de Guerre
        if len(data["en_guerre_contre"]) > 0:
            stats["H"] -= 0.5 
            stats["S"] -= 2    
            stats["A"] -= 50   
            
            if stats["S"] < 0: stats["S"] = 0
            if stats["H"] < 1: stats["H"] = 1

    # On renvoie le monde mis à jour au main.py !
    return etat_du_monde

def simulation_appel_ia(etat_du_monde, nom_joueur):
    actions_ia = {}
    tous_pays = list(etat_du_monde.keys())
    
    for pays in tous_pays:
        if pays == nom_joueur: continue
        
        actions_ia[pays] = {}
        data = etat_du_monde[pays]
        
        # L'IA regarde ses voisins/ennemis
        for cible in tous_pays:
            if cible == pays: continue
            
            est_allie = cible in data["alliances"]
            est_en_guerre = cible in data["en_guerre_contre"]
            
            # --- RÈGLE 1 : Si en guerre, peut-elle demander la paix ? ---
            if est_en_guerre:
                # Si sa satisfaction est basse, elle demande la paix
                if data["ressources"]["S"] < 40 and random.random() < 0.3:
                    actions_ia[pays][cible] = "PAIX"
            
            # --- RÈGLE 2 : Si pas allié et pas en guerre, peut-elle attaquer ? ---
            elif not est_allie and not est_en_guerre:
                # 2% de chance de déclarer une guerre au hasard
                if random.random() < 0.02:
                    actions_ia[pays][cible] = "ATTAQUE"
                # 5% de chance de proposer une alliance
                elif random.random() < 0.05:
                    actions_ia[pays][cible] = "ALLIANCE"
            
            # --- RÈGLE 3 : Peut-elle rompre une alliance ? ---
            elif est_allie:
                # Si elle n'a plus d'argent, elle peut rompre l'alliance (coûteux)
                if data["ressources"]["A"] < 0 and random.random() < 0.01:
                    actions_ia[pays][cible] = "ROMPRE_ALLIANCE"
                    
    return actions_ia