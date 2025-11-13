#!/usr/bin/env python3
"""
Script de lancement rapide de l'interface SalleSense
Usage: python start.py
"""

import sys
import os

# S'assurer d'être dans le bon répertoire
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Lancer l'interface
from lancer_interface import main

if __name__ == "__main__":
    sys.exit(main())
