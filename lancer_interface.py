#!/usr/bin/env python3
"""
Lanceur principal de l'interface graphique SalleSense MODERNE
Version avec design amélioré
"""

import sys
import tkinter as tk
from tkinter import messagebox


def verifier_dependances():
    """Vérifie que toutes les dépendances sont installées"""
    dependances = {
        'tkinter': 'Interface graphique',
        'pyodbc': 'Connexion base de données'
    }

    manquantes = []

    for module, description in dependances.items():
        try:
            if module == 'tkinter':
                import tkinter
            else:
                __import__(module)
        except ImportError:
            manquantes.append(f"{module} ({description})")

    if manquantes:
        print("❌ Dépendances manquantes:")
        for dep in manquantes:
            print(f"  - {dep}")
        print("\nInstallez les dépendances avec:")
        print("  source venv/bin/activate")
        print("  pip install -r requirements.txt")
        return False

    return True


def main():
    """Fonction principale"""
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║      SalleSense - Interface Graphique MODERNE            ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")

    # Vérifier les dépendances
    if not verifier_dependances():
        return 1

    print("✓ Toutes les dépendances sont installées")
    print("✓ Lancement de l'interface moderne...\n")

    try:
        # Lancer l'interface de connexion moderne
        from interface_connexion import InterfaceConnexionModerne

        app = InterfaceConnexionModerne()
        app.run()

        return 0

    except Exception as e:
        print(f"\n❌ Erreur lors du lancement: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
