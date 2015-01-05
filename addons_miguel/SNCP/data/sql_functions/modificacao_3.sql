 CREATE OR REPLACE function atualiza_print_modificacao() RETURNS boolean AS $$
        DECLARE
            dados RECORD;
            codigo_atual varchar;
            refor numeric;
            abat numeric;
            prev_atual numeric;
            prev_corr numeric;
            
        BEGIN
            FOR dados IN (SELECT codigo FROM sncp_modificacao_imprimir_receita WHERE linha IN ('grupo','capitulo')) LOOP
            codigo_atual=trim(dados.codigo) || '%';
	    refor=( SELECT SUM(MIR.reforco) FROM sncp_modificacao_imprimir_receita  AS MIR
	    WHERE MIR.linha='artigo' AND MIR.codigo LIKE codigo_atual);
	    abat=(SELECT SUM(MIR.abate) FROM sncp_modificacao_imprimir_receita AS MIR 
	    WHERE MIR.linha='artigo' AND MIR.codigo LIKE codigo_atual);	
	    prev_atual=( SELECT SUM(MIR.previsao_atual) FROM sncp_modificacao_imprimir_receita AS MIR 
	    WHERE MIR.linha='artigo' AND MIR.codigo LIKE codigo_atual);
	    prev_corr=( SELECT SUM(MIR.previsao_corrigida) FROM sncp_modificacao_imprimir_receita AS MIR 
	    WHERE MIR.linha='artigo' AND MIR.codigo LIKE codigo_atual);

	    UPDATE sncp_modificacao_imprimir_receita SET reforco=refor,abate=abat,
            previsao_atual=prev_atual,previsao_corrigida=prev_corr WHERE codigo=dados.codigo;
            END LOOP;
            RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;