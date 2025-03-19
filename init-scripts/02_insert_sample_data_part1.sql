-- Inserção de dados de exemplo para empresa de cosméticos
-- Parte 1: Categorias de Produtos e Produtos

-- Inserir categorias de produtos
INSERT INTO product_categories (name, description, parent_id) VALUES 
('Rosto', 'Produtos para cuidados faciais', NULL),
('Corpo', 'Produtos para cuidados corporais', NULL),
('Cabelo', 'Produtos para cuidados capilares', NULL),
('Maquiagem', 'Produtos de maquiagem', NULL),
('Perfumaria', 'Perfumes e fragrâncias', NULL);

-- Inserir subcategorias de produtos
INSERT INTO product_categories (name, description, parent_id) VALUES 
('Limpeza Facial', 'Produtos para limpeza da pele do rosto', 1),
('Hidratantes Faciais', 'Cremes e loções hidratantes para o rosto', 1),
('Tratamentos Faciais', 'Séruns, ácidos e tratamentos específicos', 1),
('Proteção Solar Facial', 'Protetores solares para o rosto', 1),
('Máscaras Faciais', 'Máscaras para tratamentos faciais', 1),
('Hidratantes Corporais', 'Cremes e loções hidratantes para o corpo', 2),
('Esfoliantes Corporais', 'Produtos para esfoliação corporal', 2),
('Proteção Solar Corporal', 'Protetores solares para o corpo', 2),
('Shampoos', 'Shampoos para diversos tipos de cabelo', 3),
('Condicionadores', 'Condicionadores para diversos tipos de cabelo', 3),
('Máscaras Capilares', 'Tratamentos intensivos para cabelos', 3),
('Óleos Capilares', 'Óleos para tratamento dos fios', 3),
('Base', 'Bases e corretivos', 4),
('Olhos', 'Produtos para maquiagem dos olhos', 4),
('Lábios', 'Produtos para maquiagem dos lábios', 4),
('Perfumes Femininos', 'Fragrâncias para mulheres', 5),
('Perfumes Masculinos', 'Fragrâncias para homens', 5);

-- Inserir produtos - Categoria: Limpeza Facial
INSERT INTO products (name, description, category_id, price, cost, sku, ingredients, benefits, usage_instructions, active) VALUES 
('Gel de Limpeza Facial Pele Oleosa', 'Gel de limpeza facial para pele oleosa com extrato de chá verde e ácido salicílico', 6, 59.90, 22.50, 'GEL-LIMP-001', 'Aqua, Sodium Laureth Sulfate, Cocamidopropyl Betaine, Glycerin, Camellia Sinensis Leaf Extract, Salicylic Acid, Menthol, Sodium Chloride, Citric Acid, Disodium EDTA, Methylchloroisothiazolinone, Methylisothiazolinone, CI 42090', 'Limpa profundamente, remove o excesso de oleosidade, previne cravos e espinhas, ação refrescante', 'Aplique sobre a pele úmida, massageie suavemente e enxágue com água abundante. Use de manhã e à noite.', TRUE),

('Espuma de Limpeza Facial Pele Sensível', 'Espuma de limpeza suave para pele sensível com aloe vera e camomila', 6, 64.90, 24.80, 'ESP-LIMP-002', 'Aqua, Glycerin, Sodium Cocoyl Isethionate, Cocamidopropyl Betaine, Aloe Barbadensis Leaf Juice, Chamomilla Recutita Flower Extract, Panthenol, Allantoin, Sodium PCA, Sodium Chloride, Citric Acid, Disodium EDTA, Phenoxyethanol, Ethylhexylglycerin', 'Limpa suavemente sem ressecar, acalma a pele sensível, reduz vermelhidão, mantém a hidratação natural', 'Aplique sobre a pele úmida, massageie suavemente e enxágue com água abundante. Use de manhã e à noite.', TRUE),

('Sabonete Facial em Barra Pele Seca', 'Sabonete facial em barra para pele seca com manteiga de karité e óleo de amêndoas', 6, 39.90, 12.40, 'SAB-LIMP-003', 'Sodium Palmate, Sodium Palm Kernelate, Aqua, Glycerin, Butyrospermum Parkii Butter, Prunus Amygdalus Dulcis Oil, Sodium Chloride, Tetrasodium EDTA, Tetrasodium Etidronate, CI 77891', 'Limpa sem ressecar, hidrata profundamente, restaura a barreira cutânea, suaviza a pele', 'Aplique sobre a pele úmida, massageie suavemente e enxágue com água abundante. Use de manhã e à noite.', TRUE);

-- Inserir produtos - Categoria: Hidratantes Faciais
INSERT INTO products (name, description, category_id, price, cost, sku, ingredients, benefits, usage_instructions, active) VALUES 
('Creme Hidratante Facial Pele Normal a Seca', 'Creme hidratante facial para pele normal a seca com ácido hialurônico e ceramidas', 7, 89.90, 32.60, 'CREM-HID-001', 'Aqua, Glycerin, Cetearyl Alcohol, Ceteareth-20, Caprylic/Capric Triglyceride, Butyrospermum Parkii Butter, Sodium Hyaluronate, Ceramide NP, Ceramide AP, Ceramide EOP, Cholesterol, Phytosphingosine, Dimethicone, Tocopheryl Acetate, Panthenol, Allantoin, Carbomer, Sodium Hydroxide, Disodium EDTA, Phenoxyethanol, Ethylhexylglycerin, Parfum', 'Hidratação intensa e prolongada, restaura a barreira cutânea, previne ressecamento, deixa a pele macia e suave', 'Aplique sobre a pele limpa e seca, massageando suavemente até completa absorção. Use de manhã e à noite.', TRUE),

('Gel Hidratante Facial Pele Oleosa', 'Gel hidratante facial oil-free para pele oleosa com niacinamida e zinco', 7, 79.90, 28.40, 'GEL-HID-002', 'Aqua, Glycerin, Niacinamide, Dimethicone, Zinc PCA, Sodium Hyaluronate, Hydroxyethylcellulose, Carbomer, Sodium Hydroxide, Disodium EDTA, Phenoxyethanol, Ethylhexylglycerin', 'Hidratação leve sem oleosidade, controla o brilho, reduz poros dilatados, ação matificante', 'Aplique sobre a pele limpa e seca, massageando suavemente até completa absorção. Use de manhã e à noite.', TRUE),

('Loção Hidratante Facial Pele Sensível', 'Loção hidratante facial para pele sensível com aveia coloidal e bisabolol', 7, 84.90, 30.20, 'LOC-HID-003', 'Aqua, Glycerin, Caprylic/Capric Triglyceride, Cetearyl Alcohol, Ceteareth-20, Avena Sativa Kernel Extract, Bisabolol, Panthenol, Allantoin, Tocopheryl Acetate, Dimethicone, Carbomer, Sodium Hydroxide, Disodium EDTA, Phenoxyethanol, Ethylhexylglycerin', 'Hidratação suave, acalma a pele irritada, reduz vermelhidão, fortalece a barreira cutânea', 'Aplique sobre a pele limpa e seca, massageando suavemente até completa absorção. Use de manhã e à noite.', TRUE);

-- Inserir produtos - Categoria: Tratamentos Faciais
INSERT INTO products (name, description, category_id, price, cost, sku, ingredients, benefits, usage_instructions, active) VALUES 
('Sérum Facial Vitamina C', 'Sérum facial com 10% de vitamina C pura para uniformizar o tom da pele', 8, 129.90, 48.60, 'SER-VIT-001', 'Aqua, Ascorbic Acid, Glycerin, Ethoxydiglycol, Propylene Glycol, Panthenol, Tocopheryl Acetate, Sodium Hyaluronate, Ferulic Acid, Sodium Hydroxide, Disodium EDTA, Phenoxyethanol, Ethylhexylglycerin', 'Uniformiza o tom da pele, clareia manchas, estimula a produção de colágeno, ação antioxidante', 'Aplique algumas gotas sobre a pele limpa e seca, pela manhã, antes do hidratante e protetor solar.', TRUE),

('Sérum Facial Ácido Hialurônico', 'Sérum facial com ácido hialurônico de baixo e alto peso molecular para hidratação profunda', 8, 119.90, 42.80, 'SER-AH-002', 'Aqua, Glycerin, Propylene Glycol, Sodium Hyaluronate, Hydrolyzed Sodium Hyaluronate, Sodium Hyaluronate Crosspolymer, Panthenol, Allantoin, Hydroxyethylcellulose, Disodium EDTA, Phenoxyethanol, Ethylhexylglycerin', 'Hidratação profunda e prolongada, preenchimento de linhas finas, efeito plumping, melhora a elasticidade', 'Aplique algumas gotas sobre a pele limpa e seca, de manhã e à noite, antes do hidratante.', TRUE),

('Sérum Facial Retinol', 'Sérum facial com 0.3% de retinol para renovação celular e anti-envelhecimento', 8, 149.90, 56.40, 'SER-RET-003', 'Aqua, Glycerin, Propylene Glycol, Retinol, Sodium Hyaluronate, Tocopheryl Acetate, Panthenol, Allantoin, Hydroxyethylcellulose, Disodium EDTA, Phenoxyethanol, Ethylhexylglycerin', 'Estimula a renovação celular, reduz linhas finas e rugas, uniformiza o tom da pele, melhora a textura', 'Aplique algumas gotas sobre a pele limpa e seca, à noite, antes do hidratante. Comece usando 2-3 vezes por semana e aumente gradualmente.', TRUE);
