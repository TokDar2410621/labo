#!/bin/bash
# Script de lancement de l'interface graphique SalleSense

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         SalleSense - Lancement Interface                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Vérifier si le venv existe
if [ ! -d ".venv" ]; then
    echo "❌ Erreur: Le dossier .venv n'existe pas"
    echo "Créez d'abord l'environnement virtuel avec: python -m venv .venv"
    exit 1
fi

# Activer le venv
echo "✓ Activation de l'environnement virtuel..."
source .venv/bin/activate

# Vérifier si les dépendances sont installées
if ! python -c "import pyodbc" 2>/dev/null; then
    echo "⚠️  Dépendances manquantes, installation..."
    pip install -r requirements.txt
fi

# Lancer l'interface
echo "✓ Lancement de l'interface moderne..."
echo ""
python lancer_interface.py

# Désactiver le venv à la sortie
deactivate
