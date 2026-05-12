from numpy.compat import asstr
import pygame
import sys
import json
import os

from engine import GameEngine
from moteur import resoudre_tour
from appel_ia import generer_tour_ia


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
    if phase_de_jeu != "JOUER": return
    
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

rect_fin_tour = pygame.Rect(WIDTH - 250, HEIGHT - 80, 230, 60)

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
    btn_action_3 = pygame.Rect(panel_x + 50, panel_y + 220, 300, 50)
    
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
    
    # 3. Bouton Commerce
    if est_en_guerre:
        couleur_3 = (40, 40, 40) # Noirâtre (Bloqué)
        label_3 = "Guerre en cours (Commerce impossible)"
    else:
        couleur_3 = (50, 150, 50) if "COMMERCE" in actions_en_cours else (70, 70, 70)
        label_3 = "Proposer Commerce"

    # Dessin
    pygame.draw.rect(screen, couleur_1, btn_action_1, border_radius=5)
    pygame.draw.rect(screen, couleur_2, btn_action_2, border_radius=5)
    pygame.draw.rect(screen, couleur_3, btn_action_3, border_radius=5)
    screen.blit(font_texte.render(label_1, True, (255, 255, 255)), (panel_x + 60, panel_y + 90))
    screen.blit(font_texte.render(label_2, True, (255, 255, 255)), (panel_x + 60, panel_y + 160))
    screen.blit(font_texte.render(label_3, True, (255, 255, 255)), (panel_x + 60, panel_y + 230))
    
    # On renvoie aussi l'état actuel pour que le clic sache quoi faire
    return btn_action_1, btn_action_2, btn_action_3, est_allie, est_en_guerre


def dessiner_commerce_panel(code_cible, clic_x):
    """Dessine le panneau d'action de façon dynamique selon les relations."""
    panel_x = 850 if clic_x < WIDTH / 2 else 30
    panel_y = 100
    
    # Fond
    rect_panel = pygame.Rect(panel_x, panel_y, 400, 400)
    pygame.draw.rect(screen, (40, 40, 60), rect_panel, border_radius=10)
    
    # Titre
    nom_cible = CODES_TO_NAMES.get(code_cible, code_cible)
    screen.blit(font_titre.render(f"Commerce avec : {nom_cible}", True, (255, 255, 255)), (panel_x + 20, panel_y + 20))
    
    # Boutons d'action
    btn_action_1 = pygame.Rect(panel_x + 50, panel_y + 80, 300, 50)
    btn_action_2 = pygame.Rect(panel_x + 50, panel_y + 150, 300, 50)
    btn_action_3 = pygame.Rect(panel_x + 50, panel_y + 220, 300, 50)
    btn_action_4 = pygame.Rect(panel_x + 50, panel_y + 290, 300, 50)

    
    # --- LOGIQUE DE VERROUILLAGE ---
    monde = moteur.etat_jeu["monde"]
    vend_nourriture_a = code_cible in monde[pays_joueur]["vend_nourriture_a"]
    achete_nourriture_a = code_cible in monde[pays_joueur]["achete_nourriture_a"]
    vend_petrole_a = code_cible in monde[pays_joueur]["vend_petrole_a"]
    achete_petrole_a = code_cible in monde[pays_joueur]["achete_petrole_a"]
    actions_en_cours = actions_joueur.get(code_cible, [])

    # 1. Bouton Vendre nourriture
    if vend_nourriture_a:
        couleur_1 = (200, 100, 50) if "PAS_VENDRE_N" in actions_en_cours else (70, 70, 70)
        label_1 = "Arreter de vendre de la nourriture"
    else:
        couleur_1 = (50, 150, 50) if "VENDRE_N" in actions_en_cours else (70, 70, 70)
        label_1 = "Vendre de la nourriture"
    
    # 2. Bouton Acheter nourriture
    if achete_nourriture_a:
        couleur_2 = (200, 100, 50) if "PAS_ACHETER_N" in actions_en_cours else (70, 70, 70)
        label_2 = "Arreter d'acheter de la nourriture"
    else:
        couleur_2 = (50, 150, 50) if "ACHETER_N" in actions_en_cours else (70, 70, 70)
        label_2 = "Acheter de la nourriture"

    # 3. Bouton Vendre pétrole
    if vend_petrole_a:
        couleur_3 = (200, 100, 50) if "PAS_VENDRE_P" in actions_en_cours else (70, 70, 70)
        label_3 = "Arreter de vendre du pétrole"
    else:
        couleur_3 = (50, 150, 50) if "VENDRE_P" in actions_en_cours else (70, 70, 70)
        label_3 = "Vendre du pétrole"
    
    # 4. Acheter pétrole
    if achete_petrole_a:
        couleur_4 = (200, 100, 50) if "PAS_ACHETER_P" in actions_en_cours else (70, 70, 70)
        label_4 = "Arreter d'acheter du pétrole"
    else:
        couleur_4 = (50, 150, 50) if "ACHETER_P" in actions_en_cours else (70, 70, 70)
        label_4 = "Acheter du pétrole"
    

    # Dessin
    pygame.draw.rect(screen, couleur_1, btn_action_1, border_radius=5)
    pygame.draw.rect(screen, couleur_2, btn_action_2, border_radius=5)
    pygame.draw.rect(screen, couleur_3, btn_action_3, border_radius=5)
    pygame.draw.rect(screen, couleur_4, btn_action_4, border_radius=5)
    screen.blit(font_texte.render(label_1, True, (255, 255, 255)), (panel_x + 60, panel_y + 90))
    screen.blit(font_texte.render(label_2, True, (255, 255, 255)), (panel_x + 60, panel_y + 160))
    screen.blit(font_texte.render(label_3, True, (255, 255, 255)), (panel_x + 60, panel_y + 230))
    screen.blit(font_texte.render(label_4, True, (255, 255, 255)), (panel_x + 60, panel_y + 300))
    
    # On renvoie aussi l'état actuel pour que le clic sache quoi faire
    return btn_action_1, btn_action_2, btn_action_3, btn_action_4, achete_nourriture_a, vend_nourriture_a, achete_petrole_a, vend_petrole_a


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
mois_actuel = 1
phase_de_jeu = "MENU"
menu_actuel = "DIPLOMATIE" # Peut être "DIPLOMATIE" ou "COMMERCE"

# --- BOUCLE PRINCIPALE ---
running = True
calque_bleu = None
calques_diplo = [] # <--- NOUVELLE VARIABLE ICI

# Si on a chargé une partie au lancement, on génère déjà la diplomatie
if phase_de_jeu == "JOUER":
    calques_diplo = maj_calques_diplomatie()

while running:

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

    elif phase_de_jeu == "SELECTION" or phase_de_jeu == "JOUER":
    
        # 1. Dessiner la carte de base
        screen.blit(MAP_VISUELLE, (0, 0))
        mouse_pos = pygame.mouse.get_pos()

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
                        
                        # ---> MISE À JOUR ICI : On utilise "creer_calque_couleur" au lieu de "creer_calque_bleu"
                        calque_joueur = creer_calque_couleur(pays_selectionne_hex, (0, 100, 255, 150))
                        calques_diplo = maj_calques_diplomatie() # On génère les rouges et verts
                        
                        afficher_dashboard = False
                        clic_sur_ui = True
                        
            elif phase_de_jeu == "JOUER":
                if rect_fin_tour.collidepoint(mouse_pos):
                    print(f"⏳ Simulation du tour {moteur.etat_jeu['tour']}...")
                    
                    # 1. On appelle l'IA pour qu'elle génère le fichier "actions_tour.json"
                    # On lui passe l'état actuel, tes actions cliquées, et ton code pays (ex: "US")
                    succes_ia = generer_tour_ia(moteur.etat_jeu, actions_joueur, pays_joueur)
                    
                    if succes_ia:
                        chemin_actions = os.path.join(dossier, "data", "actions_tour.json")
                        
                        # --- C'EST ICI QU'ON APPELLE LA CONSOLE ---
                        with open(chemin_actions, 'r', encoding='utf-8') as f:
                            data_json = json.load(f)
                            # On passe bien data_json["actions"] à l'affichage
                            moteur.afficher_interface_tour(data_json["actions"], CODES_TO_NAMES)

                        nouveau_monde = resoudre_tour(moteur.etat_jeu["monde"], chemin_actions)
                        moteur.etat_jeu["monde"] = nouveau_monde
                        moteur.avancer_tour()
                        
                        calques_diplo = maj_calques_diplomatie()
                        actions_joueur.clear()
                        afficher_dashboard = False
                    else:
                        print("❌ L'IA n'a pas pu répondre. Vérifie ta clé API ou ta connexion.")

                elif afficher_dashboard:
                    if menu_actuel == "DIPLOMATIE":
                        # On récupère les 4 variables retournées par la fonction
                        btn_all, btn_att, btn_comm, est_allie, est_en_guerre = dessiner_action_panel(pays_selectionne_code, dernier_clic_x)
                        

                        if btn_all.collidepoint(mouse_pos) and not est_en_guerre:
                            if "ATTAQUE" not in actions_joueur.get(pays_selectionne_code, []):
                                actions_joueur = ajoute_action(pays_selectionne_code, "ROMPRE_ALLIANCE", "ALLIANCE", est_allie)
                            clic_sur_ui = True
                            
                        elif btn_att.collidepoint(mouse_pos) and not est_allie:
                            if "ALLIANCE" not in actions_joueur.get(pays_selectionne_code, []):
                                actions_joueur = ajoute_action(pays_selectionne_code, "PAIX", "ATTAQUE", est_en_guerre)
                            clic_sur_ui = True
                        
                        elif btn_comm.collidepoint(mouse_pos) and not est_en_guerre:
                            menu_actuel = "COMMERCE"
                            clic_sur_ui = True
                            

                    elif menu_actuel == "COMMERCE" :
                        # Affiche options de commerce
                        btn_v_no, btn_a_no, btn_v_pe, btn_a_pe, vend_n, achete_n, vend_p, achete_p = dessiner_commerce_panel(pays_selectionne_code, dernier_clic_x)
                            
                        if btn_v_no.collidepoint(mouse_pos):
                            actions_joueur = ajoute_action(pays_selectionne_code, "PAS_VENDRE_N", "VENDRE_N", vend_n)
                            clic_sur_ui = True
                        
                        if btn_a_no.collidepoint(mouse_pos):
                            actions_joueur = ajoute_action(pays_selectionne_code, "PAS_ACHETER_N", "ACHETER_N", achete_n)
                            clic_sur_ui = True

                        if btn_v_pe.collidepoint(mouse_pos):
                            if not achete_p and "ACHETER_P" not in actions_joueur.get(pays_selectionne_code, []):
                                actions_joueur = ajoute_action(pays_selectionne_code, "PAS_VENDRE_P", "VENDRE_P", vend_p)
                            clic_sur_ui = True
                        
                        if btn_a_pe.collidepoint(mouse_pos):
                            if not vend_p and "VENDRE_P" not in actions_joueur.get(pays_selectionne_code, []):
                                actions_joueur = ajoute_action(pays_selectionne_code, "PAS_ACHETER_P", "ACHETER_P", achete_p)
                            clic_sur_ui = True


            # DÉTECTION SUR LA CARTE
            if not clic_sur_ui:
                menu_actuel = "DIPLOMATIE"
                # IMPORTANT : Pour ne pas cliquer sur la top bar ou la légende
                if mouse_pos[1] > 45 and not (phase_de_jeu == "JOUER" and mouse_pos[0] < 200 and mouse_pos[1] > HEIGHT - 140):
                    hex_clic = rgb_to_hex(MAP_COULEURS.get_at(mouse_pos))
                    
                    if hex_clic in MAP_HEX_TO_CODE:
                        if phase_de_jeu == "SELECTION" or (phase_de_jeu == "JOUER" and MAP_HEX_TO_CODE[hex_clic] != pays_joueur):
                            pays_selectionne_code = MAP_HEX_TO_CODE[hex_clic]
                            pays_selectionne_hex = hex_clic
                            afficher_dashboard = True
                            dernier_clic_x = mouse_pos[0]
                            
                            # ---> MISE À JOUR ICI
                            calque_bleu = creer_calque_couleur(pays_selectionne_hex, (0, 100, 255, 150))
                    else:
                        afficher_dashboard = False
                        if phase_de_jeu == "SELECTION":
                            calque_bleu = None

    # 4. AFFICHAGE DES INTERFACES
    if phase_de_jeu == "SELECTION" and afficher_dashboard:
        dessiner_dashboard(pays_selectionne_code, dernier_clic_x)
        
    elif phase_de_jeu == "JOUER":
        pygame.draw.rect(screen, (200, 150, 0), rect_fin_tour, border_radius=10)
        screen.blit(font_titre.render("FIN DE TOUR", True, (0,0,0)), (rect_fin_tour.x + 30, rect_fin_tour.y + 15))
        
        dessiner_top_bar()
        dessiner_legende()
        dessiner_compteur_tour()
        
        if afficher_dashboard:
            if menu_actuel == "DIPLOMATIE":
                dessiner_action_panel(pays_selectionne_code, dernier_clic_x)
            elif menu_actuel == "COMMERCE":
                dessiner_commerce_panel(pays_selectionne_code, dernier_clic_x)

    pygame.display.flip()

pygame.quit()
sys.exit()