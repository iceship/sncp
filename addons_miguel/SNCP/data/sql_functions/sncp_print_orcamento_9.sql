CREATE OR REPLACE FUNCTION insere_titulos(despesa boolean,orcamento_id integer)
  RETURNS boolean AS
$$
DECLARE
  dados varchar;
  prefixo varchar(1);
  montante numeric;
BEGIN 
     dados=(SELECT codigo FROM sncp_orcamento_imprimir WHERE linha='artigo' LIMIT 1);
     IF SUBSTRING(dados FROM 1 FOR 1) NOT BETWEEN '0' AND '9' THEN
        prefixo=SUBSTRING(dados FROM 1 FOR 1);
     ELSE
        prefixo='';

     END IF;		
     
     IF $1=FALSE THEN
        --RECEITA
        montante=(SELECT calcula_montante_titulo('',prefixo||'08'));
        INSERT INTO sncp_orcamento_imprimir(codigo,name,montante,linha,orcamento_id) VALUES('','RECEITAS CORRENTES',montante,'titulo',$2); 
        montante=(SELECT calcula_montante_titulo(prefixo||'09',prefixo||'zz'));
        INSERT INTO sncp_orcamento_imprimir(codigo,name,montante,linha,orcamento_id) VALUES(prefixo||'08zzzzzzzzzzzz','RECEITAS DE CAPITAL',montante,'titulo',$2); 
     ELSE
        --DESPESA PARA SER DESENVOLVIDA
        INSERT INTO sncp_orcamento_imprimir(codigo,name,linha) VALUES('','DESPESAS CORRENTES','titulo');
        INSERT INTO sncp_orcamento_imprimir(codigo,name,linha) VALUES(prefixo||'06zzzzzzzzzzzz','RECEITAS DE CAPITAL','titulo');
     END IF;
RETURN TRUE;

END
$$ LANGUAGE plpgsql;
