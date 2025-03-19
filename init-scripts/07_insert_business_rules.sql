-- Inserção de regras de negócio para serviços
-- Este script insere regras de negócio relacionadas a serviços na tabela business_rules

INSERT INTO business_rules (name, description, category, rule_text, active) VALUES 
('Agendamento de Serviços', 'Regras para agendamento de serviços estéticos', 'service', 
'1. Os agendamentos devem ser feitos com pelo menos 24 horas de antecedência.
2. Cancelamentos com menos de 24 horas de antecedência estão sujeitos a uma taxa de 30% do valor do serviço.
3. Reagendamentos são gratuitos se feitos com mais de 24 horas de antecedência.
4. Clientes devem chegar 15 minutos antes do horário agendado para preparação.
5. Para serviços de coloração e tratamentos químicos, é recomendada uma consulta prévia.', 
TRUE),

('Protocolos de Higiene', 'Protocolos de higiene para serviços estéticos', 'service', 
'1. Todos os equipamentos são esterilizados entre cada atendimento.
2. Materiais descartáveis são utilizados sempre que possível.
3. Os profissionais higienizam as mãos antes e depois de cada procedimento.
4. Clientes com infecções cutâneas visíveis podem ter seus procedimentos reagendados.
5. Ambientes são sanitizados regularmente ao longo do dia.', 
TRUE),

('Recomendações Pós-Procedimento', 'Recomendações para clientes após procedimentos estéticos', 'service', 
'1. Evite exposição solar direta por 48 horas após procedimentos faciais.
2. Mantenha a área tratada hidratada conforme orientação do profissional.
3. Não aplique maquiagem por 24 horas após procedimentos invasivos.
4. Em caso de vermelhidão ou inchaço persistente, entre em contato com a clínica.
5. Siga a rotina de cuidados domiciliares recomendada para otimizar resultados.', 
TRUE),

('Política de Descontos', 'Regras para aplicação de descontos em serviços', 'service', 
'1. Clientes frequentes (mais de 5 serviços em 3 meses) recebem 10% de desconto.
2. Pacotes com 3 ou mais sessões do mesmo tratamento têm 15% de desconto.
3. Aniversariantes recebem 20% de desconto em qualquer serviço durante o mês de aniversário.
4. Indicações que resultem em novos clientes geram um crédito de R$ 50,00 para o próximo serviço.
5. Promoções sazonais não são cumulativas com outros descontos.', 
TRUE),

('Contraindicações de Procedimentos', 'Contraindicações para procedimentos estéticos', 'service', 
'1. Gestantes não devem realizar procedimentos com ácidos concentrados ou aparelhos de radiofrequência.
2. Pessoas com doenças autoimunes devem consultar seu médico antes de procedimentos invasivos.
3. Clientes em uso de isotretinoína oral devem aguardar 6 meses após o término do tratamento para realizar peelings químicos.
4. Diabéticos não controlados devem evitar procedimentos que possam comprometer a cicatrização.
5. Pessoas com histórico de queloides devem evitar procedimentos que causem lesões na pele.', 
TRUE),

('Preparação para Procedimentos', 'Instruções de preparação para procedimentos estéticos', 'service', 
'1. Para procedimentos faciais, evite o uso de ácidos na pele por 3 dias antes.
2. Não consuma bebidas alcoólicas 24 horas antes de procedimentos invasivos.
3. Informe ao profissional sobre medicamentos em uso, especialmente anticoagulantes.
4. Para depilação, o comprimento ideal dos pelos é de 0,5cm.
5. Hidrate-se bem no dia anterior a procedimentos de preenchimento.', 
TRUE),

('Política de Garantia', 'Regras de garantia para serviços estéticos', 'service', 
'1. Procedimentos de coloração têm garantia de 7 dias para ajustes de cor.
2. Tratamentos para redução de manchas têm acompanhamento gratuito por 30 dias.
3. Insatisfação com preenchimentos pode ser corrigida em até 14 dias sem custo adicional.
4. Reações alérgicas a produtos utilizados têm atendimento prioritário e gratuito.
5. A garantia não cobre casos onde as instruções pós-procedimento não foram seguidas.', 
TRUE);
