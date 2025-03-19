#!/usr/bin/env python3
"""
Script para popular o banco de dados com dados de exemplo para testes.
"""

import os
import sys
import random
import logging
from datetime import datetime, timedelta
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SampleDataPopulator")

# Adicionar diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar os serviços de dados
from services.data.data_service_hub import DataServiceHub

def populate_categories(hub):
    """Popula o banco de dados com categorias de exemplo."""
    logger.info("Populando categorias...")
    
    query = """
    INSERT INTO categories (name, description, parent_id)
    VALUES (%(name)s, %(description)s, %(parent_id)s)
    RETURNING id
    """
    
    # Categorias principais
    main_categories = [
        ("Smartphones", "Telefones inteligentes e acessórios"),
        ("Notebooks", "Computadores portáteis para todos os usos"),
        ("Tablets", "Dispositivos portáteis com tela sensível ao toque"),
        ("Acessórios", "Acessórios diversos para dispositivos eletrônicos")
    ]
    
    main_category_ids = {}
    for name, description in main_categories:
        result = hub.execute_query(query, {
            "name": name,
            "description": description,
            "parent_id": None
        }, fetch_all=False)
        main_category_ids[name] = result['id']
    
    # Subcategorias
    subcategories = [
        ("Apple", "Produtos da Apple", main_category_ids["Smartphones"]),
        ("Samsung", "Produtos da Samsung", main_category_ids["Smartphones"]),
        ("Xiaomi", "Produtos da Xiaomi", main_category_ids["Smartphones"]),
        ("Outros", "Outros smartphones", main_category_ids["Smartphones"]),
        
        ("Ultrabooks", "Notebooks ultrafinos", main_category_ids["Notebooks"]),
        ("Gaming", "Notebooks para jogos", main_category_ids["Notebooks"]),
        ("Workstation", "Notebooks para trabalho pesado", main_category_ids["Notebooks"]),
        
        ("Android", "Tablets com Android", main_category_ids["Tablets"]),
        ("iPad", "Tablets da Apple", main_category_ids["Tablets"]),
        
        ("Carregadores", "Carregadores e cabos", main_category_ids["Acessórios"]),
        ("Capas", "Capas e películas", main_category_ids["Acessórios"]),
        ("Fones", "Fones de ouvido e headsets", main_category_ids["Acessórios"]),
        ("Baterias", "Baterias externas", main_category_ids["Acessórios"])
    ]
    
    subcategory_ids = {}
    for name, description, parent_id in subcategories:
        result = hub.execute_query(query, {
            "name": name,
            "description": description,
            "parent_id": parent_id
        }, fetch_all=False)
        subcategory_ids[name] = result['id']
    
    logger.info(f"Categorias populadas: {len(main_categories)} principais, {len(subcategories)} subcategorias")
    return main_category_ids, subcategory_ids

def populate_products(hub, category_ids, subcategory_ids, count=50):
    """Popula o banco de dados com produtos de exemplo."""
    logger.info(f"Populando {count} produtos...")
    
    query = """
    INSERT INTO products (name, description, price, sku, image_url, created_at, updated_at)
    VALUES (%(name)s, %(description)s, %(price)s, %(sku)s, %(image_url)s, %(created_at)s, %(updated_at)s)
    RETURNING id
    """
    
    # Base de produtos
    product_bases = [
        {
            "prefix": "Smartphone",
            "descriptions": [
                "Tela AMOLED de 6.5 polegadas, câmera de 108MP, bateria de 5000mAh",
                "Processador Octa-core, 256GB de armazenamento, 12GB de RAM",
                "Resistente à água, carregamento rápido, sistema operacional Android 13"
            ],
            "price_range": (1499.99, 4999.99),
            "categories": ["Smartphones"],
            "subcategories": ["Samsung", "Apple", "Xiaomi", "Outros"]
        },
        {
            "prefix": "Notebook",
            "descriptions": [
                "Processador Intel Core i7, 16GB RAM, SSD 512GB, Tela 15.6 Full HD",
                "Placa de vídeo dedicada, teclado retroiluminado, bateria de longa duração",
                "Ultrafino, leve e potente para trabalho ou entretenimento"
            ],
            "price_range": (3999.99, 9999.99),
            "categories": ["Notebooks"],
            "subcategories": ["Ultrabooks", "Gaming", "Workstation"]
        },
        {
            "prefix": "Tablet",
            "descriptions": [
                "Tela de 10.5 polegadas, 128GB de armazenamento, processador de alta performance",
                "Ideal para trabalho e entretenimento, suporte a caneta stylus",
                "Bateria de longa duração, conectividade 5G, câmeras de alta resolução"
            ],
            "price_range": (1999.99, 5999.99),
            "categories": ["Tablets"],
            "subcategories": ["Android", "iPad"]
        },
        {
            "prefix": "Fone Bluetooth",
            "descriptions": [
                "Conexão sem fio, bateria de longa duração, cancelamento de ruído",
                "Som de alta definição, microfones integrados, resistente à água",
                "Design ergonômico, controles touch, múltiplas cores disponíveis"
            ],
            "price_range": (199.99, 999.99),
            "categories": ["Acessórios"],
            "subcategories": ["Fones"]
        },
        {
            "prefix": "Carregador Portátil",
            "descriptions": [
                "Capacidade de 10000mAh, carregamento rápido, múltiplas portas",
                "Design compacto, indicador LED, compatibilidade universal",
                "Proteção contra sobrecarga, ideal para viagens e uso diário"
            ],
            "price_range": (89.99, 299.99),
            "categories": ["Acessórios"],
            "subcategories": ["Carregadores", "Baterias"]
        }
    ]
    
    product_ids = []
    
    for i in range(count):
        # Selecionar uma base de produto aleatória
        product_base = random.choice(product_bases)
        
        # Criar um nome único
        model = f"X{random.randint(1, 9)}{random.choice(['Pro', 'Plus', 'Max', 'Air', 'Ultra'])}"
        year = random.choice(["2023", "2024", "2025"])
        name = f"{product_base['prefix']} {model} {year}"
        
        # Selecionar descrição
        description = random.choice(product_base['descriptions'])
        
        # Gerar preço
        min_price, max_price = product_base['price_range']
        price = round(random.uniform(min_price, max_price), 2)
        
        # Gerar SKU
        sku = f"{product_base['prefix'][:3].upper()}-{model}-{random.randint(1000, 9999)}"
        
        # Data de criação/atualização aleatória nos últimos 6 meses
        days_ago = random.randint(0, 180)
        created_at = datetime.now() - timedelta(days=days_ago)
        updated_at = created_at + timedelta(days=random.randint(0, days_ago))
        
        # Inserir produto
        result = hub.execute_query(query, {
            "name": name,
            "description": description,
            "price": price,
            "sku": sku,
            "image_url": f"https://example.com/images/products/{sku.lower()}.jpg",
            "created_at": created_at,
            "updated_at": updated_at
        }, fetch_all=False)
        
        product_id = result['id']
        product_ids.append(product_id)
        
        # Associar a categorias
        category_name = random.choice(product_base['categories'])
        subcategory_name = random.choice(product_base['subcategories'])
        
        category_query = """
        INSERT INTO product_categories (product_id, category_id)
        VALUES (%(product_id)s, %(category_id)s)
        """
        
        # Categoria principal
        hub.execute_query(category_query, {
            "product_id": product_id,
            "category_id": category_ids[category_name]
        })
        
        # Subcategoria
        hub.execute_query(category_query, {
            "product_id": product_id,
            "category_id": subcategory_ids[subcategory_name]
        })
        
        # Adicionar atributos
        attributes = []
        
        if "Smartphone" in name or "Tablet" in name:
            attributes.extend([
                ("color", random.choice(["Preto", "Branco", "Azul", "Vermelho", "Verde"])),
                ("storage", random.choice(["64GB", "128GB", "256GB", "512GB", "1TB"])),
                ("ram", random.choice(["4GB", "6GB", "8GB", "12GB", "16GB"])),
                ("network", random.choice(["4G", "5G"]))
            ])
        elif "Notebook" in name:
            attributes.extend([
                ("processor", random.choice(["Intel Core i5", "Intel Core i7", "Intel Core i9", "AMD Ryzen 5", "AMD Ryzen 7"])),
                ("ram", random.choice(["8GB", "16GB", "32GB", "64GB"])),
                ("storage", random.choice(["256GB SSD", "512GB SSD", "1TB SSD", "2TB SSD"])),
                ("graphics", random.choice(["Integrada", "NVIDIA GTX 1650", "NVIDIA RTX 3050", "NVIDIA RTX 3060", "AMD Radeon"]))
            ])
        elif "Fone" in name:
            attributes.extend([
                ("color", random.choice(["Preto", "Branco", "Azul", "Vermelho", "Rosa"])),
                ("battery", random.choice(["8h", "12h", "24h", "36h"])),
                ("type", random.choice(["In-ear", "Over-ear", "On-ear", "True Wireless"]))
            ])
        elif "Carregador" in name:
            attributes.extend([
                ("capacity", random.choice(["5000mAh", "10000mAh", "20000mAh"])),
                ("ports", random.choice(["1 USB-C", "2 USB-A + 1 USB-C", "3 USB-A"])),
                ("fast_charging", random.choice(["Sim", "Não"]))
            ])
        
        # Salvar atributos
        attribute_query = """
        INSERT INTO product_attributes (product_id, attribute_name, attribute_value)
        VALUES (%(product_id)s, %(attribute_name)s, %(attribute_value)s)
        """
        
        for name, value in attributes:
            hub.execute_query(attribute_query, {
                "product_id": product_id,
                "attribute_name": name,
                "attribute_value": value
            })
        
        # Adicionar ao inventário
        inventory_query = """
        INSERT INTO inventory (product_id, quantity, status)
        VALUES (%(product_id)s, %(quantity)s, %(status)s)
        """
        
        quantity = random.randint(0, 100)
        status = "in_stock" if quantity > 0 else "out_of_stock"
        
        hub.execute_query(inventory_query, {
            "product_id": product_id,
            "quantity": quantity,
            "status": status
        })
    
    logger.info(f"Produtos populados: {len(product_ids)}")
    return product_ids

def populate_customers(hub, count=20):
    """Popula o banco de dados com clientes de exemplo."""
    logger.info(f"Populando {count} clientes...")
    
    query = """
    INSERT INTO customers (first_name, last_name, email, phone, username, external_id, avatar_url, created_at, updated_at)
    VALUES (%(first_name)s, %(last_name)s, %(email)s, %(phone)s, %(username)s, %(external_id)s, %(avatar_url)s, %(created_at)s, %(updated_at)s)
    RETURNING id
    """
    
    # Nomes e sobrenomes para gerar clientes
    first_names = [
        "Ana", "Bruno", "Carla", "Daniel", "Eduarda", "Felipe", "Gabriela", "Henrique", 
        "Isabela", "João", "Karina", "Lucas", "Mariana", "Nelson", "Olivia", "Paulo", 
        "Quiteria", "Rafael", "Sandra", "Thiago", "Ursula", "Vitor", "Wanda", "Xavier", 
        "Yasmin", "Zélio"
    ]
    
    last_names = [
        "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Almeida", "Pereira",
        "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Alves", "Araújo",
        "Monteiro", "Barbosa", "Dias", "Mendes", "Castro", "Fernandes", "Cardoso", "Teixeira"
    ]
    
    customer_ids = []
    
    for i in range(count):
        # Gerar dados do cliente
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        # Criar email único
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@example.com"
        
        # Criar telefone
        phone = f"+55{random.randint(11, 99)}{random.randint(10000000, 99999999)}"
        
        # Username e ID externo
        username = f"{first_name.lower()}{random.randint(1, 999)}"
        external_id = f"CRM-{random.randint(10000, 99999)}"
        
        # Data de criação/atualização aleatória nos últimos 2 anos
        days_ago = random.randint(0, 730)
        created_at = datetime.now() - timedelta(days=days_ago)
        updated_at = created_at + timedelta(days=random.randint(0, days_ago))
        
        # Inserir cliente
        result = hub.execute_query(query, {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "username": username,
            "external_id": external_id,
            "avatar_url": f"https://example.com/images/avatars/{username}.jpg",
            "created_at": created_at,
            "updated_at": updated_at
        }, fetch_all=False)
        
        customer_id = result['id']
        customer_ids.append(customer_id)
        
        # Adicionar endereços (1-3 por cliente)
        address_count = random.randint(1, 3)
        for j in range(address_count):
            is_default = (j == 0)  # O primeiro endereço é o padrão
            address_type = random.choice(["shipping", "billing", "both"])
            
            address_query = """
            INSERT INTO customer_addresses 
            (customer_id, address_line1, address_line2, city, state, postal_code, country, is_default, address_type)
            VALUES 
            (%(customer_id)s, %(address_line1)s, %(address_line2)s, %(city)s, %(state)s, %(postal_code)s, %(country)s, %(is_default)s, %(address_type)s)
            """
            
            hub.execute_query(address_query, {
                "customer_id": customer_id,
                "address_line1": f"Rua {random.randint(1, 999)}, {random.randint(1, 999)}",
                "address_line2": f"Apto {random.randint(1, 999)}" if random.random() > 0.5 else None,
                "city": random.choice(["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Curitiba", "Salvador", "Fortaleza"]),
                "state": random.choice(["SP", "RJ", "MG", "PR", "BA", "CE"]),
                "postal_code": f"{random.randint(10000, 99999)}-{random.randint(100, 999)}",
                "country": "Brasil",
                "is_default": is_default,
                "address_type": address_type
            })
        
        # Adicionar preferências
        preferences = [
            ("preferred_contact", random.choice(["email", "phone", "whatsapp"])),
            ("preferred_payment", random.choice(["credit_card", "debit_card", "pix", "bank_transfer"])),
            ("marketing_opt_in", random.choice(["yes", "no"])),
            ("theme", random.choice(["light", "dark", "system"])),
            ("language", random.choice(["pt_BR", "en_US", "es_ES"]))
        ]
        
        pref_query = """
        INSERT INTO customer_preferences (customer_id, preference_key, preference_value)
        VALUES (%(customer_id)s, %(preference_key)s, %(preference_value)s)
        """
        
        for key, value in preferences:
            hub.execute_query(pref_query, {
                "customer_id": customer_id,
                "preference_key": key,
                "preference_value": value
            })
    
    logger.info(f"Clientes populados: {len(customer_ids)}")
    return customer_ids

def populate_conversations(hub, customer_ids, product_ids, count=30):
    """Popula o banco de dados com conversas de exemplo."""
    logger.info(f"Populando {count} conversas...")
    
    # Templates de mensagens
    customer_messages = [
        "Olá, gostaria de mais informações sobre {product}",
        "Qual é o preço do {product}?",
        "Vocês entregam {product} em {city}?",
        "O {product} está disponível em estoque?",
        "Qual é o prazo de entrega para {product}?",
        "Estou tendo problemas com meu {product}",
        "Quero comprar o {product}, posso pagar com {payment}?",
        "O {product} tem garantia de quanto tempo?",
        "Vocês têm {product} na cor {color}?",
        "Qual a diferença entre o {product} e o {product2}?"
    ]
    
    agent_messages = [
        "Olá! Como posso ajudar você hoje?",
        "Claro, o preço do {product} é R$ {price}",
        "Sim, entregamos em {city}. O prazo é de {delivery} dias úteis",
        "Verificando em nosso estoque... Sim, temos {product} disponível!",
        "Entendo sua dúvida. O {product} possui as seguintes características: {features}",
        "Sinto muito pelo problema com seu {product}. Poderia detalhar mais o que está acontecendo?",
        "Sim, aceitamos pagamento via {payment} para o {product}",
        "O {product} tem garantia de 12 meses pelo fabricante",
        "Atualmente temos o {product} disponível nas cores: {colors}",
        "Há algo mais em que eu possa ajudar?"
    ]
    
    cities = ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Curitiba", "Salvador", "Fortaleza"]
    colors = ["preto", "branco", "azul", "vermelho", "verde", "dourado", "prata", "cinza"]
    payments = ["cartão de crédito", "cartão de débito", "PIX", "boleto", "transferência bancária"]
    
    conversation_ids = []
    
    for i in range(count):
        # Criar conversa
        customer_id = random.choice(customer_ids)
        product_id = random.choice(product_ids)
        
        # Obter nome do produto
        product_query = "SELECT name, price FROM products WHERE id = %(product_id)s"
        product = hub.execute_query(product_query, {"product_id": product_id}, fetch_all=False)
        product_name = product['name']
        product_price = product['price']
        
        # Criar ID único para conversa
        conversation_id = f"conv-{random.randint(100000, 999999)}"
        
        # Data de início (últimos 30 dias)
        days_ago = random.randint(0, 30)
        start_time = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        
        # Criar contexto de conversa
        context_query = """
        INSERT INTO conversation_contexts (conversation_id, customer_id, agent_id, status, metadata, created_at, updated_at)
        VALUES (%(conversation_id)s, %(customer_id)s, %(agent_id)s, %(status)s, %(metadata)s, %(created_at)s, %(updated_at)s)
        """
        
        status = random.choice(["active", "closed", "pending"])
        agent_id = f"agent-{random.randint(1, 10)}"
        
        metadata = {
            "channel": random.choice(["whatsapp", "web", "messenger", "instagram"]),
            "product_id": product_id,
            "initial_intent": random.choice(["product_inquiry", "support", "sales", "complaint", "general"])
        }
        
        hub.execute_query(context_query, {
            "conversation_id": conversation_id,
            "customer_id": customer_id,
            "agent_id": agent_id,
            "status": status,
            "metadata": json.dumps(metadata),
            "created_at": start_time,
            "updated_at": start_time + timedelta(minutes=random.randint(5, 60))
        })
        
        conversation_ids.append(conversation_id)
        
        # Adicionar mensagens (3-10 por conversa)
        message_count = random.randint(3, 10)
        current_time = start_time
        
        for j in range(message_count):
            # Alternar entre cliente e agente
            is_customer = (j % 2 == 0)
            
            if is_customer:
                msg_template = random.choice(customer_messages)
                
                # Segunda referência a produto (para comparações)
                other_product = hub.execute_query(
                    "SELECT name FROM products WHERE id != %(product_id)s ORDER BY RANDOM() LIMIT 1",
                    {"product_id": product_id},
                    fetch_all=False
                )
                other_product_name = other_product['name'] if other_product else "produto similar"
                
                # Formatar mensagem
                message = msg_template.format(
                    product=product_name,
                    product2=other_product_name,
                    city=random.choice(cities),
                    color=random.choice(colors),
                    payment=random.choice(payments)
                )
                
                sender_id = f"customer-{customer_id}"
                sender_type = "customer"
            else:
                msg_template = random.choice(agent_messages)
                
                # Formatar mensagem
                message = msg_template.format(
                    product=product_name,
                    price=f"{product_price:.2f}",
                    city=random.choice(cities),
                    delivery=random.randint(2, 15),
                    features=f"Tela de alta definição, {random.randint(64, 512)}GB de armazenamento, processador avançado",
                    colors=", ".join(random.sample(colors, random.randint(2, 5))),
                    payment=random.choice(payments)
                )
                
                sender_id = agent_id
                sender_type = "agent"
            
            # Adicionar algum tempo entre mensagens
            current_time += timedelta(minutes=random.randint(1, 10))
            
            # Adicionar mensagem
            message_query = """
            INSERT INTO conversation_messages (conversation_id, sender_id, sender_type, content, metadata, created_at)
            VALUES (%(conversation_id)s, %(sender_id)s, %(sender_type)s, %(content)s, %(metadata)s, %(created_at)s)
            """
            
            hub.execute_query(message_query, {
                "conversation_id": conversation_id,
                "sender_id": sender_id,
                "sender_type": sender_type,
                "content": message,
                "metadata": json.dumps({}),
                "created_at": current_time
            })
        
        # Adicionar variáveis de contexto
        variables = [
            ("viewed_products", json.dumps([product_id])),
            ("last_action", random.choice(["product_info", "price_check", "support_request"])),
            ("sentiment", random.choice(["positive", "neutral", "negative"])),
            ("user_location", random.choice(cities))
        ]
        
        var_query = """
        INSERT INTO conversation_variables (conversation_id, variable_key, variable_value)
        VALUES (%(conversation_id)s, %(variable_key)s, %(variable_value)s)
        """
        
        for key, value in variables:
            hub.execute_query(var_query, {
                "conversation_id": conversation_id,
                "variable_key": key,
                "variable_value": value
            })
    
    logger.info(f"Conversas populadas: {len(conversation_ids)}")
    return conversation_ids

def create_tables(hub):
    """Cria as tabelas necessárias para o banco de dados."""
    logger.info("Criando tabelas no banco de dados...")
    
    # Tabela de categorias
    hub.execute_query("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        parent_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES categories(id)
    )
    """)
    
    # Tabela de produtos
    hub.execute_query("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        price DECIMAL(10, 2) NOT NULL,
        sku VARCHAR(100) UNIQUE,
        image_url VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Tabela de relacionamento produtos-categorias
    hub.execute_query("""
    CREATE TABLE IF NOT EXISTS product_categories (
        product_id INTEGER,
        category_id INTEGER,
        PRIMARY KEY (product_id, category_id),
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
    )
    """)
    
    # Tabela de clientes
    hub.execute_query("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        email VARCHAR(255) UNIQUE,
        phone VARCHAR(20),
        address TEXT,
        city VARCHAR(100),
        state VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Tabela de conversas
    hub.execute_query("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        status VARCHAR(50) DEFAULT 'open',
        channel VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    )
    """)
    
    # Tabela de mensagens de conversas
    hub.execute_query("""
    CREATE TABLE IF NOT EXISTS conversation_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        sender_id INTEGER,
        sender_type VARCHAR(50),
        content TEXT,
        metadata TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
    )
    """)
    
    # Tabela de variáveis de contexto de conversas
    hub.execute_query("""
    CREATE TABLE IF NOT EXISTS conversation_variables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        variable_key VARCHAR(100),
        variable_value TEXT,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
    )
    """)
    
    logger.info("Tabelas criadas com sucesso")

def main():
    """Função principal."""
    try:
        # Inicializar hub de serviços
        logger.info("Inicializando DataServiceHub...")
        hub = DataServiceHub()
        
        # Verificar conexão ativa (PostgreSQL ou SQLite)
        logger.info(f"Status das conexões - Dev Mode: {hub.dev_mode}, SQLite: {'Conectado' if hub.sqlite_conn else 'Desconectado'}, PostgreSQL: {'Conectado' if hub.pg_conn else 'Desconectado'}")
        
        # Verificar se temos alguma conexão de banco de dados ativa
        if not hub.pg_conn and not hub.sqlite_conn:
            logger.error("Não foi possível conectar a nenhum banco de dados. Abortando.")
            sys.exit(1)
        
        # Se estiver usando SQLite, criar as tabelas necessárias
        if hub.dev_mode and hub.sqlite_conn:
            logger.info("Modo de desenvolvimento detectado. Criando tabelas no SQLite...")
            create_tables(hub)
        
        # Testar a conexão com o banco de dados
        logger.info("Testando conexão com o banco de dados...")
        test_result = hub.execute_query("SELECT 1 as test")
        if not test_result:
            logger.error("Falha ao executar consulta de teste no banco de dados.")
            sys.exit(1)
        logger.info("Conexão com banco de dados testada com sucesso!")
        
        # Popula dados de exemplo
        main_category_ids, subcategory_ids = populate_categories(hub)
        product_ids = populate_products(hub, main_category_ids, subcategory_ids)
        customer_ids = populate_customers(hub)
        conversation_ids = populate_conversations(hub, customer_ids, product_ids)
        
        logger.info("População de dados concluída com sucesso!")
        
        # Fechar conexões
        hub.close()
    
    except Exception as e:
        logger.error(f"Erro durante a população de dados: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
