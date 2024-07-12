#!/bin/bash

# Name der Python-Datei, die ausgeführt werden soll
PYTHON_FILE="main_gui.py"

# Überprüfen, ob die Python-Datei existiert
if [ -f "$PYTHON_FILE" ]; then
    echo "Starte das Python-Skript: $PYTHON_FILE"
    python3 "$PYTHON_FILE"
else
    echo "Die Datei $PYTHON_FILE wurde nicht gefunden."
    exit 1
fi
