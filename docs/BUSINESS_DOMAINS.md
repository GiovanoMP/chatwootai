# Domínios de Negócio

Este documento descreve os domínios de negócio padronizados utilizados no sistema. Estes domínios são utilizados para organizar as configurações e para direcionar o comportamento dos agentes de IA.

## Domínios Padronizados

Os seguintes domínios de negócio estão disponíveis no sistema:

| Identificador Técnico | Nome em Português | Descrição |
|-----------------------|-------------------|-----------|
| `retail` | Varejo | Lojas físicas, comércio de produtos diversos |
| `ecommerce` | E-commerce | Lojas virtuais, comércio eletrônico |
| `healthcare` | Saúde | Clínicas, consultórios, hospitais, farmácias |
| `education` | Educação | Escolas, universidades, cursos online |
| `manufacturing` | Indústria | Fabricação, produção industrial |
| `services` | Serviços | Prestadores de serviços diversos |
| `restaurant` | Restaurante | Restaurantes, pizzarias, lanchonetes |
| `financial` | Serviços Financeiros | Bancos, seguradoras, corretoras |
| `technology` | Tecnologia | Empresas de tecnologia, desenvolvimento de software |
| `hospitality` | Hotelaria | Hotéis, pousadas, resorts |
| `real_estate` | Imobiliário | Imobiliárias, construtoras |
| `other` | Outro | Outros modelos de negócio não listados |

## Uso no Sistema

Estes domínios são utilizados em vários componentes do sistema:

1. **Módulo ai_credentials_manager**: Campo `business_area` para definir a área de negócio do cliente
2. **Módulo business_rules**: Campo `business_model` para definir o modelo de negócio
3. **Arquivos YAML**: Diretórios em `config/domains/` para organizar configurações por domínio

## Estrutura de Diretórios

Os arquivos de configuração são organizados por domínio e account_id:

```
/config
  /domains
    /retail             # Domínio de varejo
      /account_1        # Diretório para o account_id 1
        /config.yaml    # Configuração geral para o account_id 1
    /healthcare         # Domínio de saúde
      /account_2        # Diretório para o account_id 2
        /config.yaml    # Configuração geral para o account_id 2
    /ecommerce          # Domínio de e-commerce
      /account_3        # Diretório para o account_id 3
        /config.yaml    # Configuração geral para o account_id 3
```

## Comportamento dos Agentes

Os agentes de IA adaptam seu comportamento com base no domínio de negócio:

- **Retail**: Foco em produtos físicos, estoque, lojas físicas
- **Healthcare**: Foco em pacientes, consultas, tratamentos
- **Education**: Foco em alunos, cursos, matrículas
- **Restaurant**: Foco em cardápios, reservas, delivery

## Extensibilidade

O sistema permite a adição de novos domínios de negócio conforme necessário. Para adicionar um novo domínio:

1. Adicione o novo domínio aos campos `business_area` e `business_model` nos módulos Odoo
2. Crie o diretório correspondente em `config/domains/`
3. Atualize este documento com o novo domínio

## Considerações para Internacionalização

Os identificadores técnicos dos domínios são em inglês para facilitar a internacionalização e a consistência técnica, enquanto as interfaces de usuário exibem os nomes em português para melhor experiência do usuário.
