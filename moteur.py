import json
import os

def resoudre_tour(etat_du_monde, chemin_actions, chemin_retours):
    """
    Lit actions_tour.json et met à jour l'état du monde.
    """
    if not os.path.exists(chemin_actions):
        return etat_du_monde

    with open(chemin_actions, 'r', encoding='utf-8') as f:
        data_actions = json.load(f)
        # IMPORTANT : On ne prend que la partie "actions" pour la boucle
        toutes_les_actions = data_actions.get("actions", {})
    
    with open(chemin_retours, 'r', encoding='utf-8') as g:
        data_retours = json.load(g)
        # IMPORTANT : On ne prend que la partie "decisions" pour la boucle
        tous_les_retours = data_retours.get("decisions", {})

    # --- ÉTAPE 1 : TRAITEMENT DES RUPTURES ET PAIX (Immédiat) ---
    for emetteur, ordres in toutes_les_actions.items():
        for cible, action in ordres.items():
            if action == "ROMPRE_ALLIANCE":
                if cible in etat_du_monde[emetteur]["alliances"]:
                    etat_du_monde[emetteur]["alliances"].remove(cible)
                if emetteur in etat_du_monde[cible]["alliances"]:
                    etat_du_monde[cible]["alliances"].remove(emetteur)
                print(f"💔 {emetteur} a rompu son alliance avec {cible}.")

            elif action == "PROPOSE_PAIX":
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
            if action == "PROPOSE_ALLIANCE":
                # Cas 1 : Déjà en guerre ou déjà allié
                if cible in etat_du_monde[emetteur]["alliances"]:
                    continue # On ignore simplement sans rien afficher

                # Cas 2 : La cible attaque l'émetteur au même tour
                cible_action_vers_emetteur = toutes_les_actions.get(cible, {}).get(emetteur)
                if cible_action_vers_emetteur == "ATTAQUE":
                    print(f"🚫 Alliance échouée : {cible} a choisi d'attaquer {emetteur} !")
                    continue

                # Cas 3 : La cible propose AUSSI une alliance (Création immédiate)
                if cible_action_vers_emetteur == "PROPOSE_ALLIANCE":
                    if cible not in etat_du_monde[emetteur]["alliances"]:
                        etat_du_monde[emetteur]["alliances"].append(cible)
                        etat_du_monde[cible]["alliances"].append(emetteur)
                        print(f"🤝 ALLIANCE RÉCIPROQUE : {emetteur} et {cible} s'unissent !")
                
                # Cas 4 : Lire le retour de la cible
                else:
                    retour = tous_les_retours.get(emetteur, {}).get(cible)
                    if retour is None:
                        continue
                    if retour[1] == "REFUSE":
                        print(f"🚫 Alliance échouée : {cible} a refusé l'alliance avec {emetteur} !")
                        continue
                    elif retour[1] == "ACCEPTE":
                        print(f"🚫 Alliance réussie : {cible} a accepté l'alliance avec {emetteur} !")
                        if cible not in etat_du_monde[emetteur]["alliances"]:
                            etat_du_monde[emetteur]["alliances"].append(cible)
                            etat_du_monde[cible]["alliances"].append(emetteur)
                        continue


    # Au début de resoudre_tour(), tu construis un compteur de lots déjà vendus
    lots_vendus = {}  # { "CA": {"petits": 0, "gros": 0}, ... }





    # --- ETAPE 4 : TRAITEMENT DU COMMERCE
    for emetteur, ordres in toutes_les_actions.items():
        for cible, action in ordres.items():
            if action == "PROPOSE_GROS_ACHAT_NOURRITURE":
                retour = tous_les_retours.get(emetteur, {}).get(cible)
                if retour is None:
                    continue
                if retour[1] == "REFUSE":
                    print(f"🚫 Achat échoué : {cible} a refusé de vendre beaucoup de nourriture a {emetteur} !")
                    continue
                
                elif retour[1] == "ACCEPTE":
                    # Initialiser le compteur pour ce vendeur (= la cible qui vend)
                    if cible not in lots_vendus:
                        lots_vendus[cible] = {"petits_N": 0, "gros_N": 0, "petits_P": 0, "gros_P": 0}

                    # Vérifier qu'il reste des lots disponibles
                    dispo = vendeurs_disponibles.get(cible, {})  # vendeurs calculés au début du tour
                    if lots_vendus[cible]["gros_N"] >= dispo.get("lots_gros", 0):
                        print(f"⚠️ {cible} n'a plus de gros lots de nourriture à vendre !")
                        continue

                    print(f"🚫 Achat réussi : {cible} a accepté de vendre beaucoup de nourriture a {emetteur} !")
                    lots_vendus[cible]["gros_N"] += 1
                    etat_du_monde[emetteur]["achete_beaucoup_de_nourriture_a"].append(cible)
                    etat_du_monde[cible]["vend_beaucoup_de_nourriture_a"].append(emetteur)
                    continue


            if action == "PROPOSE_PETIT_ACHAT_NOURRITURE":
                retour = tous_les_retours.get(emetteur, {}).get(cible)
                if retour is None:
                    continue
                if retour[1] == "REFUSE":
                    print(f"🚫 Achat échoué : {cible} a refusé de vendre un peu de nourriture a {emetteur} !")
                    continue
                elif retour[1] == "ACCEPTE":
                    # Initialiser le compteur pour ce vendeur (= la cible qui vend)
                    if cible not in lots_vendus:
                        lots_vendus[cible] = {"petits_N": 0, "gros_N": 0, "petits_P": 0, "gros_P": 0}

                    # Vérifier qu'il reste des lots disponibles
                    dispo = vendeurs_disponibles.get(cible, {})  # vendeurs calculés au début du tour
                    if lots_vendus[cible]["petits_N"] >= dispo.get("lots_petits", 0):
                        print(f"⚠️ {cible} n'a plus de petits lots de nourriture à vendre !")
                        continue
                    print(f"🚫 Achat réussi : {cible} a accepté de vendre un peu de nourriture a {emetteur} !")
                    lots_vendus[cible]["petits_N"] += 1
                    etat_du_monde[emetteur]["achete_un_peu_de_nourriture_a"].append(cible)
                    etat_du_monde[cible]["vend_un_peu_de_nourriture_a"].append(emetteur)
                    continue


            if action == "PROPOSE_GROS_ACHAT_PETROLE":
                retour = tous_les_retours.get(emetteur, {}).get(cible)
                if retour is None:
                    continue
                if retour[1] == "REFUSE":
                    print(f"🚫 Achat échoué : {cible} a refusé de vendre beaucoup de petrole a {emetteur} !")
                    continue
                elif retour[1] == "ACCEPTE":
                    # Initialiser le compteur pour ce vendeur (= la cible qui vend)
                    if cible not in lots_vendus:
                        lots_vendus[cible] = {"petits_N": 0, "gros_N": 0, "petits_P": 0, "gros_P": 0}

                    # Vérifier qu'il reste des lots disponibles
                    dispo = vendeurs_disponibles.get(cible, {})  # vendeurs calculés au début du tour
                    if lots_vendus[cible]["gros_P"] >= dispo.get("lots_gros", 0):
                        print(f"⚠️ {cible} n'a plus de gros lots de pétrole à vendre !")
                        continue
                    print(f"🚫 Achat réussi : {cible} a accepté de vendre beaucoup de petrole a {emetteur} !")
                    lots_vendus[cible]["gros_P"] += 1
                    etat_du_monde[emetteur]["achete_beaucoup_de_petrole_a"].append(cible)
                    etat_du_monde[cible]["vend_beaucoup_de_petrole_a"].append(emetteur)
                    continue


            if action == "PROPOSE_PETIT_ACHAT_PETROLE":
                retour = tous_les_retours.get(emetteur, {}).get(cible)
                if retour is None:
                    continue
                if retour[1] == "REFUSE":
                    print(f"🚫 Achat échoué : {cible} a refusé de vendre un peu de petrole a {emetteur} !")
                    continue
                elif retour[1] == "ACCEPTE":
                    # Initialiser le compteur pour ce vendeur (= la cible qui vend)
                    if cible not in lots_vendus:
                        lots_vendus[cible] = {"petits_N": 0, "gros_N": 0, "petits_P": 0, "gros_P": 0}

                    # Vérifier qu'il reste des lots disponibles
                    dispo = vendeurs_disponibles.get(cible, {})  # vendeurs calculés au début du tour
                    if lots_vendus[cible]["petits_P"] >= dispo.get("lots_gros", 0):
                        print(f"⚠️ {cible} n'a plus de petits lots de pétrole à vendre !")
                        continue
                    print(f"🚫 Achat réussi : {cible} a accepté de vendre un peu de petrole a {emetteur} !")
                    lots_vendus[cible]["petits_P"] += 1
                    etat_du_monde[emetteur]["achete_un_peu_de_petrole_a"].append(cible)
                    etat_du_monde[cible]["vend_un_peu_de_petrole_a"].append(emetteur)
                    continue

 
 
    # --- ÉTAPE 5 : MISE À JOUR ÉCONOMIQUE ---
    for pays, data in etat_du_monde.items():
        res = data["ressources"]
        nb_guerres = len(data["en_guerre_contre"])
        nb_alliances = len(data["alliances"])

        # ── MALUS DE GUERRE ──────────────────────────────────────
        if nb_guerres > 0:
            res["S"] -= 3 * nb_guerres 
            res["A"] -= 80 * nb_guerres
            res["H"] -= 0.3 * nb_guerres
            res["P"] -= 15 * nb_guerres 
            res["N"] -= 500000 * nb_guerres 

        # ── BONUS D'ALLIANCE ─────────────────────────────────────
        if nb_alliances > 0:
            res["S"] += 0.5 * nb_alliances

        # ── COMMERCE NOURRITURE ──────────────────────────────────
        # Vendeur : gagne de l'argent, perd de la nourriture
        nb_gros_ventes_N = len(data["vend_beaucoup_de_nourriture_a"])
        nb_petit_ventes_N = len(data["vend_un_peu_de_nourriture_a"])
        res["A"] += 60 * nb_gros_ventes_N
        res["N"] -= 600000 * nb_gros_ventes_N
        res["A"] += 25 * nb_petit_ventes_N
        res["N"] -= 200000 * nb_petit_ventes_N

        # Acheteur : perd de l'argent, gagne de la nourriture
        nb_gros_achats_N = len(data["achete_beaucoup_de_nourriture_a"])
        nb_petit_achats_N = len(data["achete_un_peu_de_nourriture_a"])
        res["A"] -= 60 * nb_gros_achats_N
        res["N"] += 600000 * nb_gros_achats_N
        res["A"] -= 25 * nb_petit_achats_N
        res["N"] += 200000 * nb_petit_achats_N

        # ── COMMERCE PÉTROLE ─────────────────────────────────────
        # Vendeur : gagne de l'argent, perd du pétrole
        nb_gros_ventes_P = len(data["vend_beaucoup_de_petrole_a"])
        nb_petit_ventes_P = len(data["vend_un_peu_de_petrole_a"])
        res["A"] += 100 * nb_gros_ventes_P
        res["P"] -= 400 * nb_gros_ventes_P
        res["A"] += 30 * nb_petit_ventes_P
        res["P"] -= 100 * nb_petit_ventes_P

        # Acheteur : perd de l'argent, gagne du pétrole
        nb_gros_achats_P = len(data["achete_beaucoup_de_petrole_a"])
        nb_petit_achats_P = len(data["achete_un_peu_de_petrole_a"])
        res["A"] -= 100 * nb_gros_achats_P
        res["P"] += 400 * nb_gros_achats_P
        res["A"] -= 30 * nb_petit_achats_P
        res["P"] += 100 * nb_petit_achats_P

        # ── CONSÉQUENCES DES PÉNURIES ────────────────────────────
        if res["N"] < 0: #penurie nourriture
            res["N"] = 0
            res["S"] -= 5
            res["H"] -= 1

        if res["P"] < 0: #penurie energie
            res["P"] = 0
            res["S"] -= 3
            res["A"] -= 20

        if res["A"] < 0: #crise economique
            res["S"] -= 2

        # ── SÉCURITÉ ─────────────────────────────────────────────
        res["S"] = max(0, min(100, res["S"]))
        res["H"] = max(0.01, res["H"])

    return etat_du_monde