"""
Configuration du modèle. Au lancement, l'utilisateur choisit :
  1) Ollama (local)  -> rien à configurer, tourne sur ta machine
  2) AWS Bedrock     -> demande la région et le modèle
                        (les credentials viennent de `aws configure` / variables AWS)

Astuce : pour ne PAS être redemandé (utile avec les 2 terminaux), tu peux imposer
le choix via une variable d'environnement avant de lancer :
    set PROVIDER=ollama     (ou)     set PROVIDER=bedrock

Le modèle Ollama par défaut est qwen2.5 : il est nettement plus fiable que
llama3.1 pour l'appel d'outils (tool calling), indispensable dans ce projet
multi-agents. Tu peux le changer sans toucher au code via :
    set OLLAMA_MODEL=nom_du_modele
"""
import os

# Constantes de configuration Ollama, exposées au niveau module pour que
# check_ollama.py puisse les importer (préflight avant lancement).
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_ID = os.getenv("OLLAMA_MODEL", "qwen2.5")


def _demander(question, defaut):
    """Pose une question avec une valeur par défaut (Entrée = défaut)."""
    rep = input(f"{question} [{defaut}] : ").strip()
    return rep or defaut


def _choisir_provider():
    provider = os.getenv("PROVIDER")
    if provider:
        return provider.strip().lower()
    print("\nQuel modèle d'IA veux-tu utiliser ?")
    print("  1) Ollama  (local, rien à configurer)")
    print("  2) AWS Bedrock  (cloud) [Attention : C'est payant !]")
    choix = input("Ton choix [1/2] (défaut 1) : ").strip()
    return "bedrock" if choix == "2" else "ollama"


def _build_ollama():
    from strands.models.ollama import OllamaModel

    print(f"-> Ollama (local), modele '{MODEL_ID}'")
    return OllamaModel(host=OLLAMA_HOST, model_id=MODEL_ID, temperature=0.3)


def _build_bedrock():
    from strands.models import BedrockModel

    # On demande les infos necessaires (ou on les prend dans l'env si deja definies).
    region = os.getenv("AWS_REGION") or _demander("Region AWS", "eu-west-3")
    model_id = os.getenv("BEDROCK_MODEL_ID") or _demander(
        "ID du modele (profil d'inference)",
        "eu.amazon.nova-lite-v1:0",
    )
    print(f"-> AWS Bedrock, region '{region}', modele '{model_id}'")
    print("  (credentials pris depuis `aws configure` / variables d'env AWS)")
    return BedrockModel(model_id=model_id, region_name=region)


def build_model():
    """Fabrique le modele selon le choix de l'utilisateur (Ollama ou Bedrock)."""
    if _choisir_provider() == "bedrock":
        return _build_bedrock()
    return _build_ollama()