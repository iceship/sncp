SELECT get_parents(AAA.code)
FROM sncp_orcamento_linha AS OL
LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id 
WHERE orcamento_id=2