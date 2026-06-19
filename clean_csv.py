#!/usr/bin/env python3
import csv
import os
import glob
import sys
from pathlib import Path

# Force UTF-8 en sortie
if sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Détecte l'encodage et corrige les CSV
csv_files = glob.glob("backend/questions/**/*.csv", recursive=True)

print(f"Trouve {len(csv_files)} fichiers CSV\n")

for filepath in csv_files:
    print(f"\n{'='*60}")
    print(f"Traitement: {filepath}")
    print(f"{'='*60}")
    
    # Détecte l'encodage
    detected_enc = None
    rows = []
    for enc in ["utf-8", "latin-1", "windows-1252", "iso-8859-1"]:
        try:
            with open(filepath, encoding=enc) as f:
                rows = list(csv.DictReader(f))
            detected_enc = enc
            print(f"OK - Encodage detecte: {enc}")
            break
        except Exception as e:
            continue
    
    if not detected_enc:
        print(f"ERREUR - Impossible de lire le fichier")
        continue
    
    print(f"  Lignes lues: {len(rows)}")
    
    # Détermine le type de questions (standard ou oral)
    is_manche4 = "manche4" in filepath.lower()
    
    if is_manche4:
        # Manche 4: question, reponse_correcte
        fieldnames = ["id", "question", "reponse_correcte"]
    else:
        # Manche 1-3: question, option_a/b/c/d, reponse_correcte
        fieldnames = ["id", "question", "option_a", "option_b", "option_c", "option_d", "reponse_correcte"]
    
    # Nettoie les lignes
    cleaned = []
    ignored = []
    
    for i, row in enumerate(rows, start=1):
        # Force l'ID
        row_id = str(len(cleaned) + 1)
        
        if is_manche4:
            # Manche 4: check reponse_correcte
            reponse = row.get("reponse_correcte", "").strip()
            question = row.get("question", "").strip()
            
            if not reponse or not question:
                ignored.append((i, question[:50] if question else "(vide)"))
                continue
            
            cleaned_row = {
                "id": row_id,
                "question": question,
                "reponse_correcte": reponse,
            }
        else:
            # Manche 1-3: check options et reponse_correcte
            question = row.get("question", "").strip()
            reponse = row.get("reponse_correcte", "").strip()
            
            if not reponse or not question:
                ignored.append((i, question[:50] if question else "(vide)"))
                continue
            
            # Récupère les options
            options = [
                row.get("option_a", "").strip(),
                row.get("option_b", "").strip(),
                row.get("option_c", "").strip(),
                row.get("option_d", "").strip(),
            ]
            
            # Vérifie qu'il y a au moins 2 options
            filled_options = [o for o in options if o]
            if len(filled_options) < 2:
                ignored.append((i, f"{question[:40]} (seulement {len(filled_options)} option(s))"))
                continue
            
            # Vérifie que reponse_correcte est dans les options
            if reponse not in options:
                print(f"  ATTENTION (ligne {i}): reponse '{reponse}' ne correspond pas aux options: {options}")
            
            cleaned_row = {
                "id": row_id,
                "question": question,
                "option_a": options[0],
                "option_b": options[1],
                "option_c": options[2] if len(options) > 2 else "",
                "option_d": options[3] if len(options) > 3 else "",
                "reponse_correcte": reponse,
            }
        
        cleaned.append(cleaned_row)
    
    # Affiche les ignorées
    if ignored:
        print(f"\n  Questions ignores ({len(ignored)}):")
        for line_num, question in ignored:
            print(f"    - Ligne {line_num}: {question}")
    
    # Réécrit en UTF-8
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned)
    
    print(f"\n  OK {len(cleaned)} questions ecrites en UTF-8")
    print(f"    (avant: {len(rows)}, apres nettoyage: {len(cleaned)}, supprimees: {len(ignored)})")

print(f"\n{'='*60}\nCLEANAGE TERMINE\n{'='*60}")
