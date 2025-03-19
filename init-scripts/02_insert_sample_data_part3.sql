-- Inserção de dados de exemplo para empresa de cosméticos
-- Parte 3: Clientes, Pedidos e Regras de Negócio

-- Inserir clientes
INSERT INTO customers (first_name, last_name, email, phone, birth_date, address, city, state, postal_code, skin_type, allergies, preferences) VALUES 
('Ana', 'Oliveira', 'ana.oliveira@email.com', '(11) 98765-1234', '1985-03-15', 'Rua das Flores, 123', 'São Paulo', 'SP', '01234-567', 'Mista', 'Fragrâncias artificiais', 'Prefere produtos veganos e cruelty-free'),

('Bruno', 'Santos', 'bruno.santos@email.com', '(11) 98765-2345', '1990-07-22', 'Av. Paulista, 1000', 'São Paulo', 'SP', '01310-100', 'Oleosa', 'Nenhuma conhecida', 'Prefere produtos oil-free e com ação matificante'),

('Carla', 'Ferreira', 'carla.ferreira@email.com', '(21) 98765-3456', '1978-11-10', 'Rua do Sol, 456', 'Rio de Janeiro', 'RJ', '20000-000', 'Seca', 'Parabenos', 'Prefere produtos com alta hidratação e sem fragrância'),

('Daniel', 'Lima', 'daniel.lima@email.com', '(31) 98765-4567', '1982-05-20', 'Av. Amazonas, 789', 'Belo Horizonte', 'MG', '30000-000', 'Normal', 'Nenhuma conhecida', 'Prefere produtos práticos e multifuncionais'),

('Elena', 'Costa', 'elena.costa@email.com', '(41) 98765-5678', '1995-09-30', 'Rua das Araucárias, 321', 'Curitiba', 'PR', '80000-000', 'Sensível', 'Álcool, fragrâncias artificiais', 'Prefere produtos hipoalergênicos e calmantes');

-- Inserir pedidos
INSERT INTO orders (customer_id, order_date, status, total_amount, shipping_address, shipping_city, shipping_state, shipping_postal_code, shipping_method, payment_method, payment_status) VALUES 
(1, '2023-06-10 14:30:00', 'delivered', 249.70, 'Rua das Flores, 123', 'São Paulo', 'SP', '01234-567', 'Sedex', 'Cartão de Crédito', 'paid'),
(2, '2023-06-15 10:15:00', 'shipped', 159.80, 'Av. Paulista, 1000', 'São Paulo', 'SP', '01310-100', 'PAC', 'Pix', 'paid'),
(3, '2023-06-20 16:45:00', 'pending', 329.60, 'Rua do Sol, 456', 'Rio de Janeiro', 'RJ', '20000-000', 'Sedex', 'Boleto Bancário', 'pending'),
(4, '2023-06-25 09:00:00', 'confirmed', 199.80, 'Av. Amazonas, 789', 'Belo Horizonte', 'MG', '30000-000', 'PAC', 'Cartão de Crédito', 'paid'),
(5, '2023-06-30 11:30:00', 'delivered', 279.70, 'Rua das Araucárias, 321', 'Curitiba', 'PR', '80000-000', 'Sedex', 'Pix', 'paid');

-- Inserir itens de pedido
INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount, total_price) VALUES 
(1, 1, 1, 59.90, 0.00, 59.90),   -- Ana: Gel de Limpeza Facial Pele Oleosa
(1, 4, 1, 89.90, 0.00, 89.90),   -- Ana: Creme Hidratante Facial Pele Normal a Seca
(1, 7, 1, 99.90, 0.00, 99.90),   -- Ana: Protetor Solar Facial FPS 50

(2, 2, 1, 64.90, 0.00, 64.90),   -- Bruno: Espuma de Limpeza Facial Pele Sensível
(2, 5, 1, 79.90, 0.00, 79.90),   -- Bruno: Gel Hidratante Facial Pele Oleosa
(2, 9, 1, 69.90, 55.00, 14.90),  -- Bruno: Máscara Facial de Argila Verde (com desconto)

(3, 3, 1, 39.90, 0.00, 39.90),   -- Carla: Sabonete Facial em Barra Pele Seca
(3, 6, 1, 84.90, 0.00, 84.90),   -- Carla: Loção Hidratante Facial Pele Sensível
(3, 7, 1, 129.90, 0.00, 129.90), -- Carla: Sérum Facial Vitamina C
(3, 10, 1, 74.90, 0.00, 74.90),  -- Carla: Máscara Facial Hidratante de Ácido Hialurônico

(4, 8, 1, 119.90, 0.00, 119.90), -- Daniel: Sérum Facial Ácido Hialurônico
(4, 9, 1, 84.90, 5.00, 79.90),   -- Daniel: Protetor Solar Facial Oil-Free FPS 30 (com desconto)

(5, 9, 1, 84.90, 0.00, 84.90),   -- Elena: Protetor Solar Facial Oil-Free FPS 30
(5, 10, 1, 74.90, 0.00, 74.90),  -- Elena: Máscara Facial Hidratante de Ácido Hialurônico
(5, 11, 1, 119.90, 0.00, 119.90); -- Elena: Sérum Facial Ácido Hialurônico

-- Inserir agendamentos
INSERT INTO appointments (customer_id, service_id, professional_id, start_time, end_time, status, notes) VALUES 
(1, 1, 1, '2023-07-05 10:00:00', '2023-07-05 11:30:00', 'completed', 'Cliente com muitos cravos na zona T. Recomendado uso de gel de limpeza específico para pele oleosa.'),
(2, 3, 1, '2023-07-06 14:00:00', '2023-07-06 14:45:00', 'completed', 'Cliente com flacidez moderada. Recomendado tratamento com 8 sessões, 1x por semana.'),
(3, 7, 2, '2023-07-07 11:00:00', '2023-07-07 12:00:00', 'completed', 'Cliente com pele muito ressecada. Recomendado uso de hidratante corporal 2x ao dia.'),
(4, 8, 4, '2023-07-10 16:00:00', '2023-07-10 17:00:00', 'scheduled', 'Cliente com dores nas costas devido ao trabalho. Focar na região lombar e cervical.'),
(5, 4, 1, '2023-07-12 09:00:00', '2023-07-12 10:00:00', 'confirmed', 'Primeira sessão de microagulhamento para tratamento de cicatrizes de acne.');

-- Inserir estoque para produtos
INSERT INTO inventory (product_id, quantity, location, min_quantity, max_quantity, last_restock_date) VALUES 
(1, 25, 'Prateleira A1', 10, 50, '2023-06-01'),
(2, 18, 'Prateleira A2', 10, 50, '2023-06-01'),
(3, 30, 'Prateleira A3', 15, 60, '2023-06-01'),
(4, 22, 'Prateleira B1', 10, 40, '2023-06-01'),
(5, 15, 'Prateleira B2', 8, 30, '2023-06-01'),
(6, 20, 'Prateleira B3', 10, 40, '2023-06-01'),
(7, 12, 'Prateleira C1', 5, 25, '2023-06-01'),
(8, 10, 'Prateleira C2', 5, 20, '2023-06-01'),
(9, 28, 'Prateleira D1', 15, 50, '2023-06-01'),
(10, 16, 'Prateleira D2', 8, 30, '2023-06-01'),
(11, 14, 'Prateleira D3', 7, 25, '2023-06-01');

-- Inserir regras de negócio
INSERT INTO business_rules (name, description, category, rule_text, active) VALUES 
('Desconto Primeira Compra', 'Oferecer 10% de desconto na primeira compra de um cliente', 'order', 'Se for a primeira compra do cliente, aplicar 10% de desconto no valor total do pedido.', TRUE),

('Desconto Aniversário', 'Oferecer 15% de desconto para compras realizadas no mês de aniversário do cliente', 'customer', 'Se o mês atual for o mesmo do aniversário do cliente, aplicar 15% de desconto em todos os produtos.', TRUE),

('Programa de Fidelidade', 'Acumular pontos para cada R$ 1,00 gasto e oferecer descontos baseados nos pontos', 'order', 'Para cada R$ 1,00 gasto, o cliente acumula 1 ponto. A cada 100 pontos, o cliente pode trocar por R$ 10,00 de desconto em compras futuras.', TRUE),

('Recomendação de Produtos para Pele Oleosa', 'Regra para recomendar produtos adequados para clientes com pele oleosa', 'product', 'Se o cliente tiver pele oleosa, recomendar produtos oil-free, com ácido salicílico, niacinamida e argilas. Evitar produtos muito oleosos ou oclusivos.', TRUE),

('Recomendação de Produtos para Pele Seca', 'Regra para recomendar produtos adequados para clientes com pele seca', 'product', 'Se o cliente tiver pele seca, recomendar produtos com ácido hialurônico, ceramidas, óleos vegetais e manteigas. Evitar produtos com álcool e adstringentes.', TRUE),

('Recomendação de Produtos para Pele Sensível', 'Regra para recomendar produtos adequados para clientes com pele sensível', 'product', 'Se o cliente tiver pele sensível, recomendar produtos hipoalergênicos, sem fragrância, com ingredientes calmantes como aloe vera, aveia e bisabolol. Evitar produtos com ácidos em alta concentração, álcool e fragrâncias.', TRUE),

('Protocolo de Agendamento', 'Regras para agendamento de procedimentos estéticos', 'appointment', 'Não agendar procedimentos invasivos com menos de 48 horas de antecedência. Exigir consulta prévia para procedimentos como microagulhamento e peelings químicos. Respeitar intervalo mínimo de 15 minutos entre agendamentos.', TRUE),

('Política de Cancelamento', 'Regras para cancelamento de agendamentos', 'appointment', 'Cancelamentos com menos de 24 horas de antecedência estão sujeitos a cobrança de 50% do valor do procedimento. Reagendamentos devem ser feitos com pelo menos 12 horas de antecedência.', TRUE),

('Estoque Mínimo', 'Alerta quando o estoque de um produto atinge o nível mínimo', 'inventory', 'Quando a quantidade em estoque de um produto atingir ou ficar abaixo do nível mínimo definido, gerar um alerta para reposição.', TRUE),

('Desconto por Volume', 'Aplicar desconto progressivo baseado na quantidade de itens do mesmo produto', 'order', 'Para compras de 2 a 3 unidades do mesmo produto, aplicar 5% de desconto. Para 4 a 5 unidades, aplicar 10% de desconto. Para 6 ou mais unidades, aplicar 15% de desconto.', TRUE);

-- Inserir enriquecimento de produtos
INSERT INTO product_enrichment (product_id, source, content_type, content, relevance_score) VALUES 
(7, 'web_search', 'scientific_data', 'Estudos clínicos demonstram que a vitamina C na concentração de 10% é eficaz na redução de manchas e no estímulo da produção de colágeno. Um estudo publicado no Journal of Dermatological Science mostrou redução de 73% na pigmentação após 12 semanas de uso diário.', 0.95),

(7, 'web_search', 'reviews', 'O sérum de vitamina C foi eleito o melhor produto antioxidante de 2023 pela Associação Brasileira de Dermatologia. Consumidores relatam melhora significativa na luminosidade da pele e redução de manchas após 4 semanas de uso.', 0.85),

(8, 'web_search', 'scientific_data', 'O ácido hialurônico de baixo peso molecular penetra mais profundamente na pele, enquanto o de alto peso molecular forma um filme protetor na superfície. A combinação dos dois proporciona hidratação em múltiplas camadas da pele.', 0.90),

(9, 'web_search', 'scientific_data', 'O retinol 0.3% é considerado uma concentração ideal para iniciantes, com eficácia comprovada na redução de linhas finas e melhora da textura da pele, mas com menor risco de irritação comparado a concentrações mais altas.', 0.92),

(9, 'web_search', 'usage_tips', 'Para minimizar a irritação ao iniciar o uso de retinol, aplique o produto em pele completamente seca, comece usando apenas 2-3 vezes por semana, e sempre use protetor solar durante o dia. A técnica de "sandwich" (aplicar hidratante antes e depois do retinol) pode reduzir a irritação.', 0.88);

-- Inserir enriquecimento de serviços
INSERT INTO service_enrichment (service_id, source, content_type, content, relevance_score) VALUES 
(4, 'web_search', 'scientific_data', 'O microagulhamento estimula a produção de colágeno através de microlesões controladas na pele. Um estudo publicado no International Journal of Dermatology mostrou melhora de até 80% na aparência de cicatrizes de acne após 3 sessões.', 0.94),

(4, 'web_search', 'aftercare', 'Após o microagulhamento, é essencial evitar exposição solar, uso de ácidos e retinol por pelo menos 7 dias. A pele pode apresentar vermelhidão e descamação leve nos primeiros 3 dias, o que é considerado normal no processo de cicatrização.', 0.90),

(3, 'web_search', 'scientific_data', 'A radiofrequência facial aquece o tecido dérmico a aproximadamente 40-42°C, temperatura ideal para estimular a contração das fibras de colágeno existentes e iniciar a neocolagênese, processo que continua por até 90 dias após cada sessão.', 0.92),

(6, 'web_search', 'efficacy', 'Estudos clínicos mostram que a combinação de radiofrequência e vacuoterapia pode reduzir em até 40% a aparência da celulite grau 2 após um protocolo de 10 sessões, com resultados visíveis a partir da 4ª sessão.', 0.88),

(10, 'web_search', 'benefits', 'A massagem com pedras quentes combina os benefícios da termoterapia com a massagem manual. O calor das pedras vulcânicas dilata os vasos sanguíneos, melhorando a circulação e facilitando a eliminação de toxinas, além de proporcionar relaxamento muscular profundo.', 0.86);

-- Inserir interações com clientes
INSERT INTO customer_interactions (customer_id, channel, interaction_type, content, response, chatwoot_conversation_id, chatwoot_message_id) VALUES 
(1, 'whatsapp', 'inquiry', 'Olá! Gostaria de saber se vocês têm algum produto específico para pele oleosa com tendência a acne.', 'Olá Ana! Sim, temos várias opções para pele oleosa com tendência a acne. Recomendo especialmente nosso Gel de Limpeza Facial com ácido salicílico e o Sérum de Niacinamida. Você gostaria de mais informações sobre esses produtos?', 'conv_123', 'msg_456'),

(2, 'instagram', 'appointment', 'Quero agendar uma sessão de radiofrequência facial para a próxima semana. Quais horários vocês têm disponíveis?', 'Olá Bruno! Temos horários disponíveis para radiofrequência facial na terça às 10h e 14h, e na quinta às 9h e 16h. Qual seria melhor para você? O procedimento tem duração de 45 minutos.', 'conv_124', 'msg_457'),

(3, 'email', 'complaint', 'Comprei o protetor solar de vocês e ele está deixando minha pele muito oleosa. Não era para ser oil-free?', 'Olá Carla! Lamentamos pelo inconveniente. O protetor solar que você adquiriu é o FPS 50 tradicional, que tem uma formulação mais hidratante. Para peles oleosas, recomendamos nossa versão Oil-Free FPS 30. Podemos fazer a troca do seu produto sem custos adicionais. Por favor, nos informe se gostaria de proceder com a troca.', 'conv_125', 'msg_458'),

(4, 'whatsapp', 'order', 'Quero comprar o sérum de ácido hialurônico. Vocês entregam no centro de BH? Qual o prazo e valor do frete?', 'Olá Daniel! Sim, entregamos no centro de BH. O prazo de entrega é de 2 a 3 dias úteis e o frete custa R$ 12,00. Posso finalizar o pedido para você? Temos promoção de frete grátis para compras acima de R$ 150,00.', 'conv_126', 'msg_459'),

(5, 'instagram', 'inquiry', 'Tenho pele sensível e com rosácea. Quais produtos de vocês são adequados para mim?', 'Olá Elena! Para pele sensível com rosácea, recomendamos produtos sem fragrância e com ingredientes calmantes. Nossa linha de produtos para pele sensível inclui a Espuma de Limpeza com Aloe Vera e Camomila, e a Loção Hidratante com Aveia e Bisabolol. Evite produtos com álcool, ácidos em alta concentração e esfoliantes físicos. Gostaria de mais informações sobre esses produtos?', 'conv_127', 'msg_460');
