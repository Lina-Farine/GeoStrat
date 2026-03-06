import pygame
import json
import sys

# --- CONFIGURATION (1280 x 720) ---
WIDTH, HEIGHT = 1280, 720
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GEOPOLY - ID Map Precision Tool")
font = pygame.font.SysFont("Arial", 20, bold=True)

# --- CHARGEMENT DES ASSETS (Redimensionnés) ---
# Image visuelle pour le joueur
MAP_VISUELLE = pygame.transform.scale(pygame.image.load("assets/images/world_map.png").convert(), (WIDTH, HEIGHT))
# Image de collision (sans bruit)
MAP_COULEURS = pygame.transform.scale(pygame.image.load("assets/images/world_map_colors.png").convert(), (WIDTH, HEIGHT))

# --- DONNÉES DES PAYS ---
# Charge ton JSON vide ou rempli
try:
    with open('pays_couleur.json', 'r', encoding='utf-8') as f:
        DATA_PAYS = json.load(f)
except FileNotFoundError:
    DATA_PAYS = {}
    print("Fichier JSON non trouvé. Création d'un nouveau...")

selected_country = None
current_color = None

# --- FONCTIONS UTILES ---
def rgb_to_hex(rgb):
    """Transforme un tuple (r, g, b) en chaîne '#RRGGBB'"""
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2]).upper()

def get_country_at_mouse(pos):
    """Lit la couleur sur la carte masquée et retourne les infos du JSON"""
    # Récupérer la couleur RGB du pixel
    pixel_color = MAP_COULEURS.get_at(pos)
    # Convertir en HEX
    hex_key = rgb_to_hex(pixel_color)
    
    # Chercher dans le JSON
    if hex_key in DATA_PAYS:
        return DATA_PAYS[hex_key], hex_key
    
    # Si le pays n'est pas encore enregistré, on retourne l'Hex pour t'aider
    return "Pays Inconnu (Inscrivez-le !)", hex_key

# --- BOUCLE PRINCIPALE ---
while True:
    screen.blit(MAP_VISUELLE, (0, 0))
    mouse_pos = pygame.mouse.get_pos()

    # Détection au survol
    selected_country, current_color = get_country_at_mouse(mouse_pos)

    # Affichage du debug pour t'aider à remplir ton JSON
    text_info = font.render(f"PAYS : {selected_country}", True, (255, 255, 255))
    text_color = font.render(f"HEX  : {current_color}", True, (255, 255, 255))
    
    # Zone de debug en bas à gauche
    pygame.draw.rect(screen, (0, 0, 0), (10, HEIGHT - 70, 400, 60))
    screen.blit(text_info, (20, HEIGHT - 60))
    screen.blit(text_color, (20, HEIGHT - 40))

    # Gestion des événements
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Si tu cliques, ça t'aide à enregistrer le pays
            print(f"\n--- ENREGISTREMENT ---")
            print(f"Copié dans le presse-papier : {{ \"{current_color}\": \"Nom du pays\" }}")
            # Tu n'as plus qu'à coller ça dans ton JSON !

    pygame.display.flip()