import pygame
import cv2
import numpy as np
import json
import random
import sys
import os

pygame.init()
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GEOPOLY - Ajouter des pays (Appuyez sur 'S' pour Sauvegarder)")

# --- CHEMINS DES FICHIERS ---
dossier_script = os.path.dirname(os.path.abspath(__file__))
chemin_image_base = os.path.join(dossier_script, "world_map.png")          # Ta carte grise
chemin_image_couleurs = os.path.join(dossier_script, "world_map_colors.png") # Ta carte colorée (fond noir)
chemin_json = os.path.join(dossier_script, "pays_couleur.json")            # Ton JSON

# 1. Chargement de la carte de base
carte_originale = cv2.imread(chemin_image_base)
if carte_originale is None:
    print(f"❌ Erreur: '{chemin_image_base}' introuvable !")
    sys.exit()
carte_originale = cv2.resize(carte_originale, (WIDTH, HEIGHT))

# --- FONCTIONS DE CONVERSION COULEURS ---
def hex_to_bgr(hex_str):
    """Convertit un #HEX en BGR pour OpenCV"""
    hex_str = hex_str.lstrip('#')
    r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    return (b, g, r)

def bgr_to_hex(bgr):
    """Convertit du BGR OpenCV en #HEX pour le JSON"""
    return f"#{bgr[2]:02X}{bgr[1]:02X}{bgr[0]:02X}"

# 2. REPRISE DES DONNÉES EXISTANTES
pays_hexa = {}
nom_vers_bgr = {}

# On charge l'image colorée si elle existe, sinon on crée un fond noir
if os.path.exists(chemin_image_couleurs):
    color_map = cv2.imread(chemin_image_couleurs)
    color_map = cv2.resize(color_map, (WIDTH, HEIGHT))
    print("✅ Ancienne carte des couleurs chargée !")
else:
    color_map = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

# On charge le JSON s'il existe
if os.path.exists(chemin_json):
    with open(chemin_json, 'r', encoding='utf-8') as f:
        pays_hexa = json.load(f)
        # On mémorise les couleurs pour pouvoir rajouter des îles à des pays existants
        for hexa, nom in pays_hexa.items():
            nom_vers_bgr[nom] = hex_to_bgr(hexa)
    print("✅ Ancien JSON chargé avec succès !")

# --- AFFICHAGE ---
def update_screen():
    rgb_original = cv2.cvtColor(carte_originale, cv2.COLOR_BGR2RGB)
    rgb_colors = cv2.cvtColor(color_map, cv2.COLOR_BGR2RGB)
    
    surf_orig = pygame.surfarray.make_surface(rgb_original.swapaxes(0, 1))
    surf_colors = pygame.surfarray.make_surface(rgb_colors.swapaxes(0, 1))
    
    surf_colors.set_colorkey((0,0,0))
    surf_colors.set_alpha(180) # Transparence pour voir la carte dessous
    
    screen.blit(surf_orig, (0, 0))
    screen.blit(surf_colors, (0, 0))
    pygame.display.flip()

update_screen()

print("\n🌍 Prêt à ajouter de nouveaux pays !")
print("-> Clique sur un pays non coloré.")
print("-> Saisis son nom dans ce terminal (ex: IT, JP, MX).")
print("-> Appuie sur 'S' pour sauvegarder et quitter.\n")

# --- BOUCLE PRINCIPALE ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                # SAUVEGARDE FINALE
                cv2.imwrite(chemin_image_couleurs, color_map)
                with open(chemin_json, "w", encoding="utf-8") as f:
                    json.dump(pays_hexa, f, indent=4)
                print("\n💾 SAUVEGARDE RÉUSSIE !")
                print("Ton image et ton JSON ont été mis à jour.")
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            
            nom_pays = input("-> Quel est l'ID de ce pays (ex: 'ZA', 'EG') ? : ").strip()
            
            if nom_pays:
                if nom_pays in nom_vers_bgr:
                    bgr_color = nom_vers_bgr[nom_pays]
                    print(f"ℹ️ Le pays '{nom_pays}' existe déjà, on utilise la même couleur.")
                else:
                    bgr_color = (random.randint(10,250), random.randint(10,250), random.randint(10,250))
                    nom_vers_bgr[nom_pays] = bgr_color
                    pays_hexa[bgr_to_hex(bgr_color)] = nom_pays
                    
                # Pot de peinture OpenCV
                h, w = carte_originale.shape[:2]
                mask = np.zeros((h+2, w+2), np.uint8)
                cv2.floodFill(carte_originale.copy(), mask, (x, y), (255,255,255), (10,10,10), (10,10,10), cv2.FLOODFILL_MASK_ONLY | (255 << 8))
                
                mask_crop = mask[1:-1, 1:-1]
                color_map[mask_crop == 255] = bgr_color
                
                print(f"✅ {nom_pays} ajouté !")
                update_screen()

pygame.quit()
sys.exit()