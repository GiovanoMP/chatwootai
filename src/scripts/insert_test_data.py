#!/usr/bin/env python3
"""
Insert test data script - Insere dados de teste para o sistema.
"""
import os
import sys
import logging
import random
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

# Adicionar o diretório raiz do projeto ao sys.path para poder importar os módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Importar após configurar o sys.path
from src.services.data.data_service_hub import DataServiceHub

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDataInserter:
    """Classe responsável por inserir dados de teste no banco de dados."""
    
    def __init__(self):
        """Inicializa o insersor de dados de teste."""
        # Carregar variáveis de ambiente
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        load_dotenv(env_path)
        print(f"Carregando variáveis de ambiente de: {env_path}")
        
        # Inicializar o hub de serviços de dados
        self.hub = DataServiceHub()
        
        print("\n================================================================================")
        print("INSERÇÃO DE DADOS DE TESTE")
        print("================================================================================\n")
        
    def insert_product_test_data(self):
        """Insere dados de teste para produtos."""
        print("\n### Inserindo dados de teste para produtos ###")
        
        # Atualizar a descrição detalhada de alguns produtos existentes para ajudar na busca vetorial
        update_query = """
            UPDATE products 
            SET detailed_description = %(detailed_description)s
            WHERE id = %(id)s
        """
        
        produtos_atualizados = 0
        
        # Obter ids de produtos existentes
        product_ids_query = "SELECT id, name FROM products ORDER BY id LIMIT 10"
        products = self.hub.execute_query(product_ids_query, {})
        
        if not products or len(products) == 0:
            print("⚠️ Nenhum produto encontrado para atualizar")
            return False
        
        descrições = [
            "Este produto é perfeito para peles sensíveis. Sua fórmula suave limpa profundamente sem ressecar a pele.",
            "Ideal para todos os tipos de pele, este produto hidrata intensamente e protege contra os danos do sol.",
            "Com fórmula exclusiva, este produto combate os sinais de envelhecimento e melhora a elasticidade da pele.",
            "Desenvolvido com ingredientes naturais, este produto nutre a pele e proporciona uma sensação de frescor.",
            "Este produto é essencial para quem busca uma rotina de cuidados completa, pois limpa e hidrata ao mesmo tempo.",
            "Com textura leve e de rápida absorção, este produto é perfeito para uso diário em qualquer estação do ano.",
            "Este produto contém vitaminas essenciais para a saúde da pele, garantindo um aspecto saudável e radiante.",
            "Indicado para peles oleosas, este produto controla a oleosidade sem ressecar, equilibrando a produção de sebo.",
            "Com ação antioxidante, este produto protege a pele contra os radicais livres e previne o envelhecimento precoce.",
            "Este produto possui fórmula hipoalergênica, perfeita para peles sensíveis e propensas a alergias."
        ]
        
        for i, product in enumerate(products):
            try:
                product_id = product['id']
                description = descrições[i % len(descrições)]
                
                # Atualizar descrição detalhada
                self.hub.execute_query(update_query, {
                    'id': product_id,
                    'detailed_description': description
                })
                produtos_atualizados += 1
                print(f"✅ Produto ID {product_id} ({product['name']}) atualizado com sucesso")
            except Exception as e:
                print(f"❌ Erro ao atualizar produto ID {product_id}: {str(e)}")
        
        print(f"\nTotal de produtos atualizados: {produtos_atualizados}")
        return produtos_atualizados > 0
    
    def insert_conversation_context_test_data(self):
        """Insere dados de teste para contextos de conversa."""
        print("\n### Inserindo dados de teste para contextos de conversa ###")
        
        # Verificar se já existem contextos de conversa
        count_query = "SELECT COUNT(*) as count FROM conversation_contexts"
        result = self.hub.execute_query(count_query, {})
        
        if result and result[0]['count'] > 0:
            print(f"⚠️ Já existem {result[0]['count']} contextos de conversa. Pulando inserção.")
            return True
        
        # Obter ids de clientes existentes
        customer_ids_query = "SELECT id FROM customers ORDER BY RANDOM() LIMIT 5"
        customers = self.hub.execute_query(customer_ids_query, {})
        
        if not customers or len(customers) == 0:
            print("❌ Nenhum cliente encontrado para criar contextos de conversa")
            return False
        
        # Inserir contextos de conversa
        insert_context_query = """
            INSERT INTO conversation_contexts 
            (conversation_id, customer_id, agent_id, status, metadata, created_at, updated_at)
            VALUES (%(conversation_id)s, %(customer_id)s, %(agent_id)s, %(status)s, %(metadata)s, %(created_at)s, %(updated_at)s)
            RETURNING id
        """
        
        # Inserir mensagens de conversa
        insert_message_query = """
            INSERT INTO conversation_messages
            (conversation_id, sender_id, sender_type, content, metadata, created_at)
            VALUES (%(conversation_id)s, %(sender_id)s, %(sender_type)s, %(content)s, %(metadata)s, %(created_at)s)
        """
        
        # Inserir variáveis de contexto
        insert_variable_query = """
            INSERT INTO conversation_variables
            (conversation_id, variable_key, variable_value, created_at, updated_at)
            VALUES (%(conversation_id)s, %(variable_key)s, %(variable_value)s, %(created_at)s, %(updated_at)s)
        """
        
        status_options = ['active', 'resolved', 'pending']
        agent_ids = ['agent_001', 'agent_002', 'agent_003', 'agent_004', 'agent_005']
        
        contexts_created = 0
        messages_created = 0
        variables_created = 0
        
        for customer in customers:
            try:
                customer_id = customer['id']
                conversation_id = f"conv_{customer_id}_{int(datetime.now().timestamp())}"
                status = random.choice(status_options)
                agent_id = random.choice(agent_ids)
                created_at = datetime.now() - timedelta(days=random.randint(1, 30))
                updated_at = created_at + timedelta(hours=random.randint(1, 48))
                
                metadata = {
                    'source': random.choice(['whatsapp', 'facebook', 'instagram', 'web']),
                    'channel': random.choice(['messaging', 'chat', 'direct']),
                    'priority': random.choice(['low', 'medium', 'high']),
                    'tags': random.sample(['atendimento', 'vendas', 'suporte', 'informações', 'reclamação'], k=random.randint(1, 3))
                }
                
                # Inserir contexto
                self.hub.execute_query(insert_context_query, {
                    'conversation_id': conversation_id,
                    'customer_id': customer_id,
                    'agent_id': agent_id,
                    'status': status,
                    'metadata': json.dumps(metadata),
                    'created_at': created_at,
                    'updated_at': updated_at
                })
                contexts_created += 1
                
                # Criar algumas mensagens para a conversa
                num_messages = random.randint(3, 10)
                message_time = created_at
                
                customer_messages = [
                    "Olá, gostaria de informações sobre produtos para pele sensível",
                    "Tenho alergia a alguns componentes, vocês podem me ajudar?",
                    "Quais são os ingredientes desse produto?",
                    "Esse produto é testado em animais?",
                    "Qual o prazo de entrega para minha região?",
                    "Vocês têm amostras grátis?",
                    "Esse produto serve para pele oleosa?",
                    "Posso usar este produto durante o dia?",
                    "Quanto custa o frete?",
                    "Vocês têm alguma promoção neste momento?"
                ]
                
                agent_messages = [
                    "Olá! Como posso ajudar você hoje?",
                    "Claro, posso te ajudar com informações sobre nossos produtos.",
                    "Vou verificar essa informação para você.",
                    "Este produto é hipoalergênico e não contém parabenos.",
                    "Não fazemos testes em animais em nenhuma etapa de produção.",
                    "O prazo de entrega para sua região é de 3 a 5 dias úteis.",
                    "Sim, temos amostras grátis em compras acima de R$ 150,00.",
                    "Este produto é ideal para peles oleosas, pois controla a oleosidade.",
                    "O frete é grátis para compras acima de R$ 200,00.",
                    "Sim, temos uma promoção de 20% de desconto em todos os produtos da linha facial."
                ]
                
                for i in range(num_messages):
                    is_customer = i % 2 == 0
                    sender_id = str(customer_id) if is_customer else agent_id
                    sender_type = 'customer' if is_customer else 'agent'
                    content = random.choice(customer_messages if is_customer else agent_messages)
                    
                    message_time += timedelta(minutes=random.randint(1, 15))
                    
                    self.hub.execute_query(insert_message_query, {
                        'conversation_id': conversation_id,
                        'sender_id': sender_id,
                        'sender_type': sender_type,
                        'content': content,
                        'metadata': json.dumps({'read': True, 'source_device': 'mobile' if is_customer else 'web'}),
                        'created_at': message_time
                    })
                    messages_created += 1
                
                # Adicionar algumas variáveis de contexto
                variable_keys = ['last_product_viewed', 'cart_value', 'preferred_payment', 'utm_source', 'last_page_visited']
                variable_values = ['produto-hidratante-facial', '157.90', 'credit_card', 'google', '/produtos/pele']
                
                for i in range(min(len(variable_keys), len(variable_values))):
                    self.hub.execute_query(insert_variable_query, {
                        'conversation_id': conversation_id,
                        'variable_key': variable_keys[i],
                        'variable_value': variable_values[i],
                        'created_at': created_at,
                        'updated_at': updated_at
                    })
                    variables_created += 1
                
                print(f"✅ Contexto de conversa criado para o cliente ID {customer_id} (ID da conversa: {conversation_id})")
                
            except Exception as e:
                print(f"❌ Erro ao criar contexto de conversa para o cliente ID {customer_id}: {str(e)}")
        
        print(f"\nTotal inserido: {contexts_created} contextos, {messages_created} mensagens, {variables_created} variáveis")
        return contexts_created > 0
    
    def insert_conversation_analytics_test_data(self):
        """Insere dados de teste para análise de conversas."""
        print("\n### Inserindo dados de teste para análise de conversas ###")
        
        # Verificar se já existem dados de análise
        count_query = "SELECT COUNT(*) as count FROM conversation_analytics"
        result = self.hub.execute_query(count_query, {})
        
        if result and result[0]['count'] > 0:
            print(f"⚠️ Já existem {result[0]['count']} análises de conversa. Pulando inserção.")
            return True
        
        # Obter contextos de conversa
        contexts_query = """
            SELECT cc.conversation_id, cc.customer_id, COUNT(cm.id) as message_count
            FROM conversation_contexts cc
            JOIN conversation_messages cm ON cc.conversation_id = cm.conversation_id
            GROUP BY cc.conversation_id, cc.customer_id
        """
        
        contexts = self.hub.execute_query(contexts_query, {})
        
        if not contexts or len(contexts) == 0:
            print("❌ Nenhum contexto de conversa encontrado para criar análises")
            return False
        
        # Inserir análises
        insert_analytics_query = """
            INSERT INTO conversation_analytics
            (conversation_id, customer_id, sentiment_score, topics, entities, key_points, duration, message_count, created_at, updated_at)
            VALUES (%(conversation_id)s, %(customer_id)s, %(sentiment_score)s, %(topics)s, %(entities)s, %(key_points)s, %(duration)s, %(message_count)s, %(created_at)s, %(updated_at)s)
        """
        
        analytics_created = 0
        
        for context in contexts:
            try:
                conversation_id = context['conversation_id']
                customer_id = context['customer_id']
                message_count = context['message_count']
                
                # Gerar dados aleatórios para análise
                sentiment_score = round(random.uniform(-1.0, 1.0), 2)
                
                topics = json.dumps([
                    {"name": "produto", "confidence": round(random.uniform(0.7, 0.98), 2)},
                    {"name": "preço", "confidence": round(random.uniform(0.6, 0.95), 2)},
                    {"name": "entrega", "confidence": round(random.uniform(0.5, 0.9), 2)}
                ])
                
                entities = json.dumps([
                    {"type": "product", "name": "hidratante facial", "mentions": random.randint(1, 3)},
                    {"type": "brand", "name": "dermacare", "mentions": random.randint(1, 2)},
                    {"type": "attribute", "name": "hipoalergênico", "mentions": random.randint(1, 2)}
                ])
                
                key_points = json.dumps([
                    "Cliente interessado em produtos para pele sensível",
                    "Cliente mencionou preocupação com ingredientes",
                    "Cliente perguntou sobre prazos de entrega"
                ])
                
                duration = random.randint(300, 1800)  # duração em segundos (5-30 minutos)
                created_at = datetime.now() - timedelta(hours=random.randint(1, 24))
                
                # Inserir análise
                self.hub.execute_query(insert_analytics_query, {
                    'conversation_id': conversation_id,
                    'customer_id': customer_id,
                    'sentiment_score': sentiment_score,
                    'topics': topics,
                    'entities': entities,
                    'key_points': key_points,
                    'duration': duration,
                    'message_count': message_count,
                    'created_at': created_at,
                    'updated_at': created_at
                })
                
                analytics_created += 1
                print(f"✅ Análise criada para a conversa ID {conversation_id}")
                
            except Exception as e:
                print(f"❌ Erro ao criar análise para a conversa ID {conversation_id}: {str(e)}")
        
        print(f"\nTotal de análises criadas: {analytics_created}")
        return analytics_created > 0
    
    def run(self):
        """Executa a inserção de todos os dados de teste."""
        success_count = 0
        
        if self.insert_product_test_data():
            success_count += 1
            
        if self.insert_conversation_context_test_data():
            success_count += 1
            
        if self.insert_conversation_analytics_test_data():
            success_count += 1
            
        print("\n================================================================================")
        print(f"RESULTADO DA INSERÇÃO: {success_count}/3 categorias de dados inseridas com sucesso")
        print("================================================================================")
        
        return success_count == 3

def main():
    """
    Função principal que executa a inserção de dados de teste.
    """
    inserter = TestDataInserter()
    if inserter.run():
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
