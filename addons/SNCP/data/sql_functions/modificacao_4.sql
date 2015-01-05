CREATE OR REPLACE function calcula_montante_titulo_mod(codigo_from varchar,codigo_to varchar,nref integer) RETURNS numeric AS $$
        BEGIN
        IF $3=0 THEN
		RETURN (SELECT SUM(abate)
                    FROM sncp_modificacao_imprimir_receita
                    WHERE linha = 'capitulo' AND codigo BETWEEN $1 AND $2);    
	END IF;
	IF $3=1 THEN
		RETURN (SELECT SUM(reforco)
                    FROM sncp_modificacao_imprimir_receita
                    WHERE linha = 'capitulo' AND codigo BETWEEN $1 AND $2);
	END IF;
	IF $3=2 THEN
	        RETURN (SELECT SUM(previsao_atual)
	                FROM sncp_modificacao_imprimir_receita
                        WHERE linha = 'capitulo' AND codigo BETWEEN $1 AND $2);
        END IF;
        IF $3=3 THEN
		RETURN (SELECT SUM(previsao_corrigida)
	                FROM sncp_modificacao_imprimir_receita
                        WHERE linha = 'capitulo' AND codigo BETWEEN $1 AND $2);
        END IF;
        END
        $$ LANGUAGE plpgsql;