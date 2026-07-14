"""
Mini serveur MCP (Model Context Protocol) en stdio.

Il expose UN outil "externe" : un GLOSSAIRE AWS qui donne la définition courte
d'un terme, service ou acronyme (vocabulaire de la certification Cloud
Practitioner). C'est main.py qui lance ce serveur automatiquement en
sous-processus : tu n'as RIEN à démarrer toi-même pour le MCP.
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("glossaire-aws")

# Table de définitions (lookup déterministe, comme une source de données externe).
GLOSSAIRE = {
    "IAM": "Identity and Access Management : gestion des identités et des accès (utilisateurs, groupes, rôles, politiques).",
    "EC2": "Elastic Compute Cloud : machines virtuelles (instances) à la demande.",
    "S3": "Simple Storage Service : stockage d'objets hautement durable et évolutif.",
    "EBS": "Elastic Block Store : stockage bloc persistant attaché aux instances EC2.",
    "EFS": "Elastic File System : système de fichiers partagé et élastique.",
    "VPC": "Virtual Private Cloud : réseau privé virtuel isolé au sein d'AWS.",
    "RDS": "Relational Database Service : bases de données relationnelles managées.",
    "KMS": "Key Management Service : création et gestion des clés de chiffrement.",
    "IaaS": "Infrastructure as a Service : location de l'infrastructure (calcul, réseau, stockage).",
    "PaaS": "Platform as a Service : on déploie son code, AWS gère la plateforme sous-jacente.",
    "SaaS": "Software as a Service : application prête à l'emploi consommée telle quelle.",
    "SLA": "Service Level Agreement : engagement contractuel de niveau de service (disponibilité).",
    "TAM": "Technical Account Manager : accompagnateur technique dédié (plan de support Enterprise).",
    "AZ": "Availability Zone : zone de disponibilité isolée à l'intérieur d'une Région.",
    "CDN": "Content Delivery Network : réseau de diffusion de contenu (Amazon CloudFront).",
}


@mcp.tool()
def glossaire_aws(terme: str) -> str:
    """Donne la définition courte d'un terme, service ou acronyme AWS (vocabulaire
    de la certification Cloud Practitioner). Exemples : IAM, EC2, S3, VPC, IaaS."""
    cle = terme.strip().upper()
    for k in GLOSSAIRE:
        if k.upper() == cle:
            return f"{k} — {GLOSSAIRE[k]}"
    return (
        f"Terme inconnu : {terme}. "
        f"Termes disponibles : {', '.join(GLOSSAIRE)}."
    )


if __name__ == "__main__":
    mcp.run()  # transport stdio par défaut
