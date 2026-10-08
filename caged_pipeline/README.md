## 1. Qual o mês de mais admissões e qual o mês de mais desligamentos na indústria nordestina nesses 13 meses?

**Query:** [`qt1-top-desligamentos-admissoes.sql`](queries/qt1-top-desligamentos-admissoes.sql)

| ano | mes | tipo | qtd_movimentacao |
|---|---|---|---|
| 2025 | 9 | admissao | 348856 |
| 2026 | 3 | desligamento | 316814 |

**Comentário:** Setembro de 2025 foi o mês com maior número de admissões e março de 2026 foi o com maior número de mês de desligamentos.

## 2. Qual a rotatividade absoluta na indústria elétrica de junho a dezembro de 2025?

**Query:** [`qt2-rotatividade.sql`](queries/qt2-rotatividade.sql)

| ano | mes | rotatividade_absoluta |
|---|---|---|
| 2025 | 6 | 400.0 |
| 2025 | 7 | 361.0 |
| 2025 | 8 | 387.5 |
| 2025 | 9 | 403.0 |
| 2025 | 10 | 445.5 |
| 2025 | 11 | 415.0 |
| 2025 | 12 | 361.0 |

**Comentário:** Em 2025 a indústria elétrica teve julho e dezembro com pontos de rotatividade mais baixos e outubro como maior pico de rotatividade de funcionários.

## 3. Qual setor está pagando mais entre Indústria e Serviços?

**Query:** [`qt3-industria-ou-servicos.sql`](queries/qt3-industria-ou-servicos.sql)

| grande_grupamento | media_salarial | mediana_salarial |
|---|---|---|
| Indústria Geral | 1975.68 | 1621.0 |
| Serviços | 1966.22 | 1621.0 |

**Comentário:** Indústria Geral e Serviços tem médias muito similares. A mediana sugere que grande parte receba cerca de um salário mínio. O valor do salário da Indústria ainda é maior do que Serviços, chegando a R$1.975,68, cerca de 9 reais a mais do que o salário do setor de Serviços, R$1.966,22.

## 4. Quais ocupações tiveram o maior saldo de contratações em março?

**Query:** [`qt4-ocupacoes-maior-saldo.sql`](queries/qt4-ocupacoes-maior-saldo.sql)

| descricao_ocupacao | saldo | mes | ano |
|---|---|---|---|
| Servente De Obras | 5087 | 3 | 2026 |
| Faxineiro | 4026 | 3 | 2026 |
| Alimentador De Linha De Producao | 2608 | 3 | 2026 |
| Operador De Telemarketing Ativo E Receptivo | 2370 | 3 | 2026 |
| Auxiliar De Escritorio, Em Geral | 2293 | 3 | 2026 |

**Comentário:** Servente de obras e faxineiro tiveram os maiores saldos do mês em 2026.

## 5.  Qual município nordestino tem o maior saldo em relação ao total da região nesses últimos 13 meses?

**Query:** [`qt5-municipio-maior-saldo.sql`](queries/qt5-municipio-maior-saldo.sql)

| descricao_municipio | saldo | saldo_total_nordeste |
|---|---|---|
| Ba-Salvador | 27807 | 343730 |
| Ce-Fortaleza | 21816 | 343730 |
| Pe-Recife | 20976 | 343730 |
| Ma-Sao Luis | 19180 | 343730 |
| Pb-Joao Pessoa | 12484 | 343730 |

**Comentário:** Salvador foi o município de maior saldo, chegando a um saldo equivalente a 27.807 empregos, ficando na frente de Fortaleza, com 21.816. Logo, Salvador sozinho traz a proporção de 8,1% em relação à região.

## 6. Quais são as 10 ocupações de maior pressão salarial no Nordeste no mês mais recente?

**Query:** [`qt6-pressao-salarial-ocupacao.sql`](queries/qt6-pressao-salarial-ocupacao.sql)

| descricao_ocupacao | ano | mes | qtd_admissao | qtd_desligamento | indice_pressao_salarial |
|---|---|---|---|---|---|
| Professor De Artes No Ensino Medio | 2026 | 5 | 15 | 14 | 366.5 |
| Socioeducador | 2026 | 5 | 35 | 24 | 253.5 |
| Professor De Historia Do Ensino Fundamental | 2026 | 5 | 41 | 26 | 239.3 |
| Mecanico De Manutencao De Aeronaves, Em Geral | 2026 | 5 | 11 | 9 | 220.9 |
| Professor De Linguas Estrangeiras Modernas | 2026 | 5 | 12 | 5 | 214.0 |
| Supervisor De Orcamento | 2026 | 5 | 12 | 20 | 194.0 |
| Médico Anestesiologista | 2026 | 5 | 8 | 35 | 189.5 |
| Professor De Medicina | 2026 | 5 | 9 | 9 | 185.9 |
| Medico Veterinario | 2026 | 5 | 25 | 23 | 178.9 |
| Professor De Geografia Do Ensino Fundamental | 2026 | 5 | 37 | 28 | 178.3 |

**Comentário:** Professor de artes do ensino médio, no mês de maio de 2026, foi a ocupação que teve a maior pressão salarial do Nordeste (366.5), seguida por socioeducador(253.5) e professor de história do ensino fundamental (239.3).

## 7. Qual dos 9 estados do Nordeste apresentou maior taxa de admissão desde o último ano?

**Query:** [`qt7-ranking-maior-admissao`](queries/qt7-ranking-maior-admissao.sql)

| estado | taxa_admissao | rank_taxa_estado |
|---|---|---|
| Piauí | 0.5273 | 1 |
| Sergipe | 0.5259 | 2 |
| Paraíba | 0.5249 | 3 |
| Pernambuco | 0.5247 | 4 |
| Maranhão | 0.5241 | 5 |

**Comentário:** O Piauí teve a maior taxa de admissão do Nordeste, chegando a 52,7%, apesar de que os estados Sergipe, Paraíba, Pernambuco e Maranhão tiveram uma diferença máxima de 0.32 pontos percentuais do estado de maior taxa.
