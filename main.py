import pygame
import sys
import json
import os
from engine import GameEngine
from moteur import resoudre_tour

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
    """Affiche les ressources du joueur en haut de l'écran."""
    if phase_de_jeu != "JOUER": return
    
    stats = moteur.etat_jeu["monde"][pays_joueur]["ressources"]
    
    # Barre de fond noire semi-transparente
    rect_bar = pygame.Rect(0, 0, WIDTH, 45)
    pygame.draw.rect(screen, (30, 30, 30), rect_bar)
    pygame.draw.line(screen, (100, 100, 100), (0, 45), (WIDTH, 45), 2)
    
    # Les textes à afficher
    textes = [
        f"Pop: {int(stats['H'])}M",
        f"Nourriture: {int(stats['N'])}t",
        f"Pétrole: {int(stats['P'])}k",
        f"Argent: {int(stats['A'])}$",
        f"Satisfaction: {int(stats['S'])}%"
    ]
    
    x_offset = 50
    for texte in textes:
        surf = font_titre.render(texte, True, (255, 255, 255)) # Texte blanc
        screen.blit(surf, (x_offset, 8))
        x_offset += 230 # Espace entre chaque ressource

def dessiner_legende():
    """Dessine un petit bloc en bas à gauche pour expliquer les couleurs."""
    if phase_de_jeu != "JOUER": return
    
    # Boîte de fond
    rect_legende = pygame.Rect(20, HEIGHT - 140, 180, 120)
    pygame.draw.rect(screen, (40, 40, 40), rect_legende, border_radius=8)
    pygame.draw.rect(screen, (100, 100, 100), rect_legende, 2, border_radius=8)
    
    screen.blit(font_texte.render("Légende :", True, (255, 255, 255)), (30, HEIGHT - 130))
    
    # Bleu = Vous
    pygame.draw.rect(screen, (0, 100, 255), (30, HEIGHT - 95, 20, 20))
    screen.blit(font_texte.render("Votre Pays", True, (200, 200, 200)), (60, HEIGHT - 98))
    
    # Vert = Allié
    pygame.draw.rect(screen, (0, 200, 0), (30, HEIGHT - 65, 20, 20))
    screen.blit(font_texte.render("Alliés", True, (200, 200, 200)), (60, HEIGHT - 68))
    
    # Rouge = Ennemi
    pygame.draw.rect(screen, (200, 0, 0), (30, HEIGHT - 35, 20, 20))
    screen.blit(font_texte.render("En Guerre", True, (200, 200, 200)), (60, HEIGHT - 38))

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
    """Dessine le panneau d'action (Alliance/Attaque) en phase de jeu"""
    panel_x = 850 if clic_x < WIDTH / 2 else 30
    panel_y = 100
    
    # Fond
    rect_panel = pygame.Rect(panel_x, panel_y, 400, 300)
    pygame.draw.rect(screen, (40, 40, 60), rect_panel, border_radius=10)
    
    # Titre
    nom_cible = CODES_TO_NAMES.get(code_cible, code_cible)
    screen.blit(font_titre.render(f"Ordres vers : {nom_cible}", True, (255, 255, 255)), (panel_x + 20, panel_y + 20))
    
    # Boutons d'action
    btn_alliance = pygame.Rect(panel_x + 50, panel_y + 100, 300, 50)
    btn_attaque = pygame.Rect(panel_x + 50, panel_y + 170, 300, 50)
    
    # Couleurs selon si l'action est déjà planifiée
    couleur_all = (50, 150, 50) if actions_joueur.get(code_cible) == "ALLIANCE" else (70, 70, 70)
    couleur_att = (200, 50, 50) if actions_joueur.get(code_cible) == "ATTAQUE" else (70, 70, 70)
    
    pygame.draw.rect(screen, couleur_all, btn_alliance, border_radius=5)
    pygame.draw.rect(screen, couleur_att, btn_attaque, border_radius=5)
    
    screen.blit(font_texte.render("Proposer Alliance", True, (255,255,255)), (panel_x + 100, panel_y + 110))
    screen.blit(font_texte.render("Déclarer la Guerre", True, (255,255,255)), (panel_x + 100, panel_y + 180))
    
    return btn_alliance, btn_attaque

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
 
# --- SI SAUVEGARDE EXISTE ---
if etat_actuel:
    phase_de_jeu = "JOUER"
    pays_joueur = etat_actuel["pays_joueur"]
    
    # On cherche l'Hexa du pays du joueur pour recréer son calque bleu
    for hexa, code in MAP_HEX_TO_CODE.items():
        if code == pays_joueur:
            calque_joueur = creer_calque_couleur(hexa, (0, 100, 255, 255))
            break
else:
    phase_de_jeu = "SELECTION"

# --- BOUCLE PRINCIPALE ---
running = True
calque_bleu = None
calques_diplo = [] # <--- NOUVELLE VARIABLE ICI

# Si on a chargé une partie au lancement, on génère déjà la diplomatie
if phase_de_jeu == "JOUER":
    calques_diplo = maj_calques_diplomatie()

while running:
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
        if event.type == pygame.QUIT:
            running = False
            
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
                    print(f"⏳ Résolution du tour {moteur.etat_jeu['tour']} en cours...")
                    nouveau_monde = resoudre_tour(actions_joueur, moteur.etat_jeu["monde"], pays_joueur)
                    moteur.etat_jeu["monde"] = nouveau_monde
                    moteur.avancer_tour()
                    
                    # ---> MISE À JOUR ICI : On recalcule les rouges et verts car des alliances/guerres ont pu éclater !
                    calques_diplo = maj_calques_diplomatie()
                    
                    actions_joueur.clear()
                    clic_sur_ui = True
                    afficher_dashboard = False

                elif afficher_dashboard:
                    btn_all, btn_att = dessiner_action_panel(pays_selectionne_code, dernier_clic_x)
                    if btn_all.collidepoint(mouse_pos):
                        actions_joueur[pays_selectionne_code] = "ALLIANCE"
                        clic_sur_ui = True
                    elif btn_att.collidepoint(mouse_pos):
                        actions_joueur[pays_selectionne_code] = "ATTAQUE"
                        clic_sur_ui = True

            # DÉTECTION SUR LA CARTE
            if not clic_sur_ui:
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
        
        # On ajoute nos deux nouveaux éléments UI !
        dessiner_top_bar()
        dessiner_legende()
        
        if afficher_dashboard:
            dessiner_action_panel(pays_selectionne_code, dernier_clic_x)

    pygame.display.flip()

pygame.quit()
sys.exit()