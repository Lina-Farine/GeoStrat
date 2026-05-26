from numpy.compat import asstr
import pygame
import sys
import json
import os

from engine import GameEngine
from moteur import resoudre_tour
from appel_ia import generer_tour_ia
from appel_ia import traitement_propositions_ia


moteur = GameEngine()
# On essaie de charger une partie existante au lancement
etat_actuel = moteur.charger_sauvegarde()

# --- INITIALISATION ---
pygame.init()
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GEOPOLY 2026 - Farine/Miroudot")

font_titre = pygame.font.SysFont("Arial", 30, bold=True)
font_texte = pygame.font.SysFont("Arial", 22)

# --- FONCTIONS UTILES ---
def rgb_to_hex(rgb):
    return '#{:02X}{:02X}{:02X}'.format(rgb[0], rgb[1], rgb[2])

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def creer_calque_couleur(target_hex, couleur_rgba):
    """Crée une surface de la couleur voulue (RGBA) sur la forme du pays."""
    target_rgb = hex_to_rgb(target_hex)
    masque = pygame.mask.from_threshold(MAP_COULEURS, target_rgb, (1, 1, 1, 255))
    calque = masque.to_surface(setcolor=couleur_rgba, unsetcolor=(0, 0, 0, 0))
    return calque

def maj_calques_diplomatie():
    """Génère les calques verts (alliés) et rouges (ennemis) pour le joueur."""
    calques = []
    if not moteur.etat_jeu or not pays_joueur:
        return calques
        
    monde = moteur.etat_jeu["monde"]
    
    # 1. Calques Verts (Alliés)
    for allie_code in monde[pays_joueur]["alliances"]:
        # Trouver l'Hexa correspondant au code pays
        hexa = next((h for h, c in MAP_HEX_TO_CODE.items() if c == allie_code), None)
        if hexa:
            calques.append(creer_calque_couleur(hexa, (0, 200, 0, 150))) # Vert
            
    # 2. Calques Rouges (Ennemis)
    for ennemi_code in monde[pays_joueur]["en_guerre_contre"]:
        hexa = next((h for h, c in MAP_HEX_TO_CODE.items() if c == ennemi_code), None)
        if hexa:
            calques.append(creer_calque_couleur(hexa, (200, 0, 0, 150))) # Rouge
            
    return calques

def dessiner_top_bar():
    """Affiche les ressources du joueur en haut de l'écran avec des icônes PNG."""
    if phase_de_jeu not in ("JOUER", "COMMERCE"): return
    
    stats = moteur.etat_jeu["monde"][pays_joueur]["ressources"]
    
    # Barre de fond
    rect_bar = pygame.Rect(0, 0, WIDTH, 45)
    pygame.draw.rect(screen, (30, 30, 30), rect_bar)
    pygame.draw.line(screen, (100, 100, 100), (0, 45), (WIDTH, 45), 2)
    
    # Chargement et redimensionnement
    icon_pop = pygame.image.load("assets/images/Population.png").convert_alpha()
    icon_pop = pygame.transform.smoothscale(icon_pop, (25, 25))

    icon_food = pygame.image.load("assets/images/Nourriture.png").convert_alpha()
    icon_food = pygame.transform.smoothscale(icon_food, (25, 25))

    icon_oil = pygame.image.load("assets/images/Pétrole.png").convert_alpha()
    icon_oil = pygame.transform.smoothscale(icon_oil, (25, 25))

    icon_money = pygame.image.load("assets/images/Argent.png").convert_alpha()
    icon_money = pygame.transform.smoothscale(icon_money, (25, 25))

    icon_sat = pygame.image.load("assets/images/Satisfaction.png").convert_alpha()
    icon_sat = pygame.transform.smoothscale(icon_sat, (25, 25))

    # On associe chaque icône à sa valeur textuelle
    ressources_a_afficher = [
        (icon_pop, f"{int(stats['H'])}M"),
        (icon_food, f"{int(stats['N'])}t"),
        (icon_oil, f"{int(stats['P'])}k"),
        (icon_money, f"{int(stats['A'])}$"),
        (icon_sat, f"{int(stats['S'])}%")
    ]
    
    x_offset = 30 # Point de départ à gauche
    espacement = WIDTH / len(ressources_a_afficher) # Répartition équitable
    
    for icone, texte in ressources_a_afficher:
        # 1. On dessine l'icône PNG
        screen.blit(icone, (x_offset, 10))
        
        # 2. On dessine le texte juste à droite de l'icône (+35 pixels)
        surf_texte = font_titre.render(texte, True, (255, 255, 255))
        screen.blit(surf_texte, (x_offset + 35, 8))
        
        # On décale pour la ressource suivante
        x_offset += espacement

def dessiner_legende():
    """Dessine un bloc propre en bas à gauche pour expliquer les couleurs."""
    if phase_de_jeu != "JOUER": return
    
    # Dimensions de la boîte (agrandies)
    box_width = 200
    box_height = 140
    base_x = 20
    base_y = HEIGHT - box_height - 20 # S'adapte pour laisser 20px de marge en bas
    
    # Boîte de fond
    rect_legende = pygame.Rect(base_x, base_y, box_width, box_height)
    pygame.draw.rect(screen, (40, 40, 40), rect_legende, border_radius=8)
    pygame.draw.rect(screen, (100, 100, 100), rect_legende, 2, border_radius=8)
    
    screen.blit(font_texte.render("Légende :", True, (255, 255, 255)), (base_x + 15, base_y + 10))
    
    # Bleu = Vous
    pygame.draw.rect(screen, (0, 100, 255), (base_x + 15, base_y + 45, 20, 20))
    screen.blit(font_texte.render("Votre Pays", True, (200, 200, 200)), (base_x + 45, base_y + 43))
    
    # Vert = Allié
    pygame.draw.rect(screen, (0, 200, 0), (base_x + 15, base_y + 75, 20, 20))
    screen.blit(font_texte.render("Alliés", True, (200, 200, 200)), (base_x + 45, base_y + 73))
    
    # Rouge = Ennemi
    pygame.draw.rect(screen, (200, 0, 0), (base_x + 15, base_y + 105, 20, 20))
    screen.blit(font_texte.render("En Guerre", True, (200, 200, 200)), (base_x + 45, base_y + 103))

def dessiner_dashboard(code_pays, clic_x):
    """Dessine le panneau latéral gris du côté opposé au clic."""
    nom_pays = CODES_TO_NAMES.get(code_pays, code_pays) 
    stats = STATS_PAYS.get(code_pays, {"H": "?", "N": "?", "P": "?", "A": "?", "S": "?"})
    
    # --- LOGIQUE DE POSITIONNEMENT ---
    # Si le clic est à gauche (< 640), le panneau va à droite (X=850)
    # Si le clic est à droite (>= 640), le panneau va à gauche (X=30)
    if clic_x < WIDTH / 2:
        panel_x = 850
    else:
        panel_x = 30
        
    panel_y = 100 # La hauteur reste la même
    
    # Fond du panneau
    rect_panel = pygame.Rect(panel_x, panel_y, 400, 500)
    pygame.draw.rect(screen, (100, 100, 100), rect_panel, border_radius=10)
    pygame.draw.rect(screen, (50, 50, 50), rect_panel, 3, border_radius=10)
    
    # Bouton Fermer (X)
    rect_fermer = pygame.Rect(panel_x + 350, panel_y + 10, 40, 40)
    pygame.draw.rect(screen, (200, 50, 50), rect_fermer, border_radius=5)
    screen.blit(font_titre.render("X", True, (255, 255, 255)), (panel_x + 360, panel_y + 12))
    
    # Titre (Nom du pays)
    screen.blit(font_titre.render(nom_pays, True, (0, 0, 0)), (panel_x + 30, panel_y + 30))
    pygame.draw.line(screen, (50, 50, 50), (panel_x + 30, panel_y + 70), (panel_x + 350, panel_y + 70), 2)
    
    # Affichage des Statistiques
    y_texte = panel_y + 100
    textes_stats = [
        f"Population (H) : {stats['H']} Millions",
        f"Nourriture (N) : {stats['N']} Tonnes",
        f"Pétrole (P) : {stats['P']}k Barils",
        f"Argent (A) : {stats['A']} Milliards $",
        f"Satisfaction (S) : {stats['S']} %"
    ]
    
    for texte in textes_stats:
        screen.blit(font_texte.render(texte, True, (0, 0, 0)), (panel_x + 30, y_texte))
        y_texte += 45
        
    # Bouton "Sélectionner / Jouer ce pays"
    rect_jouer = pygame.Rect(panel_x + 50, panel_y + 400, 300, 60)
    pygame.draw.rect(screen, (60, 120, 60), rect_jouer, border_radius=8)
    titre_btn = font_titre.render("JOUER CE PAYS", True, (255, 255, 255))
    screen.blit(titre_btn, (panel_x + 95, panel_y + 410))
    
    return rect_fermer, rect_jouer

# --- BOUTONS DE LA BARRE D'ACTION (bas droite) ---
rect_fin_tour   = pygame.Rect(WIDTH - 250, HEIGHT - 80,  230, 60)
rect_btn_commerce = pygame.Rect(WIDTH - 500, HEIGHT - 80,  230, 60)

# Config commerce (miroir de moteur.py pour l'affichage)
COMMERCE_CONFIG_UI = {
    "nourriture": {
        "taille_petit_lot": 200_000, "taille_gros_lot": 600_000,
        "prix_petit_lot": 25,        "prix_gros_lot": 60,
        "unite": "t",
    },
    "petrole": {
        "taille_petit_lot": 100,     "taille_gros_lot": 400,
        "prix_petit_lot": 30,        "prix_gros_lot": 100,
        "unite": "k bar.",
    },
}


def dessiner_ecran_commerce(vendeurs, actions_joueur, argent_joueur):
    """
    Panneau marché mondial plein écran (top bar reste visible).
    Retourne un dict de boutons cliquables :
      boutons = { (vendeur, ressource, taille): pygame.Rect }
    et btn_fermer.
    """
    # Overlay sombre sous la top bar (y=50)
    overlay = pygame.Surface((WIDTH, HEIGHT - 50), pygame.SRCALPHA)
    overlay.fill((10, 10, 20, 210))
    screen.blit(overlay, (0, 50))

    # Panneau principal
    PX, PY, PW, PH = 40, 60, WIDTH - 80, HEIGHT - 80
    pygame.draw.rect(screen, (20, 22, 40), (PX, PY, PW, PH), border_radius=14)
    pygame.draw.rect(screen, (80, 90, 160), (PX, PY, PW, PH), 2, border_radius=14)

    # Titre
    titre = font_titre.render("COMMERCE", True, (255, 230, 100))
    screen.blit(titre, (PX + PW//2 - titre.get_width()//2, PY + 12))

    # Bouton Fermer
    btn_fermer = pygame.Rect(PX + PW - 50, PY + 8, 40, 34)
    pygame.draw.rect(screen, (180, 50, 50), btn_fermer, border_radius=6)
    screen.blit(font_titre.render("X", True, (255,255,255)), (btn_fermer.x + 8, btn_fermer.y + 2))

    # Ligne de séparation sous le titre
    pygame.draw.line(screen, (80,90,160), (PX + 20, PY + 52), (PX + PW - 20, PY + 52), 1)

    boutons = {}  # { (vendeur, ressource, taille): pygame.Rect }

    # ── On dessine deux colonnes : gauche = Nourriture, droite = Pétrole ──
    col_configs = [
        ("nourriture", "NOURRITURE", PX + 20, (40,120,60)),
        ("petrole", "PÉTROLE", PX + PW//2 + 10, (60,80,160)),
    ]

    font_sm = pygame.font.SysFont("Arial", 17)

    for ressource, label_col, col_x, couleur_base in col_configs:
        col_w = PW // 2 - 30
        cfg = COMMERCE_CONFIG_UI[ressource]

        # En-tête colonne
        surf_col = font_titre.render(label_col, True, (200, 220, 255))
        screen.blit(surf_col, (col_x, PY + 60))

        # Sous-titre : besoins du joueur
        monde = moteur.etat_jeu["monde"]
        res_joueur = monde[pays_joueur]["ressources"]
        conso_j = res_joueur["H"] * (0.1 if ressource == "nourriture" else 0.05)
        stock_j = res_joueur["N"] if ressource == "nourriture" else res_joueur["P"]
        manque_j = max(0, conso_j - stock_j)
        unite = cfg["unite"]
        couleur_besoin = (255, 120, 80) if manque_j > 0 else (120, 200, 120)
        surf_besoin = font_sm.render(f"Votre stock : {int(stock_j):,} {unite}  |  Conso estimée : {int(conso_j):,} {unite}", True, couleur_besoin
        )
        screen.blit(surf_besoin, (col_x, PY + 88))

        vendeurs_col = vendeurs.get(ressource, {})
        if not vendeurs_col:
            screen.blit(font_sm.render("Aucun vendeur disponible.", True, (150, 150, 150)), (col_x, PY + 115))
            continue

        y = PY + 115
        for vendeur, offre in vendeurs_col.items():
            if vendeur == pays_joueur:
                continue  # On ne s'achète pas à soi-même
            nom_v = CODES_TO_NAMES.get(vendeur, vendeur)

            # En guerre → on saute
            if vendeur in monde[pays_joueur]["en_guerre_contre"]:
                continue

            # Ligne vendeur
            surf_v = font_texte.render(f"  {nom_v}", True, (230, 230, 230))
            screen.blit(surf_v, (col_x, y))
            y += 26

            # ── Gros lot ──
            if offre["lots_gros"] > 0:
                prix_g = cfg["prix_gros_lot"]
                qte_g = cfg["taille_gros_lot"]
                peut_g = argent_joueur >= prix_g
                deja_g = actions_joueur.get(vendeur) == f"PROPOSE_GROS_ACHAT_{ressource.upper()}"

                if deja_g:
                    coul_g = (30, 160, 30)
                elif peut_g:
                    coul_g = couleur_base
                else:
                    coul_g = (60, 60, 60)

                btn_g = pygame.Rect(col_x + 10, y, col_w - 20, 30)
                pygame.draw.rect(screen, coul_g, btn_g, border_radius=5)

                label_g = (f"✔ Gros lot : {qte_g:,} {unite}  ({prix_g} Mrd$)"
                           if deja_g else
                           f"Gros lot : {qte_g:,} {unite}  ({prix_g} Mrd$)"
                           if peut_g else
                           f"Gros lot : {qte_g:,} {unite}  ({prix_g} Mrd$)  ✘ insolvable")
                couleur_txt_g = (255, 255, 255) if peut_g or deja_g else (140, 140, 140)
                screen.blit(font_sm.render(label_g, True, couleur_txt_g), (btn_g.x + 8, btn_g.y + 6))

                if peut_g:
                    boutons[(vendeur, ressource, "gros")] = btn_g
                y += 36

            # ── Petit lot ──
            if offre["lots_petits"] > 0:
                prix_p = cfg["prix_petit_lot"]
                qte_p = cfg["taille_petit_lot"]
                peut_p = argent_joueur >= prix_p
                deja_p = actions_joueur.get(vendeur) == f"PROPOSE_PETIT_ACHAT_{ressource.upper()}"

                if deja_p:
                    coul_p = (30, 160, 30)
                elif peut_p:
                    coul_p = tuple(min(255, c + 40) for c in couleur_base)
                else:
                    coul_p = (60, 60, 60)

                btn_p = pygame.Rect(col_x + 10, y, col_w - 20, 30)
                pygame.draw.rect(screen, coul_p, btn_p, border_radius=5)

                label_p = (f" Petit lot : {qte_p:,} {unite}  ({prix_p} Mrd$)"
                           if deja_p else f"Petit lot : {qte_p:,} {unite}  ({prix_p} Mrd$)"
                           if peut_p else f"Petit lot : {qte_p:,} {unite}  ({prix_p} Mrd$) insolvable")
                couleur_txt_p = (255, 255, 255) if peut_p or deja_p else (140, 140, 140)
                screen.blit(font_sm.render(label_p, True, couleur_txt_p), (btn_p.x + 8, btn_p.y + 6))

                if peut_p:
                    boutons[(vendeur, ressource, "petit")] = btn_p
                y += 36

            y += 6  # Espacement entre vendeurs

            # Sécurité : ne pas déborder du panneau
            if y > PY + PH - 40:
                screen.blit(font_sm.render("...", True, (150, 150, 150)), (col_x, y))
                break

    return boutons, btn_fermer


def dessiner_ecran_propositions(propositions, reponses, codes):
    """Affiche la liste des propositions reçues avec boutons ACCEPTER/REFUSER."""

    # Fond semi-transparent
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    # Panneau central
    panel_w, panel_h = 700, 500
    panel_x = WIDTH//2 - panel_w//2
    panel_y = HEIGHT//2 - panel_h//2
    pygame.draw.rect(screen, (30, 30, 50), (panel_x, panel_y, panel_w, panel_h), border_radius=12)
    pygame.draw.rect(screen, (100, 100, 150), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=12)
    
    # Titre
    titre = font_titre.render("📬 PROPOSITIONS REÇUES CE TOUR", True, (255, 255, 255))
    screen.blit(titre, (panel_x + panel_w//2 - titre.get_width()//2, panel_y + 20))
    pygame.draw.line(screen, (100, 100, 150), (panel_x + 20, panel_y + 60), (panel_x + panel_w - 20, panel_y + 60), 1)

    # Message si aucune proposition
    if not propositions:
        msg = font_texte.render("Aucune proposition de ce type ce tour-ci.", True, (180, 180, 180))
        screen.blit(msg, (panel_x + panel_w // 2 - msg.get_width() // 2, panel_y + 200))
        # Bouton CONTINUER directement actif
        btn_confirm = pygame.Rect(panel_x + panel_w // 2 - 100, panel_y + panel_h - 60, 200, 45)
        pygame.draw.rect(screen, (200, 150, 0), btn_confirm, border_radius=8)
        screen.blit(font_titre.render("CONTINUER", True, (0, 0, 0)), (btn_confirm.x + 20, btn_confirm.y + 10))
        return {}, btn_confirm, True

    icones = {
        "PROPOSE_ALLIANCE": "ALLIANCE",
        "PROPOSE_PAIX": "PAIX",
        "PROPOSE_GROS_ACHAT_NOURRITURE": "Nourriture (gros lot)",
        "PROPOSE_PETIT_ACHAT_NOURRITURE": "Nourriture (petit lot)",
        "PROPOSE_GROS_ACHAT_PETROLE": "Pétrole (gros lot)",
        "PROPOSE_PETIT_ACHAT_PETROLE": "Pétrole (petit lot)",
    }
    
    btns = {} # { emetteur: (rect_accepter, rect_refuser) }
    y = panel_y + 80

    for emetteur, action in propositions.items():
        nom = codes.get(emetteur, emetteur)
        label_action = icones.get(action, action)

        # Texte de la proposition
        texte = font_texte.render(f"{nom}  →  {label_action}", True, (220, 220, 220))
        screen.blit(texte, (panel_x + 30, y + 8))

        # Couleur selon réponse actuelle
        reponse = reponses.get(emetteur)
        couleur_acc = (0, 180, 0) if reponse == "ACCEPTE" else (50, 80, 50)
        couleur_ref = (180, 0, 0) if reponse == "REFUSE"  else (80, 50, 50)

        # Boutons
        btn_acc = pygame.Rect(panel_x + panel_w - 220, y, 90, 36)
        btn_ref = pygame.Rect(panel_x + panel_w - 120, y, 90, 36)
        pygame.draw.rect(screen, couleur_acc, btn_acc, border_radius=6)
        pygame.draw.rect(screen, couleur_ref, btn_ref, border_radius=6)
        screen.blit(font_texte.render("✔ OUI", True, (255,255,255)), (btn_acc.x + 10, btn_acc.y + 6))
        screen.blit(font_texte.render("✘ NON", True, (255,255,255)), (btn_ref.x + 10, btn_ref.y + 6))

        btns[emetteur] = (btn_acc, btn_ref)
        y += 55
        if y > panel_y + panel_h - 80:
            break  # Sécurité si trop de propositions

    # Bouton CONFIRMER (actif seulement si tout est répondu)
    tout_repondu = len(reponses) == len(propositions)
    couleur_confirm = (200, 150, 0) if tout_repondu else (60, 60, 60)
    btn_confirm = pygame.Rect(panel_x + panel_w//2 - 100, panel_y + panel_h - 60, 200, 45)
    pygame.draw.rect(screen, couleur_confirm, btn_confirm, border_radius=8)
    label_btn = "CONFIRMER" if tout_repondu else f"{len(reponses)}/{len(propositions)} répondu(e)s"
    screen.blit(font_titre.render(label_btn, True, (0,0,0)), (btn_confirm.x + 30, btn_confirm.y + 10))

    return btns, btn_confirm, tout_repondu

def dessiner_action_panel(code_cible, clic_x):
    """Dessine le panneau d'action de façon dynamique selon les relations."""
    panel_x = 850 if clic_x < WIDTH / 2 else 30
    panel_y = 100
    
    # Fond
    rect_panel = pygame.Rect(panel_x, panel_y, 400, 300)
    pygame.draw.rect(screen, (40, 40, 60), rect_panel, border_radius=10)
    
    # Titre
    nom_cible = CODES_TO_NAMES.get(code_cible, code_cible)
    screen.blit(font_titre.render(f"Ordres vers : {nom_cible}", True, (255, 255, 255)), (panel_x + 20, panel_y + 20))
    
    # Boutons d'action
    btn_action_1 = pygame.Rect(panel_x + 50, panel_y + 80, 300, 50)
    btn_action_2 = pygame.Rect(panel_x + 50, panel_y + 150, 300, 50)
    
    # --- LOGIQUE DE VERROUILLAGE ---
    monde = moteur.etat_jeu["monde"]
    est_allie = code_cible in monde[pays_joueur]["alliances"]
    est_en_guerre = code_cible in monde[pays_joueur]["en_guerre_contre"]
    actions_en_cours = actions_joueur.get(code_cible, [])

    # 1. Bouton Alliance / Rupture
    if est_en_guerre:
        couleur_1 = (40, 40, 40) # Noirâtre (Bloqué)
        label_1 = "Guerre en cours (Alliance impossible)"
    elif est_allie:
        couleur_1 = (200, 100, 50) if "ROMPRE_ALLIANCE" in actions_en_cours else (70, 70, 70)
        label_1 = "Rompre l'Alliance"
    else:
        couleur_1 = (50, 150, 50) if "ALLIANCE" in actions_en_cours else (70, 70, 70)
        label_1 = "Proposer Alliance"

    # 2. Bouton Guerre / Paix
    if est_allie:
        couleur_2 = (40, 40, 40) # Noirâtre (Bloqué)
        label_2 = "Allié (Attaque impossible)"
    elif est_en_guerre:
        couleur_2 = (50, 150, 200) if "PAIX" in actions_en_cours else (70, 70, 70)
        label_2 = "Signer la Paix"
    else:
        couleur_2 = (200, 50, 50) if "ATTAQUE" in actions_en_cours else (70, 70, 70)
        label_2 = "Déclarer la Guerre"
    

    # Dessin
    pygame.draw.rect(screen, couleur_1, btn_action_1, border_radius=5)
    pygame.draw.rect(screen, couleur_2, btn_action_2, border_radius=5)
    screen.blit(font_texte.render(label_1, True, (255, 255, 255)), (panel_x + 60, panel_y + 90))
    screen.blit(font_texte.render(label_2, True, (255, 255, 255)), (panel_x + 60, panel_y + 160))
    
    # On renvoie aussi l'état actuel pour que le clic sache quoi faire
    return btn_action_1, btn_action_2, est_allie, est_en_guerre


def dessiner_menu():
    """Affiche l'écran d'accueil avec les boutons Nouvelle Partie et Charger."""
    screen.fill((20, 20, 30)) # Fond sombre élégant
    
    # Titre du jeu
    titre_surf = font_titre.render("GEOPOLY 2026", True, (255, 255, 255))
    screen.blit(titre_surf, (WIDTH//2 - titre_surf.get_width()//2, 150))
    
    # Bouton Nouvelle Partie
    btn_neuf = pygame.Rect(WIDTH//2 - 150, 300, 300, 60)
    pygame.draw.rect(screen, (50, 150, 50), btn_neuf, border_radius=10)
    txt_neuf = font_texte.render("Nouvelle Partie", True, (255, 255, 255))
    screen.blit(txt_neuf, (btn_neuf.centerx - txt_neuf.get_width()//2, btn_neuf.centery - txt_neuf.get_height()//2))
    
    # Bouton Charger (uniquement si une save existe)
    btn_load = pygame.Rect(WIDTH//2 - 150, 400, 300, 60)
    couleur_load = (50, 50, 150) if os.path.exists(moteur.fichier_sauvegarde) else (80, 80, 80)
    pygame.draw.rect(screen, couleur_load, btn_load, border_radius=10)
    txt_load = font_texte.render("Charger la partie", True, (255, 255, 255))
    screen.blit(txt_load, (btn_load.centerx - txt_load.get_width()//2, btn_load.centery - txt_load.get_height()//2))
    
    return btn_neuf, btn_load

def dessiner_compteur_tour():
    """Affiche le numéro du tour juste au-dessus du bloc légende."""
    if phase_de_jeu != "JOUER": return
    
    tour = moteur.etat_jeu["tour"]
    
    # Positionnement : au-dessus de la légende (base_y de la légende - 40)
    # On utilise les mêmes coordonnées que ta légende pour l'alignement
    x_pos = 20
    y_pos = HEIGHT - 140 - 60 # 140 (hauteur légende) + 20 (marge) + 40 (décalage)
    
    # Petit badge pour le tour
    rect_tour = pygame.Rect(x_pos, y_pos, 150, 40)
    pygame.draw.rect(screen, (30, 30, 50), rect_tour, border_radius=5)
    pygame.draw.rect(screen, (200, 200, 200), rect_tour, 2, border_radius=5)
    
    texte_tour = font_titre.render(f"TOUR : {tour}", True, (255, 255, 255))
    screen.blit(texte_tour, (x_pos + 15, y_pos + 5))



def ajoute_action(pays_code, oui, non, cond):
    action = oui if cond else non
                 
    # Si le pays n'a aucune action, on crée une liste vide
    if pays_code not in actions_joueur:
        actions_joueur[pays_code] = []
    
    # On ajoute l'action si elle n'y est pas déjà
    if action not in actions_joueur[pays_code]:
        actions_joueur[pays_code].append(action)

    # Si on reclique on l'enleve
    else:
        actions_joueur[pays_code].remove(action)
    return actions_joueur

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

def calculer_vendeurs_disponibles(etat_du_monde):
    vendeurs = {"nourriture": {}, "petrole": {}}

    for pays, data in etat_du_monde.items():
        res = data["ressources"]


        # ── NOURRITURE ───────────────────────────────────────
        config = COMMERCE_CONFIG["nourriture"]
        conso = res["H"] * config["consommation_par_habitant"]

        stock_securite_petit = conso * config["seuil_surplus_petit"]
        stock_securite_gros  = conso * config["seuil_surplus_gros"]

        dispo_petits = max(0, res["N"] - stock_securite_petit)
        dispo_gros   = max(0, res["N"] - stock_securite_gros)

        lots_petits = int(dispo_petits // config["taille_petit_lot"])
        lots_gros   = int(dispo_gros   // config["taille_gros_lot"])

        if lots_petits > 0 or lots_gros > 0:
            vendeurs["nourriture"][pays] = {
                "lots_petits": lots_petits,
                "lots_gros": lots_gros,
                "total_unites": lots_petits  # en équivalent petits lots
            }

        # ── PÉTROLE ──────────────────────────────────────────
        config = COMMERCE_CONFIG["petrole"]
        conso = res["H"] * config["consommation_par_habitant"]

        stock_securite_petit = conso * config["seuil_surplus_petit"]
        stock_securite_gros  = conso * config["seuil_surplus_gros"]

        dispo_petits = max(0, res["P"] - stock_securite_petit)
        dispo_gros   = max(0, res["P"] - stock_securite_gros)

        lots_petits = int(dispo_petits // config["taille_petit_lot"])
        lots_gros   = int(dispo_gros   // config["taille_gros_lot"])

        if lots_petits > 0 or lots_gros > 0:
            vendeurs["petrole"][pays] = {
                "lots_petits": lots_petits,
                "lots_gros": lots_gros,
                "total_unites": lots_petits
            }

    return vendeurs



rect_fin_tour = pygame.Rect(WIDTH - 250, HEIGHT - 80, 230, 60)


# --- CHARGEMENT DES DONNÉES ---
dossier = os.path.dirname(os.path.abspath(__file__))

# 1. Les Cartes
MAP_VISUELLE = pygame.transform.scale(pygame.image.load(os.path.join(dossier, "assets/images/world_map.png")).convert(), (WIDTH, HEIGHT))
MAP_COULEURS = pygame.transform.scale(pygame.image.load(os.path.join(dossier, "assets/images/world_map_colors.png")).convert(), (WIDTH, HEIGHT))

# 2. Les JSON
with open(os.path.join(dossier, "data/pays_couleur.json"), 'r') as f:
    MAP_HEX_TO_CODE = json.load(f)

with open(os.path.join(dossier, "data/pays_base_stats.json"), 'r') as f:
    STATS_PAYS = json.load(f)

with open(os.path.join(dossier, "data/countries_codes.json"), 'r', encoding='utf-8') as f:
    CODES_TO_NAMES = json.load(f)

# --- ÉTATS DU JEU ---
pays_survole = None
pays_selectionne_code = None
pays_selectionne_hex = None
afficher_dashboard = False
dernier_clic_x = 0 
pays_joueur = None
calque_joueur = None 
actions_joueur = {}
achats_joueur  = {}   
vendeurs = {}
mois_actuel = 1
phase_de_jeu = "MENU"

commerce_boutons = {}   # { (vendeur, ressource, taille): Rect }
btn_fermer_commerce = None

# --- BOUCLE PRINCIPALE ---
running = True
calque_bleu = None
calques_diplo = []

# Si on a chargé une partie au lancement, on génère déjà la diplomatie
if phase_de_jeu == "JOUER":
    calques_diplo = maj_calques_diplomatie()

while running:
    mouse_pos = pygame.mouse.get_pos()

    # 0. Charger une partie
    if phase_de_jeu == "MENU":
        btn_neuf, btn_load = dessiner_menu()
        
        for event in pygame.event.get():
            # si le joueur ferme la fenetre par ex
            if event.type == pygame.QUIT:
                running = False
            
            # sinon
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_neuf.collidepoint(event.pos):
                    # On supprime l'ancienne save si elle existe pour repartir de zéro
                    if os.path.exists(moteur.fichier_sauvegarde):
                        os.remove(moteur.fichier_sauvegarde)
                    phase_de_jeu = "SELECTION" # On va choisir son pays
                    
                elif btn_load.collidepoint(event.pos) and os.path.exists(moteur.fichier_sauvegarde):
                    etat = moteur.charger_sauvegarde()
                    if etat:
                        phase_de_jeu = "JOUER"
                        pays_joueur = etat["pays_joueur"]
                        # On recrée les calques immédiatement
                        for hexa, code in MAP_HEX_TO_CODE.items():
                            if code == pays_joueur:
                                calque_joueur = creer_calque_couleur(hexa, (0, 100, 255, 150))
                        calques_diplo = maj_calques_diplomatie()
                        vendeurs = moteur.calculer_vendeurs_disponibles(moteur.etat_jeu["monde"])  # ← ICI

    elif phase_de_jeu == "SELECTION" or phase_de_jeu == "JOUER":
    
        # 1. Dessiner la carte de base
        screen.blit(MAP_VISUELLE, (0, 0))

        # 2. Dessiner TOUS les calques de couleurs
        if phase_de_jeu == "JOUER":
            # Les alliés et ennemis
            for calque in calques_diplo:
                screen.blit(calque, (0, 0))
            # Le pays du joueur
            if calque_joueur:
                screen.blit(calque_joueur, (0, 0))

            # Le calque bleu quand on survole/clique (pour la sélection)
        if afficher_dashboard and calque_bleu:
            screen.blit(calque_bleu, (0, 0))

    # 3. GESTION DES ÉVÉNEMENTS
    for event in pygame.event.get():
        # si le joueur ferme la fenetre par ex
        if event.type == pygame.QUIT:
            running = False

        # sinon
        elif event.type == pygame.MOUSEBUTTONDOWN:
            clic_sur_ui = False

            # ── PHASE SÉLECTION ────────────────────────────────────────────────────
            if phase_de_jeu == "SELECTION":
                if afficher_dashboard:
                    btn_fermer, btn_jouer = dessiner_dashboard(pays_selectionne_code, dernier_clic_x)
                    
                    if btn_fermer.collidepoint(mouse_pos):
                        afficher_dashboard = False
                        calque_bleu = None
                        clic_sur_ui = True

                    elif btn_jouer.collidepoint(mouse_pos):
                        moteur.nouvelle_partie(pays_selectionne_code)
                        phase_de_jeu = "JOUER"
                        pays_joueur = pays_selectionne_code
                        calque_joueur = creer_calque_couleur(pays_selectionne_hex, (0, 100, 255, 150))
                        calques_diplo = maj_calques_diplomatie()
                        vendeurs = calculer_vendeurs_disponibles(moteur.etat_jeu["monde"])
                        afficher_dashboard = False
                        clic_sur_ui = True

            # ── PHASE JOUER ────────────────────────────────────────────────────────
            elif phase_de_jeu == "JOUER":

                # — Bouton COMMERCE 
                if rect_btn_commerce.collidepoint(mouse_pos):
                    phase_de_jeu = "COMMERCE"
                    afficher_dashboard = False
                    clic_sur_ui = True

                # — Bouton FIN DE TOUR —
                elif rect_fin_tour.collidepoint(mouse_pos):
                    print(f"⏳ Simulation du tour {moteur.etat_jeu['tour']}...")

                    # Fusionner achats_joueur dans actions_joueur avant d'appeler l'IA
                    # actions_joueur : { pays_cible: [liste_actions_diplo] }  (format existant)
                    # achats_joueur  : { vendeur: action_str }
                    # generer_tour_ia attend : { cible: action } (une action par cible)
                    actions_finales_joueur = {}
                    for pays_c, liste in actions_joueur.items():
                        if liste:
                            actions_finales_joueur[pays_c] = liste[-1]  # on prend la dernière action
                    for vendeur, action_achat in achats_joueur.items():
                        actions_finales_joueur[vendeur] = action_achat

                    succes_ia = generer_tour_ia(moteur.etat_jeu, actions_finales_joueur, pays_joueur, vendeurs)

                    if succes_ia:
                        chemin_actions = os.path.join(dossier, "data", "actions_tour.json")
                        with open(chemin_actions, 'r', encoding='utf-8') as f:
                            data_json = json.load(f)
                        moteur.afficher_interface_tour(data_json["actions"], CODES_TO_NAMES)

                        succes_retours = traitement_propositions_ia(moteur.etat_jeu, data_json["actions"], vendeurs)

                        if succes_retours:
                            chemin_retours = os.path.join(dossier, "data", "retours_propositions.json")
                            with open(chemin_retours, 'r', encoding='utf-8') as f:
                                retours_json = json.load(f)
                            moteur.afficher_interface_tour2(retours_json["decisions"], CODES_TO_NAMES)

                            nouveau_monde = resoudre_tour(moteur.etat_jeu["monde"], chemin_actions, chemin_retours)
                            moteur.etat_jeu["monde"] = nouveau_monde
                            moteur.avancer_tour()
                            calques_diplo = maj_calques_diplomatie()
                            vendeurs = moteur.calculer_vendeurs_disponibles(moteur.etat_jeu["monde"])
                            actions_joueur.clear()
                            achats_joueur.clear()
                            afficher_dashboard = False
                        else:
                            print("❌ L'IA n'a pas pu répondre. Vérifie ta clé API ou ta connexion.")
                    else:
                        print("❌ L'IA n'a pas pu générer ses actions. Vérifie ta clé API ou ta connexion.")
                    clic_sur_ui = True

                # — Clics sur le panneau de diplomatie/commerce —
                elif afficher_dashboard:
                    btn_all, btn_att, est_allie, est_en_guerre = dessiner_action_panel(pays_selectionne_code, dernier_clic_x)
                    if btn_all.collidepoint(mouse_pos) and not est_en_guerre:
                        if "ATTAQUE" not in actions_joueur.get(pays_selectionne_code, []):
                            actions_joueur = ajoute_action(pays_selectionne_code, "ROMPRE_ALLIANCE", "ALLIANCE", est_allie)
                        clic_sur_ui = True

                    elif btn_att.collidepoint(mouse_pos) and not est_allie:
                        if "ALLIANCE" not in actions_joueur.get(pays_selectionne_code, []):
                            actions_joueur = ajoute_action(pays_selectionne_code, "PAIX", "ATTAQUE", est_en_guerre)
                        clic_sur_ui = True

            # ── PHASE commerce ───────────────────────────────────────────────────────
            elif phase_de_jeu == "COMMERCE":
                # Fermer le panneau commerce
                if btn_fermer and btn_fermer_commerce.collidepoint(mouse_pos):
                    phase_de_jeu = "JOUER"
                    clic_sur_ui = True
                
                
                # Sélectionner / désélectionner un lot
                for (vendeur, ressource, taille), btn_rect in commerce_boutons.items():
                    if btn_rect.collidepoint(mouse_pos):
                        action_str = (f"PROPOSE_GROS_ACHAT_{ressource.upper()}" if taille == "gros" else f"PROPOSE_PETIT_ACHAT_{ressource.upper()}")
                        if achats_joueur.get(vendeur) == action_str:
                            del achats_joueur[vendeur]
                        else:
                            achats_joueur[vendeur] = action_str
                        clic_sur_ui = True
                        break


            # ── DÉTECTION SUR LA CARTE (hors commerce) ──────────────────────────────
            if not clic_sur_ui and phase_de_jeu in ("SELECTION", "JOUER"):
                if mouse_pos[1] > 45 and not (phase_de_jeu == "JOUER" and mouse_pos[0] < 200 and mouse_pos[1] > HEIGHT - 140):
                    hex_clic = rgb_to_hex(MAP_COULEURS.get_at(mouse_pos))
                    if hex_clic in MAP_HEX_TO_CODE:
                        if phase_de_jeu == "SELECTION" or (phase_de_jeu == "JOUER"and MAP_HEX_TO_CODE[hex_clic] != pays_joueur):
                            pays_selectionne_code = MAP_HEX_TO_CODE[hex_clic]
                            pays_selectionne_hex = hex_clic
                            afficher_dashboard = True
                            dernier_clic_x = mouse_pos[0]
                            calque_bleu = creer_calque_couleur(pays_selectionne_hex, (0, 100, 255, 150))
                    else:
                        afficher_dashboard = False
                        if phase_de_jeu == "SELECTION":
                            calque_bleu = None

    # 4. AFFICHAGE DES INTERFACES
    if phase_de_jeu == "SELECTION" and afficher_dashboard:
        dessiner_dashboard(pays_selectionne_code, dernier_clic_x)

    elif phase_de_jeu == "JOUER":
        # Bouton COMMERCE
        pygame.draw.rect(screen, (50, 100, 180), rect_btn_commerce, border_radius=10)
        screen.blit(font_titre.render("COMMERCE", True, (255, 255, 255)),(rect_btn_commerce.x + 35, rect_btn_commerce.y + 15))
        # Badge achats en cours
        if achats_joueur:
            badge_surf = font_texte.render(f"  {len(achats_joueur)} achat(s)", True, (255, 220, 80))
            screen.blit(badge_surf, (rect_btn_commerce.x + 55, rect_btn_commerce.y - 22))

        # Bouton FIN DE TOUR
        pygame.draw.rect(screen, (200, 150, 0), rect_fin_tour, border_radius=10)
        screen.blit(font_titre.render("FIN DE TOUR", True, (0,0,0)), (rect_fin_tour.x + 30, rect_fin_tour.y + 15))

        dessiner_top_bar()
        dessiner_legende()
        dessiner_compteur_tour()

        if afficher_dashboard:
            dessiner_action_panel(pays_selectionne_code, dernier_clic_x)

    elif phase_de_jeu == "COMMERCE":
        screen.blit(MAP_VISUELLE, (0, 0)) 
        for calque in calques_diplo:
            screen.blit(calque, (0, 0))
        if calque_joueur:
            screen.blit(calque_joueur, (0, 0))
        # Le panneau marché (avec top bar visible au-dessus)
        argent = moteur.etat_jeu["monde"][pays_joueur]["ressources"]["A"]
        commerce_boutons, btn_fermer_commerce = dessiner_ecran_commerce(vendeurs, achats_joueur, argent)
        # Top bar par-dessus tout
        dessiner_top_bar()

    pygame.display.flip()

pygame.quit()
sys.exit()