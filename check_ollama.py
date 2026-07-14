"""
Vérifie qu'Ollama tourne ET que le modèle est installé. À LANCER EN PREMIER.
Si tout est vert, tu peux démarrer le worker puis l'orchestrateur.
"""
import json
import urllib.request

from config import MODEL_ID, OLLAMA_HOST

try:
    with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=5) as r:
        data = json.load(r)
except Exception:
    print("❌ Ollama ne répond pas sur", OLLAMA_HOST)
    print("   -> Ouvre l'application Ollama (elle doit tourner en arrière-plan), puis réessaie.")
    raise SystemExit(1)

noms = [m["name"] for m in data.get("models", [])]
print("✅ Ollama répond. Modèles installés :", noms or "(aucun)")

if any(n == MODEL_ID or n.startswith(MODEL_ID + ":") for n in noms):
    print(f"✅ Le modèle '{MODEL_ID}' est prêt. Tu peux lancer le projet.")
else:
    print(f"⚠️  Le modèle '{MODEL_ID}' n'est pas installé.")
    print(f"   -> Fais : ollama pull {MODEL_ID}")
