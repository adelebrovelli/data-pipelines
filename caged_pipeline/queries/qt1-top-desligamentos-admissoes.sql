-- Pergunta 1: Qual o mês de mais admissões e qual o mês de mais desligamentos na indústria nordestina nesses 13 meses?
SELECT * FROM (
  SELECT
    t.ano, t.mes, fato.tipo,
    COUNT(*) AS qtd_movimentacao,
    RANK() OVER (PARTITION BY fato.tipo ORDER BY COUNT(*) DESC) AS posicao
  FROM `caged_pressao_salarial.fct_movimentacao` fato
  JOIN `caged_pressao_salarial.dim_tempo` t ON fato.sk_tempo = t.sk_tempo
  GROUP BY t.ano, t.mes, fato.tipo
)
WHERE posicao = 1
