class Country:
    def __init__(self, name, n, p, h, a, s):
        self.name = name
        self.resources = {"N": n, "P": p, "H": h, "A": a, "S": s}
        self.alliances = [] # Liste des pays alliés

    def get_trade_price(self, item, amount, partner_name):
        # Prix de base : 1.5 Argent pour 1 Pétrole (exemple)
        base_rate = 1.5 if item == "P" else 1.0
        
        # Si allié, réduction de 33% (1.5 -> 1.0)
        if partner_name in self.alliances:
            return amount * (base_rate * 0.66)
        return amount * base_rate