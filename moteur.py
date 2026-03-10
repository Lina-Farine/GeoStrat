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
            if action == "ATTAQUE":
                if cible not in etat_du_monde[attaquant]["en_guerre_contre"]:
                    etat_du_monde[attaquant]["en_guerre_contre"].append(cible)
                if attaquant not in etat_du_monde[cible]["en_guerre_contre"]:
                    etat_du_monde[cible]["en_guerre_contre"].append(attaquant)
                    print(f"⚔️ GUERRE DÉCLARÉE : {attaquant} attaque {cible} !")
                    
            elif action == "ALLIANCE":
                if cible not in etat_du_monde[attaquant]["alliances"]:
                    etat_du_monde[attaquant]["alliances"].append(cible)
                    print(f"🤝 ALLIANCE CONCLUE : {attaquant} s'allie avec {cible} !")

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
    pays_ia = [p for p in etat_du_monde.keys() if p != nom_joueur]
    
    for pays in pays_ia:
        actions_ia[pays] = {}
        if random.random() < 0.05: # 5% de chance d'attaquer
            cible = random.choice(list(etat_du_monde.keys()))
            if cible != pays:
                actions_ia[pays][cible] = "ATTAQUE"
                
    return actions_ia