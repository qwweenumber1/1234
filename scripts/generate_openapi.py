import sys
import os
sys.path.append(os.getcwd())
import yaml
from gateway.main import app

with open("openapi.yaml", "w", encoding="utf-8") as f:
    yaml.dump(app.openapi(), f, default_flow_style=False)
    
print("openapi.yaml generated successfully.")
