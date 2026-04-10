<p align="center">
  <a href="../../README.md">English</a> |
  <a href="README.zh.md">简体中文</a> |
  <a href="README.zht.md">繁體中文</a> |
  <a href="README.ko.md">한국어</a> |
  <a href="README.de.md">Deutsch</a> |
  <a href="README.es.md">Español</a> |
  <a href="README.fr.md">Français</a> |
  <a href="README.it.md">Italiano</a> |
  <a href="README.da.md">Dansk</a> |
  <a href="README.ja.md">日本語</a> |
  <a href="README.pl.md">Polski</a> |
  <a href="README.ru.md">Русский</a> |
  <a href="README.bs.md">Bosanski</a> |
  <a href="README.ar.md">العربية</a> |
  <a href="README.no.md">Norsk</a> |
  <a href="README.br.md">Português (Brasil)</a> |
  <a href="README.th.md">ไทย</a> |
  <a href="README.tr.md">Türkçe</a> |
  <a href="README.uk.md">Українська</a> |
  <a href="README.bn.md">বাংলা</a> |
  <a href="README.gr.md">Ελληνικά</a> |
  <a href="README.vi.md">Tiếng Việt</a> |
  <a href="README.fi.md">Suomi</a> |
  <a href="README.sv.md">Svenska</a>
</p>

<p align="center">
  <img width="4000" height="800" alt="Skene_git" src="https://github.com/user-attachments/assets/2be11c04-6b98-4e26-8905-bf3250c4addb" />
  <a href="https://www.skene.ai"><img width="120" height="42" alt="website" src="https://github.com/user-attachments/assets/8ae8c68f-eeb5-411f-832f-6b6818bd2c34"></a>
  <a href="https://www.skene.ai/resources/docs/skene"><img width="120" height="42" alt="docs" src="https://github.com/user-attachments/assets/f847af52-0f6f-4570-9a48-1b7c8f4f0d7a"></a>
  <a href="https://www.skene.ai/resources/blog"><img width="100" height="42" alt="blog" src="https://github.com/user-attachments/assets/8c62e3b8-39a8-43f6-bb0b-f00b118aff82"></a>
  <a href="https://www.reddit.com/r/plgbuilders/"><img width="153" height="42" alt="reddit" src="https://github.com/user-attachments/assets/b420ea50-26e3-40fe-ab34-ac179f748357"></a>
</p>


Skene est une boite a outils d'analyse de code pour la croissance produit. Il scanne votre code, detecte les opportunites de croissance et genere des plans d'implementation actionnables.

## Demarrage Rapide

Installez et lancez l'interface de terminal interactive :

```bash
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash
skene
```

L'assistant vous guide a travers la selection du fournisseur, l'authentification et l'analyse -- aucune configuration prealable necessaire.

<p align="center">
  <img src="https://github.com/user-attachments/assets/49dcd0c4-2bad-4fd3-b29e-89ba2b85c669" width="100%" height="auto"/>
<p>

## Ce Qu'il Fait

- **Detection de la stack technique** -- identifie les frameworks, bases de donnees, authentification, deploiement
- **Decouverte des fonctionnalites de croissance** -- trouve les flux d'inscription existants, le partage, les invitations, la facturation
- **Registre des fonctionnalites** -- suit les fonctionnalites a travers les executions d'analyse, les relie aux boucles de croissance
- **Analyse des fuites de revenus** -- repere la monetisation manquante et les niveaux de tarification faibles
- **Generation de plans de croissance** -- produit des boucles de croissance priorisees avec des feuilles de route d'implementation
- **Prompts d'implementation** -- construit des prompts prets a l'emploi pour Cursor, Claude ou d'autres outils IA
- **Deploiement de la telemetrie** -- genere des migrations Supabase et les pousse vers l'upstream
- **Validation des boucles** -- verifie que les exigences des boucles de croissance sont implementees
- **Chat interactif** -- posez des questions sur votre code dans le terminal

Compatible avec OpenAI, Gemini, Claude, LM Studio, Ollama et tout endpoint compatible OpenAI. Audit local gratuit disponible sans cle API requise.

<img width="1662" height="393" alt="ide_git" src="https://github.com/user-attachments/assets/0b9de3f8-9083-4dc8-b68e-105abc7ea0b4" />

## Installation

### Interface de Terminal (recommandee)

La TUI est un assistant interactif qui vous guide a travers l'ensemble du flux de travail. Aucun prerequis -- l'installateur gere tout.

```bash
# Installer la TUI
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash

# La lancer
skene
```

### Python CLI

Si vous preferez la ligne de commande, vous pouvez executer Skene directement avec `uvx` (aucune installation necessaire) ou l'installer globalement :

```bash
# Installer uv (si vous ne l'avez pas)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Executer directement (aucune installation necessaire)
uvx skene

# Ou installer globalement
pip install skene
```

Pour les details d'utilisation du CLI, consultez la [documentation](https://www.skene.ai/resources/docs/skene).

## Structure du Monorepo

| Repertoire | Description | Langage | Distribution |
|-----------|-------------|----------|-------------|
| `src/skene/` | CLI + moteur d'analyse | Python | [PyPI](https://pypi.org/project/skene/) |
| `tui/` | Assistant interactif de terminal | Go | [GitHub Releases](https://github.com/SkeneTechnologies/skene/releases) |
| `cursor-plugin/` | Plugin Cursor IDE | — | — |

La TUI (`tui/`) est une application Bubble Tea qui offre une experience d'assistant interactif et orchestre le CLI Python via `uvx`. Chaque package dispose de pipelines CI/CD independants.

## Contribuer

Les contributions sont les bienvenues. Veuillez [ouvrir une issue](https://github.com/SkeneTechnologies/skene/issues) ou soumettre une [pull request](https://github.com/SkeneTechnologies/skene/pulls).

## Licence

[MIT](https://opensource.org/licenses/MIT)

<img width="4000" height="800" alt="Skene_end_git" src="https://github.com/user-attachments/assets/04119cd1-ee00-4902-9075-5fc3e1e5ec48" />
