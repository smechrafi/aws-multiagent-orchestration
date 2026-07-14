"""
Agent WORKER spécialisé dans l'ESTIMATION DE COÛTS AWS, exposé sur le réseau via
le protocole A2A.

A2A (Agent-to-Agent) = un standard qui permet à un agent d'en appeler un autre par
HTTP. Ici on transforme ce worker en petit service : l'orchestrateur (main.py)
pourra le solliciter comme un simple outil dès qu'une question implique une
estimation de facture AWS (prix d'instances EC2, de stockage S3, de Lambda, etc.).

Lance-le dans SON PROPRE terminal :  python worker.py
Il écoute sur http://127.0.0.1:9000 et reste actif (laisse la fenêtre ouverte).
"""
import logging

from strands import Agent, tool
from strands.multiagent.a2a import A2AServer
from strands_tools.calculator import calculator

from config import build_model

logging.basicConfig(level=logging.INFO)


# Tarifs indicatifs simplifiés (USD, base région us-east-1, à la demande).
# But pédagogique uniquement : NE PAS utiliser pour un devis réel — les prix
# varient par région, par offre (Reserved/Spot/Savings Plans) et dans le temps.
# Chaque entrée : identifiant -> (prix_unitaire, unité, libellé lisible).
TARIFS_AWS = {
    "ec2-t3-micro":      (0.0104, "heure",              "instance EC2 t3.micro à la demande"),
    "ec2-t3-small":      (0.0208, "heure",              "instance EC2 t3.small à la demande"),
    "ec2-m5-large":      (0.096,  "heure",              "instance EC2 m5.large à la demande"),
    "s3-standard":       (0.023,  "Go-mois",            "stockage Amazon S3 Standard"),
    "ebs-gp3":           (0.08,   "Go-mois",            "volume Amazon EBS gp3"),
    "rds-t3-micro":      (0.017,  "heure",              "base Amazon RDS db.t3.micro"),
    "lambda":            (0.20,   "million de requêtes", "invocations AWS Lambda"),
    "transfert-sortant": (0.09,   "Go",                 "transfert de données sortant vers Internet"),
}

# Coefficient de prix par région (indicatif, base us-east-1 = 1.00). Illustre le
# concept CLF-C02 : le prix d'un même service varie selon la région AWS.
COEFF_REGION = {
    "us-east-1":      1.00,
    "us-west-2":      1.00,
    "eu-west-1":      1.08,   # Irlande
    "eu-west-3":      1.10,   # Paris
    "eu-central-1":   1.12,   # Francfort
    "ap-southeast-1": 1.15,   # Singapour
    "ap-northeast-1": 1.14,   # Tokyo
}


def _coeff_region(region):
    """Renvoie (coefficient, région_effective, note). Si la région est inconnue,
    on retombe sur la base us-east-1 en le signalant, pour ne jamais annoncer une
    région différente de celle réellement utilisée dans le calcul."""
    r = region.strip().lower()
    if r in COEFF_REGION:
        return COEFF_REGION[r], r, ""
    return 1.00, "us-east-1", f" (région '{region}' non tarifée, base us-east-1 utilisée)"


@tool
def calculateur_cout_aws(service: str, quantite: float, region: str = "us-east-1") -> str:
    """Estime le coût d'un service AWS à partir d'un tarif indicatif simplifié.

    service : identifiant du service, parmi ec2-t3-micro, ec2-t3-small,
              ec2-m5-large, s3-standard, ebs-gp3, rds-t3-micro, lambda,
              transfert-sortant.
    quantite : nombre TOTAL d'unités consommées (heures, Go-mois, Go, ou millions
               de requêtes selon le service). Si plusieurs ressources tournent en
               parallèle, multiplie d'abord le nombre de ressources par la durée.
    region : région AWS (par exemple us-east-1, eu-west-3, eu-central-1). Le prix
             est ajusté par un coefficient régional.
    """
    cle = service.strip().lower()
    if cle not in TARIFS_AWS:
        return (
            f"Service inconnu : {service}. "
            f"Services disponibles : {', '.join(TARIFS_AWS)}."
        )
    prix, unite, libelle = TARIFS_AWS[cle]
    coeff, region_utilisee, note = _coeff_region(region)
    total = prix * quantite * coeff
    return (
        f"{libelle}, région {region_utilisee}{note} : "
        f"{quantite:g} {unite} x {prix} USD x {coeff:.2f} = {total:.2f} USD "
        f"(tarif indicatif simplifié, hors taxes)."
    )


agent = Agent(
    model=build_model(),
    name="Agent Coût AWS",
    description="Agent spécialisé dans l'estimation de coûts de services AWS, par région.",
    system_prompt=(
        "Tu es un agent d'estimation de coûts AWS. Pour chaque service demandé, "
        "détermine le nombre TOTAL d'unités (par exemple nombre d'instances x nombre "
        "d'heures) puis appelle l'outil calculateur_cout_aws avec l'identifiant du "
        "service, cette quantité, et la région si l'utilisateur en précise une "
        "(par défaut us-east-1). Utilise l'outil calculator pour toute multiplication "
        "ou pour additionner plusieurs coûts. Dans ta réponse, REPRENDS le détail "
        "chiffré renvoyé par l'outil (quantité x prix unitaire x coefficient régional "
        "= total) et donne le total en dollars US, en précisant que les tarifs sont "
        "indicatifs. Réponds en une à trois phrases."
    ),
    tools=[calculateur_cout_aws, calculator],
    callback_handler=None,
)

if __name__ == "__main__":
    logging.info("Worker A2A (coûts AWS) démarré sur http://127.0.0.1:9000 (Ctrl+C pour arrêter)")
    A2AServer(agent=agent, host="127.0.0.1", port=9000).serve()