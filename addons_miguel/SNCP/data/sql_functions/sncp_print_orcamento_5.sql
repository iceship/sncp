CREATE OR REPLACE function atualiza_print_orcamento() RETURNS boolean AS $$
DECLARE 
	dados RECORD;
	codigo_atual varchar;
	novo_montante numeric; 
BEGIN
    FOR dados IN (SELECT codigo FROM sncp_orcamento_imprimir WHERE linha IN ('grupo','capitulo')) LOOP
	codigo_atual=trim(dados.codigo) || '%';
	novo_montante=( SELECT SUM(montante) FROM sncp_orcamento_imprimir WHERE linha='artigo' AND codigo LIKE codigo_atual);
	UPDATE sncp_orcamento_imprimir SET montante=novo_montante WHERE codigo=dados.codigo;
    END LOOP;
    RETURN TRUE; 
END
$$ LANGUAGE plpgsql;
