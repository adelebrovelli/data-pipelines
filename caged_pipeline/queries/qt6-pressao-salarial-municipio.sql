-- Pergunta 6: Quais são as 10 ocupações de maior pressão salarial no Nordeste no mês mais recente?
WITH indice_mensal AS (
  SELECT
    o.descricao_ocupacao,
    t.ano,
    t.mes,
    COUNT(CASE WHEN fato.tipo_sinal = 1 THEN 1 END) AS qtd_admissao,
    COUNT(CASE WHEN fato.tipo_sinal = -1 THEN 1 END) AS qtd_desligamento,
    ROUND(
      AVG(CASE WHEN fato.tipo_sinal = 1 THEN fato.salario END)
      / NULLIF(AVG(CASE WHEN fato.tipo_sinal = -1 THEN fato.salario END), 0)
    * 100, 1) AS indice_pressao_salarial
  FROM `caged-pressao-salarial.caged_pressao_salarial.fct_movimentacao` fato
  JOIN `caged-pressao-salarial.caged_pressao_salarial.dim_ocupacao` o
    ON fato.sk_ocupacao = o.sk_ocupacao
  JOIN `caged-pressao-salarial.caged_pressao_salarial.dim_tempo` t
    ON fato.sk_tempo = t.sk_tempo
  GROUP BY o.descricao_ocupacao, t.ano, t.mes
  HAVING qtd_admissao >= 5 AND qtd_desligamento >= 5
)
SELECT *
FROM indice_mensal
WHERE ano = (SELECT MAX(ano) FROM indice_mensal)
  AND mes = (SELECT MAX(mes) FROM indice_mensal WHERE ano = (SELECT MAX(ano) FROM indice_mensal))
ORDER BY indice_pressao_salarial DESC
LIMIT 10;