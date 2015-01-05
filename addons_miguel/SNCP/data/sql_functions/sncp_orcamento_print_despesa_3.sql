SELECT get_parents_economica(AAA2.code,AAA.code,1)
FROM sncp_orcamento_linha AS OL
LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id
LEFT JOIN account_analytic_account AS AAA2 ON AAA2.id=OL.organica_id
WHERE orcamento_id=1
