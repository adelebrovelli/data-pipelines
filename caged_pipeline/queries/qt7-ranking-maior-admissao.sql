-- Pergunta 7: Qual dos 9 estados do Nordeste apresentou maior taxa de admissão desde o último ano?
WITH base_query_nordeste AS (
  SELECT m.sigla_uf AS estado, t.competencia, fato.tipo_sinal
  FROM `caged-pressao-salarial.caged_pressao_salarial.fct_movimentacao` fato
  JOIN `caged-pressao-salarial.caged_pressao_salarial.dim_municipio` m ON fato.sk_municipio = m.sk_municipio
  JOIN `caged-pressao-salarial.caged_pressao_salarial.dim_tempo` t ON fato.sk_tempo = t.sk_tempo
),
taxa_por_estado AS (
  SELECT estado, 
  COUNTIF(tipo_sinal = 1) / COUNT(*) AS taxa_admissao
  FROM base_query_nordeste
  WHERE competencia > DATE_SUB((SELECT MAX(competencia) FROM base_query_nordeste), INTERVAL 12 MONTH)
  GROUP BY estado
)

SELECT estado, 
ROUND(taxa_admissao, 4) AS taxa_admissao, 
RANK() OVER (ORDER BY taxa_admissao DESC) AS rank_taxa_estado
FROM taxa_por_estado
ORDER BY rank_taxa_estado;