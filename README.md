# ⚡ MAVERICK J.A.R.V.I.S. - Neural AI Assistant

![Version](https://img.shields.io/badge/version-2.5.0-cyan.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-orange.svg)
![OpenWebUI](https://img.shields.io/badge/Open%20WebUI-Integrated-purple.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Maverick J.A.R.V.I.S.** est un assistant personnel IA inspiré de Tony Stark / J.A.R.V.I.S., doté d'une interface HUD holographique animée (Arc Reactor, télémétrie en temps réel, visualiseur spectral), d'un moteur neuronal local 100% privé via Ollama, d'une synthèse vocale calibrée Iron Man, et d'une intégration transparente avec **Open WebUI**.

---

## 🌟 Fonctionnalités Clés

- 💎 **Interface HUD Holographique Animée :**
  - Réacteur Arc rotatif avec anneaux d'énergie et télémétrie réactive.
  - Onde sonore spectrale synchronisée avec la voix de Maverick.
  - Thème sombre néon cyan & or inspiré de Windows 7 J.A.R.V.I.S. et Iron Man Mark VII.
- 🎙️ **Activation Vocale Mains-Libres ("Hey Mav") :**
  - Détection automatique continue sans clic.
  - Réponse vocale immédiate : *"À votre écoute, patron."*
  - AGC adaptatif (Automatic Gain Control) et gestion anti-conflit matériel (WASAPI Direct + Thread Mutex).
  - Prise en charge bilingue fluide (Français et Anglais).
- 🔊 **Moteur Vocal Double Profil (Iron Man / J.A.R.V.I.S.) :**
  - **Profil J.A.R.V.I.S. :** Timbre flegmatique, mesuré et métallique (Paul Bettany / Jean-Philippe Puymartin).
  - **Profil Tony Stark :** Voix dynamique et chaleureuse.
  - Basculement instantané par commande vocale (*"Mets la voix d'Iron Man"* / *"Mets la voix de Tony Stark"*) ou bouton HUD.
- 🌐 **Studio Open WebUI Intégré :**
  - Switcher en haut du HUD `[ 💎 HUD MAVERICK ]` / `[ 🌐 STUDIO OPEN WEBUI ]`.
  - Contrôle total sur vos modèles Ollama, prompts système, RAG et historiques.
  - Commande vocale directe : *"Hey Mav, ouvre Open WebUI"*.
- 🧠 **Cerveau Local & Outils :**
  - Modèle LLM local via Ollama (Llama 3, Mistral, Qwen, DeepSeek).
  - Mémoire contextuelle à long terme (`memoire.json`).
  - Outils intégrés : Recherche Web, Gestionnaire de fichiers, Intégration Notion & Gmail.

---

## 📁 Architecture du Projet

```
jarvis-personnel/
├── app_neural.py             # Serveur Neural OS (FastAPI + WebSockets + Télémétrie)
├── jarvis.py                 # Moteur logique Maverick, intent routing & wake-word
├── config.py                 # Configuration globale & variables d'environnement
├── requirements.txt          # Dépendances Python
├── MAVERICK.bat              # Lanceur HUD principal en 1 clic
├── MAVERICK_TERMINAL.bat     # Lanceur mode console debug
│
├── tools/                    # Modules & outils de l'assistant
│   ├── voix.py               # Moteur TTS & STT (Edge-TTS prosody + speech_recognition)
│   ├── open_webui_service.py # Supervision & contrôle du service Open WebUI
│   ├── memoire.py            # Persistance de la mémoire contextuelle
│   ├── web.py                # Recherches et scraping web
│   ├── fichiers.py           # Opérations sur le système de fichiers
│   ├── gmail_tools.py        # Connecteur API Gmail
│   └── notion.py             # Connecteur base de connaissances Notion
│
├── ui/                       # Interface HUD Holographique
│   ├── index.html            # Structure HUD, Arc Reactor & Iframe Open WebUI
│   ├── style.css             # Effets néon cyan/gold, animations 3D & shaders
│   ├── script.js             # Logique WebSocket, synthèse audio & switchers
│   └── assets/               # Médias, shaders vidéo & textures HUD
│
├── data/                     # Données persistantes
│   ├── memoire.json          # Souvenirs et préférences utilisateur
│   ├── conversations.json    # Historique des échanges
│   └── documents/            # Documents indexés
│
└── scratch/                  # Scripts de test audio, benchmarks & diagnostics
```

---

## 🚀 Installation & Démarrage Rapide

### 1. Prérequis
- **Windows 10/11** (64-bit)
- **Python 3.10+**
- **Ollama** installé avec un modèle (ex: `ollama pull llama3`)

### 2. Cloner le Dépôt
```bash
git clone https://github.com/<votre-utilisateur>/jarvis-personnel.git
cd jarvis-personnel
```

### 3. Créer l'environnement virtuel & Installer les dépendances
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configuration
Copiez le fichier `.env.example` en `.env` et ajustez les paramètres si nécessaire :
```bash
copy .env.example .env
```

### 5. Démarrage
Double-cliquez simplement sur **`MAVERICK.bat`** ou lancez dans votre terminal :
```bash
python app_neural.py
```
L'interface HUD s'ouvre automatiquement dans votre navigateur à l'adresse : **`http://localhost:8000`**.

---

## 🗣️ Commandes Vocales Exemples

- *"Hey Mav"* ➔ Réveil de l'assistant : *"À votre écoute, patron."*
- *"Quelle heure est-il ?"* / *"Quel temps fait-il à Paris ?"*
- *"Mets la voix d'Iron Man"* / *"Mets la voix de Tony Stark"*
- *"Ouvre Open WebUI"* ➔ Bascule instantanément sur l'interface studio LLM
- *"Rappelle-toi que mon projet s'appelle Mark VII"* ➔ Enregistré dans la mémoire persistante

---

## 🔒 Confidentialité & Sécurité
Toutes les interactions vocales, les prompts et les traitements de données sont exécutés **localement** sur votre machine via Ollama. Aucune donnée privée n'est envoyée vers des serveurs tiers.

---

## 📜 Licence
Distribué sous la licence **MIT**. Voir le fichier `LICENSE` pour plus de détails.
