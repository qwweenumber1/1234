from typing import Dict, Optional

def calculate_order_price(
    width: Optional[float] = None,
    length: Optional[float] = None,
    height: Optional[float] = None,
    material: Optional[str] = None,
    infill: Optional[float] = None,
    real_weight: Optional[float] = None
) -> Dict:
    # Logic for price calculation
    rho = 1.24
    X = width or 0
    Y = length or 0
    Z = height or 0
    W = real_weight or 0
    I = infill or 20
    
    material_prices = {
        "PLA": 1.2, 
        "ABS": 1.5, 
        "PETG": 1.4, 
        "TPU": 3.0, 
        "Nylon": 4.5, 
        "SLA": 10.0,
        # Syncing with mobile app materials
        "PLA/PETG": 1.3,
        "ASA/NYLON": 4.5,
        "TPU 95A": 3.0,
        "PETG CF 10": 4.0,
        "ABSpro UL 94 V-0": 5.0,
        "Basic": 10.0,
        "ABS-Like Resin Pro": 15.0,
        "Flexible Tough Resin D76": 20.0,
        "High Clear": 17.0
    }
    
    P = material_prices.get(material, 1.2)
    K_I = 0.2 + 0.8 * (I / 100)
    V_cm3 = (X * Y * Z) / 1000
    Wv = V_cm3 * rho
    Wb = max(W, Wv)
    calculated_price = Wb * P * K_I
    
    min_price = 200
    # High-end materials have higher minimum price
    if material in ["TPU", "Nylon", "SLA", "ASA/NYLON", "TPU 95A", "PETG CF 10", "ABSpro UL 94 V-0", "ABS-Like Resin Pro", "Flexible Tough Resin D76", "High Clear"]:
        min_price = 500
        
    price = max(min_price, int(calculated_price))
    return {"price": price, "currency": "UAH"}
