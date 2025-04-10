#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import sys

def validate_xml(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        print(f"XML válido: {file_path}")
        return True
    except Exception as e:
        print(f"Erro no XML: {file_path}")
        print(f"Detalhes: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python validate_xml.py <arquivo.xml>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if validate_xml(file_path):
        sys.exit(0)
    else:
        sys.exit(1)
