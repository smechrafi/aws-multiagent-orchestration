# Système multi-agents AWS (Strands · A2A · MCP · RAG)

[Toujours en cours de développement et d'amélioration]

## Contexte du projet : 

Dans le cadre d'un workshop spécial Donjons & Dragons (DnD) proposé par Amazon Web Services et l'association AWS Student Builder Group @EFREI, nous avions commencé à coder un maître du Jeu capable d'orchestrer plusieurs agents IA, chacun spécialisé dans une tache précise (lancer des dés, vérifier les règles du DnD..)

Mais j'ai eu ensuite une autre idée.. Pourquoi pas reprendre ce projet afin d'avoir plusieurs agents IA qui aide les personnes souhaitant se certifier en technologies AWS (notamment la certification Certified Cloud Practitioner)

Désormais, je souhaite vous présenter un petit système multi-agents en Python qui met en œuvre, sur un cas concret orienté AWS, les quatre briques d'une architecture agentique moderne : orchestration, A2A, MCP et RAG. Il tourne **en local** via Ollama — aucun credential, aucun coût — ou sur **AWS Bedrock** si vous préférez un modèle cloud (payant).

Le principe : vous posez une question en langage naturel, un agent orchestrateur la décompose et appelle lui-même le bon outil — estimer un coût AWS, définir un terme, chercher une fiche de révision ou donner l'heure.

## Les quatre briques

| Concept | Où c'est dans le code | Ce que ça fait |
|---------|-----------------------|----------------|
| Orchestration | `main.py` | L'agent principal reçoit la question et route vers le bon outil |
| A2A (Agent-to-Agent) | `worker.py` | Un second agent autonome, spécialisé dans l'estimation de coûts AWS, appelé par le réseau |
| MCP (Model Context Protocol) | `mcp_server.py` | Un serveur d'outils qui expose un glossaire AWS |
| RAG (Retrieval-Augmented Generation) | `rag.py` + `knowledge.md` | Recherche dans une base de fiches de révision AWS Cloud Practitioner |

Le SDK utilisé partout, c'est [Strands Agents](https://github.com/strands-agents/sdk-python).

## Prérequis (à faire une fois)

1. **Python 3.10+** (par exemple 3.12) : https://www.python.org/downloads
   Important : au moment de l'installation, cochez bien **"Add python.exe to PATH"**.
2. **Ollama**, pour faire tourner l'IA en local : https://ollama.com/download
3. Autoriser l'exécution de scripts PowerShell, puis télécharger le modèle :
   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ollama pull qwen2.5
   ```
   qwen2.5 est bien plus fiable que llama3.1 pour l'appel d'outils, ce qui est indispensable ici (~4,7 Go).

## Installation

Depuis le dossier du projet, dans PowerShell :

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
```

Vous pouvez vérifier qu'Ollama tourne et que le modèle est prêt avant de lancer :

```powershell
python check_ollama.py
```

## Lancement

Il faut **deux terminaux** : le worker A2A est un service réseau qui doit rester actif pendant que l'orchestrateur l'interroge.

Terminal 1 — le worker d'estimation de coûts (laissez-le tourner) :

```powershell
python worker.py
```

Terminal 2 — l'orchestrateur, avec votre question :

```powershell
python main.py "Combien coûtent 3 instances EC2 t3.micro pendant 730 heures en eu-west-3, que signifie IAM, et qu'est-ce que le modèle de responsabilité partagée AWS ?"
```

Le MCP et le RAG tournent tout seuls dans le processus de `main.py` — seul le worker A2A a besoin de sa propre fenêtre.

## Ollama ou Bedrock ?

Au démarrage, le programme demande quel modèle utiliser :

- **Ollama (1)** — local, gratuit, rien à configurer. Utilise qwen2.5 par défaut.
- **Bedrock (2)** — cloud, quelques centimes. Demande la région (défaut `eu-west-3`) et le modèle (défaut Amazon Nova Lite). Nécessite un `aws configure` au préalable ; aucun credential n'est stocké dans le code.

Comme le worker et l'orchestrateur sont deux processus, la question apparaît dans les deux terminaux. Pour ne pas être redemandé, fixez le choix avant de lancer :

```powershell
$env:PROVIDER = "ollama"   # ou "bedrock"
```

## Comment ça marche, en une phrase

`main.py` crée un agent avec une liste d'outils — l'heure (natif), la recherche doc (RAG), le worker distant (A2A) et le glossaire (MCP) — et le modèle décide lui-même lequel appeler pour chaque partie de la question, puis assemble une seule réponse.

## Limites connues

Autant être transparent sur ce qui coince :

- **L'A2A est fragile en local.** L'estimation de coûts passe par un aller-retour entre deux agents LLM ; un petit modèle local (qwen2.5 7B) rate parfois le relais de la réponse et part en vrille. Sur Bedrock, le même code tourne proprement. Le MCP et le RAG, eux, restent stables partout car ce sont de simples appels d'outils à retour propre.
- **Le RAG est lexical, pas sémantique.** Il classe les passages par mots-clés communs, sans embeddings ni base vectorielle. C'est suffisant pour la démo, mais ce n'est pas ce qu'on ferait en production.
- **Les tarifs AWS sont indicatifs.** Les prix et les coefficients par région sont des valeurs simplifiées à but pédagogique, pas la grille réelle d'AWS.

## Structure du projet

| Fichier | Rôle |
|---------|------|
| `main.py` | Orchestrateur (point d'entrée) |
| `worker.py` | Agent A2A d'estimation de coûts AWS |
| `mcp_server.py` | Serveur MCP (glossaire AWS) |
| `rag.py` + `knowledge.md` | RAG sur les fiches Cloud Practitioner |
| `config.py` | Choix du modèle (Ollama / Bedrock) |
| `check_ollama.py` | Vérifie qu'Ollama et le modèle sont prêts |
