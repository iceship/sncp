CREATE OR REPLACE function atualiza_print_modificacao_despesa() RETURNS boolean AS $$
            DECLARE
                dados RECORD;
                codigo_atual varchar;
                refor numeric;
                abat numeric;
                prev_atual numeric;
                prev_corr numeric;
                
            BEGIN
                FOR dados IN (SELECT codigo_org,codigo_eco FROM sncp_modificacao_imprimir_despesa WHERE linha IN ('grupo','capitulo')) LOOP
                codigo_atual=trim(dados.codigo_eco) || '%';
		refor=( SELECT SUM(MID.reforco) FROM sncp_modificacao_imprimir_despesa  AS MID
	    WHERE MID.linha='artigo' AND MID.codigo_org=dados.codigo_org AND MID.codigo_eco LIKE codigo_atual);
	    abat=( SELECT SUM(MID.abate) FROM sncp_modificacao_imprimir_despesa  AS MID
	    WHERE MID.linha='artigo' AND MID.codigo_org=dados.codigo_org AND MID.codigo_eco LIKE codigo_atual);	
	    prev_atual=( SELECT SUM(MID.previsao_atual) FROM sncp_modificacao_imprimir_despesa  AS MID
	    WHERE MID.linha='artigo' AND MID.codigo_org=dados.codigo_org AND MID.codigo_eco LIKE codigo_atual);
	    prev_corr=( SELECT SUM(MID.previsao_corrigida) FROM sncp_modificacao_imprimir_despesa  AS MID
	    WHERE MID.linha='artigo' AND MID.codigo_org=dados.codigo_org AND MID.codigo_eco LIKE codigo_atual);

	    UPDATE sncp_modificacao_imprimir_despesa SET reforco=refor,abate=abat,
            previsao_atual=prev_atual,previsao_corrigida=prev_corr WHERE codigo_org=dados.codigo_org AND codigo_eco=dados.codigo_eco ;
                END LOOP;
                RETURN TRUE;
            END
            $$ LANGUAGE plpgsql;
