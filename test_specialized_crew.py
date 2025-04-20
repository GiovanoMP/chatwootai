#!/usr/bin/env python
"""
Script para testar a crew especializada.

Este script permite interagir com a crew especializada, fazendo perguntas
e recebendo respostas baseadas nos dados do Qdrant.
"""

import os
import asyncio
import argparse
from typing import Dict, Any
from crew_tests.specialized_crew import SpecializedCrew


def parse_args():
    """
    Analisa os argumentos da linha de comando.
    
    Returns:
        Argumentos analisados
    """
    parser = argparse.ArgumentParser(description="Teste da crew especializada")
    parser.add_argument("--account_id", type=str, default="account_1", help="ID da conta do cliente")
    parser.add_argument("--query", type=str, help="Consulta do usuário")
    return parser.parse_args()


async def main():
    """Função principal."""
    # Analisar argumentos
    args = parse_args()
    
    # Inicializar crew especializada
    crew = SpecializedCrew(account_id=args.account_id)
    
    # Se a consulta foi fornecida como argumento, processá-la
    if args.query:
        result = await crew.process_query(args.query)
        print(f"\nResposta para '{args.query}':\n{result['response']}")
        return
    
    # Caso contrário, iniciar um loop interativo
    print(f"Bem-vindo ao teste da crew especializada para a conta {args.account_id}")
    print("Este chat foi projetado para fornecer APENAS informações factuais baseadas nos dados do Qdrant.")
    print("Digite 'sair' para encerrar o chat")
    print()
    
    # Loop de chat
    while True:
        # Obter consulta do usuário
        query = input("\n\033[1;32mVocê:\033[0m ")
        
        if query.lower() in ["sair", "exit", "quit"]:
            break
        
        # Processar consulta
        print("\n\033[1;33mProcessando...\033[0m")
        result = await crew.process_query(query)
        
        # Exibir resposta
        if 'response_parts' in result and 'resposta' in result['response_parts']:
            # Exibir resposta formatada
            parts = result['response_parts']
            
            # Exibir saudação se disponível
            if 'saudacao' in parts:
                print(f"\n\033[1;36mAtendente:\033[0m {parts.get('saudacao', '')}")
            
            # Exibir resposta
            print(f"\n{parts.get('resposta', '')}")
            
            # Exibir fontes se disponíveis
            if 'fontes' in parts:
                print(f"\n\033[0;90mFontes: {parts.get('fontes', '')}\033[0m")
            
            # Exibir confiança se disponível
            if 'confianca' in parts:
                confianca = parts.get('confianca', '').lower()
                if 'alta' in confianca:
                    print(f"\n\033[0;32mConfiança: {confianca}\033[0m")
                elif 'média' in confianca:
                    print(f"\n\033[0;33mConfiança: {confianca}\033[0m")
                else:
                    print(f"\n\033[0;31mConfiança: {confianca}\033[0m")
        else:
            # Exibir resposta completa
            print(f"\n\033[1;36mAtendente:\033[0m {result['response']}")
    
    print("\nObrigado por usar o teste da crew especializada!")


if __name__ == "__main__":
    asyncio.run(main())
