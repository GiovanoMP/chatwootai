# Situação Atual, Desafios e Próximos Passos - CrewAI & Qdrant

## Resumo da Situação Atual

- O pipeline de busca vetorial está funcional: perguntas feitas no chat são processadas, embeddings são gerados e buscas são realizadas no Qdrant.
- O campo `processed_text` dos documentos é acessado corretamente, evitando respostas `None`.
- O sistema retorna a mensagem padrão quando não encontra informações relevantes.

## Testes Realizados

- **Testes automatizados**: Passaram integração, latência e contexto compartilhado. O teste de precisão falhou porque a resposta não continha termos esperados (ex: "promoção").
- **Chat interativo**: Perguntas genéricas (ex: "Boa noite", "Vc tem alguma promoção?") não retornam os documentos esperados, mesmo com os dados corretos no Qdrant.
- **Inspeção dos dados**: O campo `processed_text` está corretamente preenchido e rico em conteúdo, mas as respostas não são recuperadas para perguntas semânticas.

## Desafios Atuais

1. **Similaridade semântica**: Perguntas feitas no chat não estão retornando documentos relevantes, mesmo quando o conteúdo existe no Qdrant.
2. **Granularidade dos embeddings**: Documentos longos e pouco segmentados podem dificultar a busca vetorial.
3. **Alinhamento do modelo de embedding**: É preciso garantir que o mesmo modelo (e idioma) seja usado na indexação e na consulta.
4. **Repetição de documentos**: O módulo do Odoo está enviando 5 vezes os mesmos documentos para a coleção de suporte no Qdrant.
5. **Processamento antecipado**: No módulo Odoo, ao pressionar "Processar Documento", o documento já é enviado para vetorização, mas isso deveria ocorrer apenas ao pressionar "Sincronizar com IA".

## Pontos de Verificação e Ajustes Sugeridos

- [ ] **Verificar no módulo [`addons/business_rules`]** como está sendo feita a geração de embeddings para a documentação de suporte. Garantir que o texto enviado seja segmentado e enriquecido.
- [ ] **Corrigir o fluxo do Odoo**: O envio para vetorização/Qdrant deve ocorrer apenas ao pressionar "Sincronizar com IA", não ao processar localmente.
- [ ] **Evitar duplicidade**: Ajustar o Odoo para não enviar múltiplas vezes o mesmo documento para o Qdrant.
- [ ] **Melhorar granularidade**: Considerar dividir documentos longos em trechos menores antes de enviar para o Qdrant, aumentando a precisão da busca vetorial.
- [ ] **Testar perguntas literais e semânticas**: Validar se perguntas mais próximas do texto original recuperam resultados. Se sim, ajustar embeddings ou segmentação.
- [ ] **Revisar o QdrantTool**: Garantir que o filtro de `account_id` e o modelo de embedding estejam corretos e alinhados com a indexação.

## Próximos Passos

1. Revisar e ajustar a lógica de geração e envio de embeddings no módulo Odoo, especialmente em [`addons/business_rules`].
2. Corrigir o fluxo de sincronização para evitar envios duplicados e garantir que só ocorra ao pressionar "Sincronizar com IA".
3. Testar perguntas mais próximas do conteúdo real dos documentos para validar se a busca vetorial está funcionando.
4. Se necessário, segmentar documentos longos antes de enviar ao Qdrant.
5. Após os ajustes, rodar novamente os testes automatizados e o chat interativo para validar a precisão e relevância das respostas.

---

**Observação:**
Esses pontos são fundamentais para garantir que a CrewAI funcione de forma robusta, precisa e escalável, aproveitando todo o potencial do Qdrant e da arquitetura modular baseada em YAML.
