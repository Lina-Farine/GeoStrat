import json
import os

class GameEngine:
    def __init__(self):
        # On pointe bien vers le dossier "data"
        self.dossier = os.path.dirname(os.path.abspath(__file__))
        self.fichier_base = os.path.join(self.dossier, "data", "pays_base_stats.json")
        self.fichier_sauvegarde = os.path.join(self.dossier, "data", "partie_en_cours.json")
        
        self.etat_jeu = None

    def _charger_stats_base(self):
        with open(self.fichier_base, 'r', encoding='utf-8') as f:
            return json.load(f)

    def nouvelle_partie(self, pays_joueur):
        print(f"🌍 Création d'un nouveau monde (Contexte 2026). Joueur: {pays_joueur}")
        stats_base = self._charger_stats_base()
        
        chemin_diplo = os.path.join(self.dossier, "data", "situation_initiale.json")
        with open(chemin_diplo, 'r', encoding='utf-8') as f:
            diplo_initiale = json.load(f)
        
        monde = {}
        # 1. On charge d'abord les données brutes
        for code_pays, stats in stats_base.items():
            diplo = diplo_initiale.get(code_pays, {"alliances": [], "en_guerre_contre": []})
            monde[code_pays] = {
                "ressources": stats.copy(),
                "alliances": diplo["alliances"],
                "en_guerre_contre": diplo["en_guerre_contre"]
            }

        # 2. SYMÉTRISATION AUTOMATIQUE (La sécurité)
        # On parcourt chaque pays pour s'assurer que les relations sont réciproques
        for pays_a, data in monde.items():
            # Pour les guerres
            for pays_b in data["en_guerre_contre"]:
                if pays_b in monde and pays_a not in monde[pays_b]["en_guerre_contre"]:
                    monde[pays_b]["en_guerre_contre"].append(pays_a)
            
            # Pour les alliances (même logique)
            for pays_b in data["alliances"]:
                if pays_b in monde and pays_a not in monde[pays_b]["alliances"]:
                    monde[pays_b]["alliances"].append(pays_a)
            
        self.etat_jeu = {
            "tour": 1,
            "pays_joueur": pays_joueur,
            "monde": monde
        }
        self.sauvegarder()
        return self.etat_jeu

    def charger_sauvegarde(self):
        if os.path.exists(self.fichier_sauvegarde):
            print("💾 Fichier de sauvegarde trouvé. Chargement...")
            with open(self.fichier_sauvegarde, 'r', encoding='utf-8') as f:
                self.etat_jeu = json.load(f)
            return self.etat_jeu
        return None

    def sauvegarder(self):
        if self.etat_jeu is not None:
            with open(self.fichier_sauvegarde, 'w', encoding='utf-8') as f:
                json.dump(self.etat_jeu, f, indent=4, ensure_ascii=False)
            print("✅ Partie sauvegardée (Tour {})".format(self.etat_jeu["tour"]))

    def avancer_tour(self):
        """Fait juste avancer le compteur de tour et sauvegarde"""
        if self.etat_jeu:
            self.etat_jeu['tour'] += 1
            self.sauvegarder()