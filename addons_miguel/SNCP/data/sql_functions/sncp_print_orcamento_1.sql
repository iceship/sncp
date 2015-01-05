SELECT AAA.code,AAA.name,OL.reforco AS montante,CAST('artigo' AS varchar) AS linha INTO sncp_print_orcamento
FROM sncp_orcamento_linha AS OL
LEFT JOIN account_analytic_account AS AAA ON AAA.id=OL.economica_id 
WHERE orcamento_id=2