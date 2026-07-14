"""
Agent ORCHESTRATEUR = le point d'entrée du système multi-agents.

Il reçoit ta question, la décompose, et utilise les 4 briques :
  - Outil natif : l'heure UTC (fonction Python locale)
  - A2A         : délègue les ESTIMATIONS DE COÛTS AWS au worker distant (worker.py)
  - MCP         : appelle l'outil glossaire_aws du serveur mcp_server.py
                  (lancé tout seul en sous-processus, rien à démarrer)
  - RAG         : cherche dans knowledge.md (révisions Cloud Practitioner) via
                  rechercher_documentation

Lancement :
  1) Dans un 1er terminal :  python worker.py
  2) Dans un 2e terminal  :  python main.py "ta question"
"""
import sys
import re
from datetime import datetime, timezone

from strands import Agent, tool
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from strands_tools.a2a_client import A2AClientToolProvider

from config import build_model
from rag import rechercher_documentation


@tool
def heure_utc() -> str:
    """Donne l'heure UTC actuelle au format ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


SYSTEM_PROMPT = (
    "Tu es un orchestrateur multi-agents spécialisé AWS. Utilise le bon outil selon la demande :\n"
    "- une ESTIMATION DE COÛT AWS ou un calcul de facture (prix d'instances EC2, de "
    "stockage S3, de Lambda, de transfert, etc.) -> délègue TOUJOURS à l'agent de coût "
    "via l'outil a2a_send_message, en lui transmettant le service, la durée/quantité ET "
    "la région si l'utilisateur en précise une. Utilise TOUJOURS l'adresse exacte "
    "http://127.0.0.1:9000 comme URL de l'agent. N'invente JAMAIS d'autre URL "
    "(surtout pas example.com). Ne calcule JAMAIS le coût toi-même et n'invente AUCUN "
    "prix ni aucun type d'instance : c'est la réponse de l'agent de coût qui fait foi.\n"
    "- la DÉFINITION d'un terme, service ou acronyme AWS (par exemple IAM, EC2, IaaS) "
    "-> l'outil glossaire_aws\n"
    "- une question de RÉVISION sur AWS ou la certification Cloud Practitioner (concepts "
    "du cloud, sécurité et conformité, technologie et services, facturation, tarification, "
    "support) -> l'outil rechercher_documentation\n"
    "- l'HEURE -> l'outil heure_utc\n"
    "Si la question ne correspond à AUCUNE de ces catégories (par exemple une question "
    "de culture générale ou technique comme le routage OSPF), n'utilise aucun outil et "
    "réponds directement avec tes propres connaissances.\n"
    "RÈGLE DE RELAIS (importante) : quand un outil te renvoie un résultat — en particulier "
    "l'agent de coût via a2a_send_message — extrais l'information utile (le montant en USD, "
    "la définition, le passage) et recopie-la fidèlement. Ignore TOTALEMENT les métadonnées "
    "techniques comme Context ID, Task ID ou l'état de la tâche, et ne décris JAMAIS le "
    "déroulé des échanges entre agents. EN REVANCHE, si l'agent de coût renvoie le détail "
    "du calcul (quantité, prix unitaire, coefficient régional, total) ET que l'utilisateur "
    "a demandé un détail ou une explication, reprends ce calcul chiffré dans ta réponse au "
    "lieu du seul total.\n"
    "Rédige toujours UNE seule réponse finale en français, en phrases normales. "
    "N'écris jamais de balises comme <thinking> ou <response>, ni de JSON brut."
)


def main(question: str) -> None:
    # MCP : on lance mcp_server.py en sous-processus stdio et on récupère ses outils.
    mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(command=sys.executable, args=["mcp_server.py"])
        )
    )

    # A2A : le worker distant (port 9000) est présenté comme un ensemble d'outils.
    a2a = A2AClientToolProvider(known_agent_urls=["http://127.0.0.1:9000"])

    with mcp_client:  # garde le sous-processus MCP vivant le temps de la requête
        mcp_tools = mcp_client.list_tools_sync()

        orchestrateur = Agent(
            model=build_model(),
            system_prompt=SYSTEM_PROMPT,
            tools=[heure_utc, rechercher_documentation, *a2a.tools, *mcp_tools],
        )

        reponse = orchestrateur(question)

        # Nettoyage : certains modèles (Nova) laissent fuiter des balises
        # <thinking>...</thinking> et <response>...</response>. On les enlève.
        texte = str(reponse)
        texte = re.sub(r"<thinking>.*?</thinking>", "", texte, flags=re.DOTALL)
        texte = re.sub(r"</?response>", "", texte).strip()

        print("\n=== Réponse ===")
        print(texte)


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or (
        "Quelle heure est-il en UTC, "
        "combien coûtent 3 instances EC2 t3.micro pendant 730 heures en eu-west-3, "
        "que signifie l'acronyme IAM, "
        "et qu'est-ce que le modèle de responsabilité partagée AWS ?"
    )
    main(q)