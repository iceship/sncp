CREATE OR REPLACE FUNCTION mod_desp_check_cab_organica() RETURNS BOOLEAN AS $$
        DECLARE
          dados RECORD;
        BEGIN
          IF (SELECT COALESCE((SELECT id FROM sncp_modificacao_imprimir_despesa WHERE linha='cabecalho1'),0))=0 THEN
             UPDATE sncp_modificacao_imprimir_despesa SET linha='cabecalho1' WHERE linha='cabecalho2';
          END IF;
        RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;