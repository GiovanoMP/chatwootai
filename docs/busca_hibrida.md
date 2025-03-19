# Busca Híbrida: Integrando PostgreSQL e Qdrant

Este documento explica como implementamos a busca híbrida no ChatwootAI, combinando o banco de dados relacional (PostgreSQL) com o banco de dados vetorial (Qdrant) para fornecer resultados de busca relevantes e atualizados.

## O que é Busca Híbrida?

A busca híbrida é uma estratégia que combina duas abordagens diferentes de busca:

1. **Busca Semântica** (Qdrant): Encontra produtos com base na similaridade semântica com a consulta do usuário.
2. **Busca Relacional** (PostgreSQL): Verifica disponibilidade, preço e outras informações estruturadas.

## Por que usar Busca Híbrida?

Imagine o seguinte cenário:

> Um cliente pergunta: "Vocês têm algo para pele oleosa?"

Com a busca híbrida:

1. O sistema primeiro consulta o Qdrant para encontrar produtos semanticamente relacionados a "pele oleosa"
2. Em seguida, verifica no PostgreSQL se esses produtos estão disponíveis em estoque
3. Retorna apenas os produtos que são relevantes E estão disponíveis

Isso garante que o cliente receba recomendações precisas e atualizadas.

## Arquitetura da Solução

Nossa implementação de busca híbrida consiste em três componentes principais:

### 1. Serviço de Embeddings (OpenAI)

Este serviço é responsável por converter textos em vetores (embeddings) que representam seu significado semântico.

```python
# Exemplo simplificado
from openai import OpenAI

client = OpenAI(api_key="sua_chave_api")
embedding = client.embeddings.create(
    model="text-embedding-3-small",
    input="Hidratante para pele oleosa"
).data[0].embedding
```

#### 1.1 Estratégias de Otimização de Custos

Para reduzir os custos associados à geração de embeddings, implementamos várias estratégias de otimização:

##### 1.1.1 Cache de Embeddings

Utilizamos o Redis para armazenar embeddings previamente gerados, evitando chamadas repetidas à API da OpenAI:

```python
# Verificar se o embedding está no cache antes de gerar um novo
cached_embedding = redis_client.get(f"embedding:{text_hash}")
if cached_embedding:
    return json.loads(cached_embedding)
```

##### 1.1.2 Processamento em Lote

Agrupamos múltiplas solicitações de embeddings em uma única chamada de API, reduzindo o número total de chamadas:

```python
# Processar múltiplos textos em uma única chamada
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=batch_texts
)
```

##### 1.1.3 Pré-processamento de Texto

Otimizamos os textos antes de gerar embeddings para reduzir o número de tokens processados:

```python
# Remover espaços extras e limitar o tamanho do texto
text = " ".join(text.strip().split())
if len(text) > 8000:
    text = text[:8000]
```

##### 1.1.4 Monitoramento de Uso e Custos

Implementamos funcionalidades para monitorar o uso de tokens e estimar os custos associados, permitindo uma gestão eficiente dos recursos:

### 2. Sincronização de Dados

Este componente mantém os dados sincronizados entre o PostgreSQL e o Qdrant:

- Quando um produto é adicionado ou modificado no PostgreSQL, seu embedding é gerado e armazenado no Qdrant
- Quando um produto fica indisponível, essa informação é refletida no Qdrant

#### 2.1 Serviços de Sincronização Detalhados

Nossa arquitetura implementa três serviços de sincronização que trabalham juntos para manter a consistência entre o PostgreSQL e o Qdrant:

##### 2.1.1 DataSyncService

O `DataSyncService` é o componente central responsável por coordenar a sincronização entre o PostgreSQL e o Qdrant:

```python
class DataSyncService:
    def __init__(self, db_client, qdrant_client, embedding_service, redis_client=None):
        self.db_client = db_client
        self.qdrant_client = qdrant_client
        self.embedding_service = embedding_service
        self.redis_client = redis_client
        
    def sync_product(self, product_id):
        """Sincroniza um único produto entre PostgreSQL e Qdrant"""
        # 1. Obter dados do produto do PostgreSQL
        product = self.db_client.get_product(product_id)
        
        if not product:
            # Se o produto foi removido, remova-o do Qdrant também
            self.qdrant_client.delete(collection_name="products", points_selector=[product_id])
            return
        
        # 2. Preparar o texto para embedding
        product_text = self._prepare_product_text(product)
        
        # 3. Gerar embedding
        embedding = self.embedding_service.generate_embedding(product_text)
        
        # 4. Atualizar ou inserir no Qdrant
        self.qdrant_client.upsert(
            collection_name="products",
            points=[
                {
                    "id": product_id,
                    "vector": embedding,
                    "payload": {
                        "name": product["name"],
                        "category_id": product["category_id"],
                        "active": product["active"],
                        "price": float(product["price"]),
                        "last_updated": datetime.now().isoformat()
                    }
                }
            ]
        )
        
        # 5. Invalidar cache se necessário
        if self.redis_client:
            self.redis_client.delete(f"product:{product_id}")
            self.redis_client.delete("product_search:*")
    
    def sync_business_rule(self, rule_id):
        """Sincroniza uma única regra de negócio entre PostgreSQL e Qdrant"""
        # Lógica similar à sincronização de produtos
        # ...
    
    def full_sync_products(self):
        """Sincroniza todos os produtos"""
        # Obter todos os IDs de produtos
        product_ids = self.db_client.get_all_product_ids()
        
        # Sincronizar em lotes para evitar sobrecarga de memória
        batch_size = 100
        for i in range(0, len(product_ids), batch_size):
            batch = product_ids[i:i+batch_size]
            for product_id in batch:
                self.sync_product(product_id)
    
    def full_sync_business_rules(self):
        """Sincroniza todas as regras de negócio"""
        # Lógica similar à sincronização completa de produtos
        # ...
```

##### 2.1.2 DatabaseChangeListener

O `DatabaseChangeListener` monitora alterações no PostgreSQL usando triggers e notificações, garantindo que as mudanças sejam propagadas para o Qdrant em tempo real:

```python
class DatabaseChangeListener:
    def __init__(self, db_connection_string, data_sync_service):
        self.db_connection_string = db_connection_string
        self.data_sync_service = data_sync_service
        self.running = False
        
    async def start(self):
        """Inicia o listener para mudanças no banco de dados"""
        self.running = True
        conn = await asyncpg.connect(self.db_connection_string)
        
        # Configurar triggers no PostgreSQL (se ainda não existirem)
        await self._setup_triggers(conn)
        
        # Inscrever-se para receber notificações
        await conn.add_listener('product_changes', self._on_product_change)
        await conn.add_listener('business_rule_changes', self._on_business_rule_change)
        
        # Manter a conexão aberta enquanto o serviço estiver rodando
        while self.running:
            await asyncio.sleep(1)
            
        # Limpar ao parar
        await conn.remove_listener('product_changes', self._on_product_change)
        await conn.remove_listener('business_rule_changes', self._on_business_rule_change)
        await conn.close()
    
    async def _on_product_change(self, connection, pid, channel, payload):
        """Callback para mudanças em produtos"""
        try:
            data = json.loads(payload)
            product_id = data['id']
            operation = data['operation']  # INSERT, UPDATE, DELETE
            
            if operation == 'DELETE':
                # Remover do Qdrant
                await self.data_sync_service.delete_product(product_id)
            else:
                # Sincronizar com Qdrant
                await self.data_sync_service.sync_product(product_id)
                
        except Exception as e:
            logger.error(f"Erro ao processar mudança de produto: {e}")
    
    async def _on_business_rule_change(self, connection, pid, channel, payload):
        """Callback para mudanças em regras de negócio"""
        # Lógica similar ao callback de produtos
        # ...
        
    async def _setup_triggers(self, conn):
        """Configura triggers no PostgreSQL para notificar sobre mudanças"""
        # Criar função para notificação
        await conn.execute("""
            CREATE OR REPLACE FUNCTION notify_product_changes()
            RETURNS trigger AS $$
            BEGIN
                PERFORM pg_notify(
                    'product_changes',
                    json_build_object(
                        'operation', TG_OP,
                        'id', CASE TG_OP WHEN 'DELETE' THEN OLD.id ELSE NEW.id END
                    )::text
                );
                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Verificar se o trigger já existe
        trigger_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM pg_trigger 
                WHERE tgname = 'products_change_trigger'
            );
        """)
        
        if not trigger_exists:
            # Criar trigger para produtos
            await conn.execute("""
                CREATE TRIGGER products_change_trigger
                AFTER INSERT OR UPDATE OR DELETE ON products
                FOR EACH ROW EXECUTE FUNCTION notify_product_changes();
            """)
            
        # Configuração similar para regras de negócio
        # ...
```

##### 2.1.3 PeriodicSyncService

O `PeriodicSyncService` executa sincronizações completas em intervalos regulares para garantir a consistência, mesmo se algumas notificações forem perdidas:

```python
class PeriodicSyncService:
    def __init__(self, data_sync_service, sync_interval=3600):  # Padrão: 1 hora
        self.data_sync_service = data_sync_service
        self.sync_interval = sync_interval
        self.running = False
        self.last_sync_time = None
        
    async def start(self):
        """Inicia o serviço de sincronização periódica"""
        self.running = True
        while self.running:
            try:
                # Executar sincronização completa
                await self.data_sync_service.full_sync_products()
                await self.data_sync_service.full_sync_business_rules()
                
                self.last_sync_time = datetime.now()
                logger.info(f"Sincronização periódica concluída em {self.last_sync_time}")
                
            except Exception as e:
                logger.error(f"Erro durante sincronização periódica: {e}")
                
            # Aguardar até o próximo intervalo
            await asyncio.sleep(self.sync_interval)
    
    def stop(self):
        """Para o serviço de sincronização periódica"""
        self.running = False
```

#### 2.2 Estratégias de Sincronização

Nossa implementação utiliza várias estratégias para garantir a sincronização eficiente e confiável:

1. **Sincronização Baseada em Eventos**: Usando triggers do PostgreSQL e o sistema de notificação, detectamos mudanças em tempo real e atualizamos o Qdrant imediatamente.

2. **Sincronização Periódica**: Executamos sincronizações completas em intervalos regulares para corrigir quaisquer inconsistências que possam ter ocorrido.

3. **Sincronização em Lote**: Para grandes volumes de dados, processamos em lotes para otimizar o uso de memória e as chamadas à API da OpenAI.

4. **Sincronização Sob Demanda**: Expondo endpoints de API que permitem forçar a sincronização de produtos ou regras específicas quando necessário.

#### 2.3 Tratamento de Falhas

Para garantir a resiliência do sistema, implementamos as seguintes estratégias de tratamento de falhas:

1. **Filas de Retry**: Operações de sincronização que falham são colocadas em uma fila de retry com backoff exponencial.

2. **Logs Detalhados**: Cada operação de sincronização é registrada com detalhes suficientes para diagnóstico e recuperação manual se necessário.

3. **Alertas**: Falhas persistentes geram alertas para a equipe de operações.

4. **Verificações de Integridade**: O serviço periódico inclui verificações de integridade que podem detectar e corrigir inconsistências entre o PostgreSQL e o Qdrant.

### 3. Serviço de Busca Híbrida

Este é o componente central que implementa a estratégia de busca híbrida:

```python
# Fluxo simplificado
def buscar_produtos(consulta_usuario):
    # 1. Converter a consulta em embedding
    embedding = gerar_embedding(consulta_usuario)
    
    # 2. Buscar no Qdrant produtos semanticamente relevantes
    resultados_qdrant = qdrant.search(
        collection_name="products",
        query_vector=embedding,
        filter={"active": True}  # Filtro básico
    )
    
    # 3. Extrair IDs dos produtos encontrados
    ids_produtos = [resultado.id for resultado in resultados_qdrant]
    
    # 4. Verificar disponibilidade no PostgreSQL
    produtos_disponiveis = postgres.execute_query("""
        SELECT * FROM products
        WHERE id IN %s AND active = TRUE AND stock > 0
    """, (tuple(ids_produtos),))
    
    # 5. Retornar produtos disponíveis ordenados por relevância
    return ordenar_por_relevancia(produtos_disponiveis, resultados_qdrant)
```

## Fluxo de Dados

![Diagrama de Fluxo de Dados](https://mermaid.ink/img/pako:eNp1kU1PwzAMhv9KlBMI0ZWPcYBJcEBCQuKAuKDRuKtYm1RJOjZV_e-4Xdex7ZCL7dd-_NqOD1JbhTKTB-_QkYFbZbxBFmgbPHlCQ6YhXFvXEBXwALUjS1TDHdQOHNWgHFrfQKuRwRsXGrJgLTrYBN-QdWBgb7xCBe_KGNxZhyxYtA4qZXwLZbD1Ew_KoYKVMnhSxhFv4T2-KIcFLJVBrZQnHnvXwvhQwEIZPCrVEo-9c_DJQgGPymClVEs89s7BFwsFPCmDWilPPPZuYGChgCdlsFSqJR5752BgoYCFMnhWyhOPvRvYWyhgoQxelGqJx94N7CwUMFcGa6U88di7gZ2FApbK4FWplnjsXcPWQgGvymCtlCceezewtVDAQhm8KdUSj70b2Fko4E0ZvCvliMfeDewsFPCuDN6VcsRj7wZ2FgqYy-wQZ5jJfRhxHv_FbJgNs3E2ycbZJLvILrOrbJpNs-urc3ZxeXY-zS4n2XiUZX8UvK2E?type=png)

## Vantagens da Busca Híbrida

1. **Relevância Semântica**: Encontra produtos que são semanticamente relevantes para a consulta do usuário, mesmo que não contenham exatamente as mesmas palavras.

2. **Dados Atualizados**: Garante que apenas produtos disponíveis sejam recomendados, pois verifica a disponibilidade no PostgreSQL.

3. **Desempenho Otimizado**: Cada banco faz o que sabe fazer melhor - o Qdrant para similaridade semântica e o PostgreSQL para consultas estruturadas.

4. **Escalabilidade**: A arquitetura pode escalar horizontalmente, adicionando mais nós tanto ao PostgreSQL quanto ao Qdrant conforme necessário.

## Implementação no ChatwootAI

No ChatwootAI, implementamos a busca híbrida como um plugin que pode ser facilmente utilizado pelos agentes:

```python
# Exemplo de uso em um agente
produtos = product_search_plugin.search_products(
    query="produtos para pele oleosa",
    limit=3,
    min_score=0.7
)

# Formatar resposta para o cliente
resposta = product_search_plugin.format_product_results(produtos)
```

## Considerações de Implementação

1. **Cache**: Utilizamos Redis para cachear resultados de consultas frequentes, reduzindo a carga nos bancos de dados.

2. **Atualização Assíncrona**: Quando um produto fica indisponível no PostgreSQL, atualizamos assincronamente o Qdrant para refletir essa mudança.

3. **Monitoramento**: Implementamos métricas para avaliar a qualidade das recomendações e ajustar os parâmetros da busca conforme necessário.

## Conclusão

A busca híbrida nos permite oferecer aos clientes recomendações de produtos que são semanticamente relevantes para suas necessidades e garantidamente disponíveis em estoque. Isso melhora significativamente a experiência do cliente e aumenta a eficácia dos agentes de vendas.

---

## Apêndice: Configuração do Ambiente

Para utilizar a busca híbrida, você precisa configurar as seguintes variáveis de ambiente:

```
OPENAI_API_KEY=sua_chave_api_openai
DATABASE_URL=postgresql://usuario:senha@host:porta/banco
QDRANT_URL=http://qdrant:6333
REDIS_URL=redis://redis:6379/0
EMBEDDING_MODEL=text-embedding-3-small
```

## Apêndice: Diagrama de Sequência

![Diagrama de Sequência](https://mermaid.ink/img/pako:eNqFkk1rwzAMhv-KMYUVSrKPHXbYoYcNSinssEMvxVjOBrEd_JGNkv73OW5Ky9jWnGT0vJIeyfcirRYoE7lzFg3Z8KiUNcgcbZwjS6jJ1IS3xjZEOTxA5cgQVfAEtQVLFSiLxtVQa2Rwa2xNlrRGC6tga7IONGyNVajgRWmDa2uRBYvGQqW0a6D0tn7iQVlUsFK6X2_ixGPvHHyykMMi2K-UcsTDLBx8sZDDMtivlLLEwywcfLOQwyLYr5SyxMMsHPywkMMy2K-UcsRj7xwMLOSwCPYrpSzxMAsHAwsFrJTulVKOeJiFg4GFHBbBfqWUIx5m4WBgIYdFsF8p5YiHWTgYWMhhEexXSjniYRYOBhZyWAT7lVKOeJiFg4GFHBbBfqWUIx5m4WBgIYdFsF8p5YiHWTgYWMhhEexXSjniYRYOBhZyWAT7lVKOeJiFg4GFHObJZh9nmMmtH3Ee_8VsmA2zcTbJxtkkO0vOs_PkIplmk-ziPD0dZafDZDRMkj-NVsEA?type=png)
