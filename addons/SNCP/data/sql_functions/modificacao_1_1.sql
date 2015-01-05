CREATE OR REPLACE FUNCTION obtem_previsao_atual(datahora varchar,ano integer) RETURNS BOOLEAN AS
$$
 DECLARE
  dados RECORD;
  prev_atual numeric;
  abate numeric;
  prev_futura numeric;
 BEGIN
    FOR dados IN (SELECT * FROM sncp_modificacao_imprimir_receita) LOOP
	prev_atual=COALESCE((SELECT SUM(montante) FROM sncp_orcamento_historico AS OH WHERE OH.name=$2 AND OH.datahora < $1::TIMESTAMP AND 
	OH.economica_id=dados.economica_id AND OH.categoria IN ('51rdota','52rrefo')),0.0);
	abate=COALESCE((SELECT SUM(montante) FROM sncp_orcamento_historico AS OH WHERE OH.name=$2 AND OH.datahora < $1::TIMESTAMP 
	AND OH.economica_id=dados.economica_id AND OH.categoria = '53rabat'),0.0);
        prev_atual=prev_atual-abate;
	prev_futura=prev_atual+dados.reforco-dados.abate;
	UPDATE sncp_modificacao_imprimir_receita SET previsao_atual=prev_atual,previsao_corrigida=prev_futura
	WHERE id=dados.id;
    END LOOP;
    RETURN TRUE;
 END
$$ LANGUAGE plpgsql;