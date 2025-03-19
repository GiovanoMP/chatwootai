-- Script de inicialização do banco de dados para simulação de ERP
-- Empresa de cosméticos com procedimentos estéticos

-- Tabela de Categorias de Produtos
CREATE TABLE IF NOT EXISTS product_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES product_categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Produtos
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category_id INTEGER REFERENCES product_categories(id),
    price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2),
    sku VARCHAR(50) UNIQUE,
    barcode VARCHAR(50),
    weight DECIMAL(8, 3),
    volume DECIMAL(8, 3),
    ingredients TEXT,
    benefits TEXT,
    usage_instructions TEXT,
    detailed_information TEXT, -- Informações detalhadas em linguagem natural para vetorização
    image_url VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Estoque
CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 0,
    location VARCHAR(100),
    min_quantity INTEGER DEFAULT 0,
    max_quantity INTEGER,
    last_restock_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Categorias de Serviços
CREATE TABLE IF NOT EXISTS service_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Serviços (Procedimentos Estéticos)
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category_id INTEGER REFERENCES service_categories(id),
    price DECIMAL(10, 2) NOT NULL,
    duration INTEGER NOT NULL, -- Duração em minutos
    preparation TEXT,
    aftercare TEXT,
    contraindications TEXT,
    detailed_information TEXT, -- Informações detalhadas em linguagem natural para vetorização
    image_url VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Clientes
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    birth_date DATE,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'Brasil',
    skin_type VARCHAR(50), -- Tipo de pele (seca, oleosa, mista, etc.)
    allergies TEXT,
    preferences TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Pedidos
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, confirmed, shipped, delivered, cancelled
    total_amount DECIMAL(10, 2) NOT NULL,
    shipping_address TEXT,
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(50),
    shipping_postal_code VARCHAR(20),
    shipping_country VARCHAR(50) DEFAULT 'Brasil',
    shipping_method VARCHAR(50),
    tracking_number VARCHAR(100),
    payment_method VARCHAR(50),
    payment_status VARCHAR(50) DEFAULT 'pending', -- pending, paid, failed, refunded
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Itens de Pedido
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    discount DECIMAL(10, 2) DEFAULT 0,
    total_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Agendamentos
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    service_id INTEGER REFERENCES services(id),
    professional_id INTEGER REFERENCES professionals(id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled', -- scheduled, confirmed, completed, cancelled, no-show
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Profissionais
CREATE TABLE IF NOT EXISTS professionals (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    specialization TEXT,
    bio TEXT,
    image_url VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Associação entre Profissionais e Serviços
CREATE TABLE IF NOT EXISTS professional_services (
    professional_id INTEGER REFERENCES professionals(id),
    service_id INTEGER REFERENCES services(id),
    PRIMARY KEY (professional_id, service_id)
);

-- Tabela de Regras de Negócio
CREATE TABLE IF NOT EXISTS business_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL, -- product, service, customer, order, appointment, etc.
    rule_text TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de preços de produtos (histórico e promoções)
CREATE TABLE IF NOT EXISTS product_prices (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    price_type VARCHAR(50) NOT NULL, -- 'regular', 'promotional', 'seasonal', 'wholesale', etc.
    price DECIMAL(10, 2) NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de preços de serviços (histórico e promoções)
CREATE TABLE IF NOT EXISTS service_prices (
    id SERIAL PRIMARY KEY,
    service_id INTEGER REFERENCES services(id),
    price_type VARCHAR(50) NOT NULL, -- 'regular', 'promotional', 'seasonal', 'package', etc.
    price DECIMAL(10, 2) NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para registrar interações com clientes
CREATE TABLE IF NOT EXISTS customer_interactions (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    channel VARCHAR(50) NOT NULL, -- 'whatsapp', 'instagram', 'email', etc.
    interaction_type VARCHAR(50) NOT NULL, -- 'inquiry', 'complaint', 'order', 'appointment', etc.
    content TEXT,
    response TEXT,
    chatwoot_conversation_id VARCHAR(100),
    chatwoot_message_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhorar a performance
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_services_category ON services(category_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_appointments_customer ON appointments(customer_id);
CREATE INDEX idx_appointments_service ON appointments(service_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_business_rules_category ON business_rules(category);
CREATE INDEX idx_product_prices_product ON product_prices(product_id);
CREATE INDEX idx_service_prices_service ON service_prices(service_id);
CREATE INDEX idx_customer_interactions_customer ON customer_interactions(customer_id);

-- Funções para atualizar o timestamp de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para atualizar updated_at automaticamente
CREATE TRIGGER update_product_categories_updated_at BEFORE UPDATE ON product_categories FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_inventory_updated_at BEFORE UPDATE ON inventory FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_service_categories_updated_at BEFORE UPDATE ON service_categories FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_services_updated_at BEFORE UPDATE ON services FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_order_items_updated_at BEFORE UPDATE ON order_items FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_professionals_updated_at BEFORE UPDATE ON professionals FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_business_rules_updated_at BEFORE UPDATE ON business_rules FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_product_prices_updated_at BEFORE UPDATE ON product_prices FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_service_prices_updated_at BEFORE UPDATE ON service_prices FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_customer_interactions_updated_at BEFORE UPDATE ON customer_interactions FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
