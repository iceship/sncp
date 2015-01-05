CREATE OR REPLACE FUNCTION calcula_montante_titulo(codigo_from varchar,codigo_to varchar) RETURNS numeric AS $$
BEGIN
     RETURN (SELECT SUM(montante)
            FROM sncp_orcamento_imprimir
            WHERE linha = 'capitulo' AND codigo BETWEEN $1 AND $2); 
END
$$ LANGUAGE plpgsql;
