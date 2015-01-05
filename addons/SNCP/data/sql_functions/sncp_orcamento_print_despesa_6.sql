CREATE OR REPLACE function atualiza_print_orcamento_despesa() RETURNS boolean AS $$
DECLARE 
	dados RECORD;
	codigo_atual varchar;
	novo_montante numeric; 
BEGIN
    FOR dados IN (SELECT codigo_org,codigo_eco FROM sncp_orcamento_imprimir_despesa WHERE linha IN ('grupo','capitulo')) LOOP
	codigo_atual=trim(dados.codigo_eco) || '%';
	novo_montante=( SELECT SUM(montante) FROM sncp_orcamento_imprimir_despesa WHERE linha='artigo' AND codigo_org=dados.codigo_org 
	AND codigo_eco LIKE codigo_atual);
	UPDATE sncp_orcamento_imprimir_despesa SET montante=novo_montante WHERE codigo_org=dados.codigo_org AND codigo_eco=dados.codigo_eco;
    END LOOP;
    RETURN TRUE; 
END
$$ LANGUAGE plpgsql;