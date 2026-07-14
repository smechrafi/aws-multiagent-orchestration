"""
RAG (Retrieval-Augmented Generation) minimal, 100% local.

On lit knowledge.md, on le découpe en passages, et on renvoie les plus pertinents
pour la question. C'est exposé comme un OUTIL que l'agent peut appeler.
"""
from pathlib import Path

from strands import tool

_DOC = Path(__file__).parent / "knowledge.md"
_CHUNKS = [c.strip() for c in _DOC.read_text(encoding="utf-8").split("\n\n") if c.strip()]


@tool
def rechercher_documentation(question: str) -> str:
    """Cherche dans la base de connaissances AWS Certified Cloud Practitioner
    (concepts du cloud, sécurité et conformité, technologie et services cloud,
    facturation, tarification et support) les passages pertinents pour répondre
    à la question."""
    mots = {m for m in question.lower().split() if len(m) > 3}
    classés = sorted(
        _CHUNKS,
        key=lambda c: sum(1 for m in mots if m in c.lower()),
        reverse=True,
    )
    top = [c for c in classés if any(m in c.lower() for m in mots)][:2]
    return "\n---\n".join(top) if top else "Aucun passage pertinent trouvé."
