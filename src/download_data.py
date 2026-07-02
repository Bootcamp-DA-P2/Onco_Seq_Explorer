# download_data.py
from ucimlrepo import fetch_ucirepo
import pandas as pd
import os

os.makedirs("data", exist_ok=True)

dataset = fetch_ucirepo(id=401)

X = dataset.data.features   # los 20.531 genes
y = dataset.data.targets    # la etiqueta de tipo de tumor

X.to_csv("data/gene_expression.csv", index=False)
y.to_csv("data/labels.csv", index=False)

print(f"Guardado: {X.shape[0]} muestras x {X.shape[1]} genes")

# para cargar en notebooks:
#import pandas as pd
#X = pd.read_csv("data/gene_expression.csv")
#y = pd.read_csv("data/labels.csv")
