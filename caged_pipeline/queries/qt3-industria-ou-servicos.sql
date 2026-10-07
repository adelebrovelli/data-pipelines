-- Pergunta 3: Qual setor está pagando mais entre Indústria e Serviços?
SELECT
  s.grande_grupamento,
  AVG(fato.salario) AS media_salarial,
  APPROX_QUANTILES(fato.salario, 100)[OFFSET(50)] AS mediana_salarial
FROM `caged-pressao-salarial.caged_pressao_salarial.fct_movimentacao` fato
JOIN `caged-pressao-salarial.caged_pressao_salarial.dim_setor` s
  ON fato.sk_setor = s.sk_setor
WHERE fato.tipo = 'admissao' AND (s.grande_grupamento = "Serviços" OR s.grande_grupamento = "Indústria Geral")
GROUP BY s.grande_grupamento
ORDER BY salario_medio_admissao DESC
