#!/usr/bin/env python
"""
Script para executar os testes do sistema.

Este script executa os testes unitários e de integração do sistema.
"""

import os
import sys
import pytest
import argparse

def main():
    """Função principal para executar os testes."""
    parser = argparse.ArgumentParser(description='Executa os testes do sistema.')
    parser.add_argument('--unit', action='store_true', help='Executa apenas os testes unitários')
    parser.add_argument('--integration', action='store_true', help='Executa apenas os testes de integração')
    parser.add_argument('--coverage', action='store_true', help='Gera relatório de cobertura de código')
    parser.add_argument('--verbose', '-v', action='store_true', help='Exibe informações detalhadas')
    
    args = parser.parse_args()
    
    # Diretório base dos testes
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Argumentos para o pytest
    pytest_args = []
    
    # Adicionar diretórios de teste com base nos argumentos
    if args.unit and not args.integration:
        pytest_args.append(os.path.join(test_dir, 'unit'))
    elif args.integration and not args.unit:
        pytest_args.append(os.path.join(test_dir, 'integration'))
    else:
        # Se nenhum ou ambos forem especificados, executar todos os testes
        pytest_args.append(test_dir)
    
    # Adicionar opção de verbose
    if args.verbose:
        pytest_args.append('-v')
    
    # Adicionar opção de cobertura
    if args.coverage:
        pytest_args.extend(['--cov=src', '--cov=odoo_api', '--cov-report=term', '--cov-report=html'])
    
    # Executar os testes
    return pytest.main(pytest_args)

if __name__ == '__main__':
    sys.exit(main())
