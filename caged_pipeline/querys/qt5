-- Pergunta 5: Qual município nordestino tem o maior saldo em relação ao total da região nesses últimos 13 meses?
SELECT
  m.descricao_municipio,
  SUM(fato.tipo_sinal) AS saldo,
  SUM(SUM(fato.tipo_sinal)) OVER () AS saldo_total_nordeste
FROM `caged-pressao-salarial.caged_pressao_salarial.fct_movimentacao` fato
JOIN `caged-pressao-salarial.caged_pressao_salarial.dim_municipio` m
  ON fato.sk_municipio = m.sk_municipio
GROUP BY m.descricao_municipio
ORDER BY saldo DESC;