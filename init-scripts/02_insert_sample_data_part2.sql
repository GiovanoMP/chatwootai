-- Inserção de dados de exemplo para empresa de cosméticos
-- Parte 2: Proteção Solar, Máscaras Faciais e Serviços

-- Inserir produtos - Categoria: Proteção Solar Facial
INSERT INTO products (name, description, category_id, price, cost, sku, ingredients, benefits, usage_instructions, active) VALUES 
('Protetor Solar Facial FPS 50', 'Protetor solar facial com FPS 50 e proteção UVA/UVB para uso diário', 9, 89.90, 32.60, 'PROT-50-001', 'Aqua, Homosalate, Ethylhexyl Salicylate, Butyl Methoxydibenzoylmethane, Octocrylene, Ethylhexyl Triazone, Glycerin, Silica, Cetearyl Alcohol, Ceteareth-20, Phenoxyethanol, Parfum, Carbomer, Sodium Hydroxide, Disodium EDTA, Tocopheryl Acetate', 'Proteção UVA/UVB, previne o fotoenvelhecimento, textura leve, não deixa resíduo branco', 'Aplique generosamente sobre a pele do rosto 15-30 minutos antes da exposição solar. Reaplicar a cada 2 horas ou após nadar ou transpirar.', TRUE),

('Protetor Solar Facial com Cor FPS 30', 'Protetor solar facial com cor e FPS 30 para uniformizar o tom da pele', 9, 94.90, 34.80, 'PROT-COR-002', 'Aqua, Homosalate, Ethylhexyl Salicylate, Butyl Methoxydibenzoylmethane, Octocrylene, Glycerin, CI 77891, CI 77492, CI 77491, CI 77499, Silica, Cetearyl Alcohol, Ceteareth-20, Phenoxyethanol, Parfum, Carbomer, Sodium Hydroxide, Disodium EDTA, Tocopheryl Acetate', 'Proteção UVA/UVB, uniformiza o tom da pele, disfarça imperfeições, acabamento natural', 'Aplique generosamente sobre a pele do rosto 15-30 minutos antes da exposição solar. Reaplicar a cada 2 horas ou após nadar ou transpirar.', TRUE),

('Protetor Solar Facial Oil-Free FPS 30', 'Protetor solar facial oil-free com FPS 30 para pele oleosa', 9, 84.90, 30.20, 'PROT-OIL-003', 'Aqua, Homosalate, Ethylhexyl Salicylate, Butyl Methoxydibenzoylmethane, Octocrylene, Glycerin, Silica, Dimethicone, Phenoxyethanol, Acrylates/C10-30 Alkyl Acrylate Crosspolymer, Sodium Hydroxide, Disodium EDTA, Tocopheryl Acetate', 'Proteção UVA/UVB, controle da oleosidade, efeito matte, não obstrui os poros', 'Aplique generosamente sobre a pele do rosto 15-30 minutos antes da exposição solar. Reaplicar a cada 2 horas ou após nadar ou transpirar.', TRUE);

-- Inserir produtos - Categoria: Máscaras Faciais
INSERT INTO products (name, description, category_id, price, cost, sku, ingredients, benefits, usage_instructions, active) VALUES 
('Máscara Facial de Argila Verde', 'Máscara facial de argila verde para controle da oleosidade e limpeza profunda', 10, 69.90, 24.80, 'MASC-ARG-001', 'Aqua, Kaolin, Bentonite, Glycerin, Propylene Glycol, Montmorillonite, Aloe Barbadensis Leaf Juice, Chamomilla Recutita Flower Extract, Phenoxyethanol, Ethylhexylglycerin, CI 77289', 'Controle da oleosidade, limpeza profunda dos poros, redução de cravos e espinhas, efeito adstringente', 'Aplique uma camada uniforme sobre a pele limpa e seca, evitando a área dos olhos e lábios. Deixe agir por 15-20 minutos e enxágue com água morna. Use 1-2 vezes por semana.', TRUE),

('Máscara Facial Hidratante de Ácido Hialurônico', 'Máscara facial hidratante com ácido hialurônico para pele desidratada', 10, 74.90, 26.40, 'MASC-AH-002', 'Aqua, Glycerin, Butylene Glycol, Sodium Hyaluronate, Hydrolyzed Sodium Hyaluronate, Sodium Hyaluronate Crosspolymer, Panthenol, Allantoin, Hydroxyethylcellulose, Carbomer, Sodium Hydroxide, Disodium EDTA, Phenoxyethanol, Ethylhexylglycerin', 'Hidratação intensa, preenchimento de linhas finas, efeito plumping, revitaliza a pele desidratada', 'Aplique uma camada uniforme sobre a pele limpa e seca, evitando a área dos olhos e lábios. Deixe agir por 15-20 minutos e remova o excesso com um algodão. Não é necessário enxaguar. Use 2-3 vezes por semana.', TRUE),

('Máscara Facial Esfoliante com AHA', 'Máscara facial esfoliante com ácidos alfa-hidroxiácidos para renovação celular', 10, 79.90, 28.60, 'MASC-AHA-003', 'Aqua, Glycerin, Lactic Acid, Glycolic Acid, Mandelic Acid, Sodium Hydroxide, Xanthan Gum, Aloe Barbadensis Leaf Juice, Panthenol, Allantoin, Disodium EDTA, Phenoxyethanol, Ethylhexylglycerin', 'Renovação celular, uniformização do tom da pele, melhora da textura, luminosidade', 'Aplique uma camada uniforme sobre a pele limpa e seca, evitando a área dos olhos e lábios. Deixe agir por 10-15 minutos e enxágue com água morna. Use 1 vez por semana. Pode causar leve formigamento.', TRUE);

-- Inserir categorias de serviços
INSERT INTO service_categories (name, description) VALUES 
('Tratamentos Faciais', 'Procedimentos estéticos para o rosto'),
('Tratamentos Corporais', 'Procedimentos estéticos para o corpo'),
('Massagens', 'Diferentes tipos de massagens terapêuticas e relaxantes'),
('Depilação', 'Serviços de remoção de pelos'),
('Estética Capilar', 'Tratamentos para os cabelos');

-- Inserir serviços - Categoria: Tratamentos Faciais
INSERT INTO services (name, description, category_id, price, duration, preparation, aftercare, contraindications, active) VALUES 
('Limpeza de Pele Profunda', 'Procedimento completo de limpeza de pele com extração de cravos e impurezas', 1, 180.00, 90, 'Evite o uso de ácidos e retinol 3 dias antes do procedimento. Venha com o rosto limpo, sem maquiagem.', 'Evite exposição solar direta por 24 horas. Não aplique maquiagem nas próximas 12 horas. Mantenha a pele hidratada.', 'Lesões ativas de acne inflamatória, herpes labial ativa, dermatite seborreica em fase aguda, rosácea em fase inflamatória.', TRUE),

('Peeling de Diamante', 'Esfoliação mecânica da pele com ponteira de diamante para renovação celular', 1, 220.00, 60, 'Evite o uso de ácidos e retinol 3 dias antes do procedimento. Venha com o rosto limpo, sem maquiagem.', 'Use protetor solar com FPS 50+ por pelo menos 7 dias. Evite exposição solar direta. Não aplique ácidos ou retinol por 3 dias.', 'Lesões ativas de acne inflamatória, herpes labial ativa, pele muito sensibilizada, rosácea, uso recente de isotretinoína.', TRUE),

('Radiofrequência Facial', 'Tratamento com radiofrequência para estimular o colágeno e melhorar a firmeza da pele', 1, 250.00, 45, 'Venha com o rosto limpo, sem maquiagem. Mantenha-se bem hidratado antes do procedimento.', 'Evite exposição solar direta por 24 horas. Mantenha a pele hidratada. Beba bastante água após o procedimento.', 'Gestantes, marca-passo cardíaco, próteses metálicas na face, câncer de pele, doenças autoimunes em fase aguda.', TRUE),

('Microagulhamento Facial', 'Tratamento com microagulhas para estimular a produção de colágeno e melhorar cicatrizes e estrias', 1, 350.00, 60, 'Evite o uso de ácidos e retinol 7 dias antes do procedimento. Venha com o rosto limpo, sem maquiagem.', 'Use protetor solar com FPS 50+ por pelo menos 30 dias. Evite exposição solar direta. Não aplique ácidos ou retinol por 7 dias. Siga o protocolo de home care recomendado.', 'Lesões ativas de acne inflamatória, herpes labial ativa, pele muito sensibilizada, rosácea, uso recente de isotretinoína, gestantes, doenças autoimunes em fase aguda.', TRUE);

-- Inserir serviços - Categoria: Tratamentos Corporais
INSERT INTO services (name, description, category_id, price, duration, preparation, aftercare, contraindications, active) VALUES 
('Drenagem Linfática Corporal', 'Massagem suave que estimula o sistema linfático para reduzir o inchaço e melhorar a circulação', 2, 150.00, 60, 'Evite refeições pesadas antes do procedimento. Venha com roupas confortáveis.', 'Beba bastante água após o procedimento. Evite alimentos muito salgados nas próximas 24 horas.', 'Trombose venosa profunda, insuficiência cardíaca descompensada, infecções agudas, câncer em tratamento sem liberação médica.', TRUE),

('Tratamento para Celulite', 'Combinação de técnicas para reduzir a aparência da celulite, incluindo radiofrequência e vacuoterapia', 2, 220.00, 75, 'Evite refeições pesadas antes do procedimento. Venha com roupas confortáveis.', 'Beba bastante água após o procedimento. Mantenha a pele hidratada. Siga o protocolo de home care recomendado.', 'Gestantes, varizes muito acentuadas, trombose venosa profunda, infecções cutâneas na área a ser tratada.', TRUE),

('Esfoliação Corporal', 'Tratamento de esfoliação profunda para renovar a pele do corpo, deixando-a macia e renovada', 2, 180.00, 60, 'Evite depilar a área a ser tratada 24 horas antes do procedimento.', 'Mantenha a pele hidratada. Evite exposição solar direta por 48 horas.', 'Lesões cutâneas na área a ser tratada, queimaduras solares, dermatites em fase aguda.', TRUE);

-- Inserir serviços - Categoria: Massagens
INSERT INTO services (name, description, category_id, price, duration, preparation, aftercare, contraindications, active) VALUES 
('Massagem Relaxante', 'Massagem suave com movimentos lentos para promover relaxamento e aliviar o estresse', 3, 120.00, 60, 'Evite refeições pesadas antes do procedimento. Venha com roupas confortáveis.', 'Beba bastante água após o procedimento. Descanse se possível.', 'Febre, infecções cutâneas, lesões musculares agudas sem avaliação médica.', TRUE),

('Massagem Modeladora', 'Massagem vigorosa para modelar o corpo, reduzir medidas e combater a celulite', 3, 150.00, 60, 'Evite refeições pesadas antes do procedimento. Venha com roupas confortáveis.', 'Beba bastante água após o procedimento. Evite alimentos muito salgados nas próximas 24 horas.', 'Varizes muito acentuadas, trombose venosa profunda, gestantes, hipertensão descompensada.', TRUE),

('Massagem com Pedras Quentes', 'Massagem relaxante com pedras vulcânicas aquecidas para aliviar tensões musculares', 3, 180.00, 75, 'Evite refeições pesadas antes do procedimento. Venha com roupas confortáveis. Informe sobre sensibilidade ao calor.', 'Beba bastante água após o procedimento. Descanse se possível.', 'Diabetes descompensada, problemas circulatórios graves, hipertensão descompensada, infecções cutâneas.', TRUE);

-- Inserir profissionais
INSERT INTO professionals (first_name, last_name, email, phone, specialization, bio, active) VALUES 
('Mariana', 'Silva', 'mariana.silva@esteticacosmetica.com.br', '(11) 98765-4321', 'Esteticista Facial', 'Especialista em tratamentos faciais avançados, com mais de 10 anos de experiência. Pós-graduada em Cosmetologia Avançada.', TRUE),

('Carlos', 'Oliveira', 'carlos.oliveira@esteticacosmetica.com.br', '(11) 98765-4322', 'Esteticista Corporal', 'Especialista em tratamentos corporais e massagens, com formação em Fisioterapia Dermatofuncional.', TRUE),

('Juliana', 'Santos', 'juliana.santos@esteticacosmetica.com.br', '(11) 98765-4323', 'Terapeuta Capilar', 'Especialista em tratamentos capilares e tricologia, com formação em Farmácia e especialização em Cosmetologia.', TRUE),

('Rafael', 'Costa', 'rafael.costa@esteticacosmetica.com.br', '(11) 98765-4324', 'Massoterapeuta', 'Especialista em diversas técnicas de massagem, com formação em Fisioterapia e especialização em Terapias Manuais.', TRUE);

-- Associar profissionais a serviços
INSERT INTO professional_services (professional_id, service_id) VALUES 
(1, 1), -- Mariana - Limpeza de Pele Profunda
(1, 2), -- Mariana - Peeling de Diamante
(1, 3), -- Mariana - Radiofrequência Facial
(1, 4), -- Mariana - Microagulhamento Facial
(2, 5), -- Carlos - Drenagem Linfática Corporal
(2, 6), -- Carlos - Tratamento para Celulite
(2, 7), -- Carlos - Esfoliação Corporal
(4, 8), -- Rafael - Massagem Relaxante
(4, 9), -- Rafael - Massagem Modeladora
(4, 10); -- Rafael - Massagem com Pedras Quentes
