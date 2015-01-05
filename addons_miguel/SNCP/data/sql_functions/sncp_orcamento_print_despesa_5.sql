SELECT get_parents_organica(AAA2.code,1)
FROM sncp_orcamento_linha AS OL
LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
WHERE orcamento_id=1