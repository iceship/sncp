# -*- encoding: utf-8 -*-
# #############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    vals program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    vals program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with vals program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import *
from openerp.osv import fields, osv
from openerp.tools.translate import _


# __________________________________________________ TABELAS AUXILIARES_________________________________
# __________________________________________________ PPI EIXOS ________________________________________
class sncp_orcamento_ppi_eixos(osv.Model):
    _name = 'sncp.orcamento.ppi.eixos'

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'descricao'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['descricao']:
                name = name + ' ' + record['descricao']
            res.append((record['id'], name))
        return res

    _columns = {
        'name': fields.char(u'Código', size=1),
        'descricao': fields.char(u'Descrição'),
    }

    _order = 'name'

    _sql_constraints = [
        ('codigo_eixos_unique', 'unique (name)', u'O código têm que ser único!'),
    ]

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_orcamento_ppi_accoes
            WHERE eixo_id = %d
            """ % obj.id)

            res_accoes = cr.fetchall()

            if len(res_accoes) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o eixo ' + obj.name + u' '
                                                    + obj.descricao
                                                    + u' têm associação em:\n'
                                                    u'1. PPI\Acções.'))

        return super(sncp_orcamento_ppi_eixos, self).unlink(cr, uid, ids, context=context)

    def codigo_valido(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        if len(obj.name) < 1:
            raise osv.except_osv(_(u'Aviso'), _(u'O código deve ter comprimento 1.'))

        if ord(obj.name[0]) in range(48, 58) or ord(obj.name[0]) in range(65, 91):
            return True

        raise osv.except_osv(_(u'Aviso'), _(u'O código do eixo deve estar entre 0 e Z contendo apenas algarismos '
                                            u'e letras maiúsculas.'))

    _constraints = [(codigo_valido, u'', ['name']), ]


sncp_orcamento_ppi_eixos()


# ___________________________________________________ PPI OBJECTIVOS ___________________________________
class sncp_orcamento_ppi_objetivos(osv.Model):
    _name = 'sncp.orcamento.ppi.objetivos'

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'descricao'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['descricao']:
                name = name + ' ' + record['descricao']
            res.append((record['id'], name))
        return res

    _columns = {
        'name': fields.char(u'Código', size=2),
        'descricao': fields.char(u'Descrição'),
    }

    _order = 'name'

    _sql_constraints = [
        ('codigo_objetivos_unique', 'unique (name)', u'O código têm que ser único!'),
    ]

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_orcamento_ppi_accoes
            WHERE objetivo_id = %d
            """ % obj.id)

            res_accoes = cr.fetchall()

            if len(res_accoes) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o objetivo ' + obj.name + u' '
                                                    + obj.descricao
                                                    + u' têm associação em:\n'
                                                    u'1. PPI\Acções.'))

        return super(sncp_orcamento_ppi_objetivos, self).unlink(cr, uid, ids, context=context)

    def codigo_valido(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        ok = False

        if len(obj.name) < 2:
            raise osv.except_osv(_(u'Aviso'), _(u'O código deve ter comprimento 2.'))

        for i in range(0, len(obj.name)):
            if ord(obj.name[i]) in range(48, 58) or ord(obj.name[i]) in range(65, 91):
                ok = True
            else:
                ok = False
                break

        if ok is False:
            raise osv.except_osv(_(u'Aviso'), _(u'O código do objetivo deve estar entre 00 e ZZ contendo apenas'
                                                u' algarismos e letras maiúsculas.'))

        return True

    _constraints = [(codigo_valido, u'', ['name']), ]


sncp_orcamento_ppi_objetivos()


# ___________________________________________________ PPI PROGRAMAS ____________________________________
class sncp_orcamento_ppi_programas(osv.Model):
    _name = 'sncp.orcamento.ppi.programas'

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'descricao'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['descricao']:
                name = name + ' ' + record['descricao']
            res.append((record['id'], name))
        return res

    _columns = {
        'name': fields.char(u'Código', size=5),
        'descricao': fields.char(u'Descrição'),
    }

    _order = 'name'

    _sql_constraints = [
        ('codigo_programas_unique', 'unique (name)', u'O código têm que ser único!'),
    ]

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_orcamento_ppi_accoes
            WHERE programa_id = %d
            """ % obj.id)

            res_accoes = cr.fetchall()

            if len(res_accoes) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o programa ' + obj.name + u' '
                                                    + obj.descricao
                                                    + u' têm associação em:\n'
                                                    u'1. PPI\Acções.'))

        return super(sncp_orcamento_ppi_programas, self).unlink(cr, uid, ids, context=context)

    def codigo_valido(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        ok = False

        if len(obj.name) < 5:
            raise osv.except_osv(_(u'Aviso'), _(u'O código deve ter comprimento 5.'))

        for i in range(0, len(obj.name)):
            if i == 2 and obj.name[i] == u'.':
                ok = True
            elif ord(obj.name[i]) in range(48, 58) or ord(obj.name[i]) in range(65, 91):
                ok = True
            else:
                ok = False
                break

        if ok is False:
            raise osv.except_osv(_(u'Aviso'), _(u'O código do objetivo deve estar entre 00.00 e ZZ.ZZ'
                                                u' contendo apenas algarismos e maiúsculas e o .!'))

        return True

    _constraints = [(codigo_valido, u'', ['name']), ]

sncp_orcamento_ppi_programas()


# ___________________________________________________ PPI ACCOES _______________________________________
class sncp_orcamento_ppi_accoes(osv.Model):
    _name = 'sncp.orcamento.ppi.accoes'

    def on_change_eixo_objt_prog(self, cr, uid, ids, eixo_id, objetivo_id, programa_id, context=None):
        name = ''

        if eixo_id and objetivo_id and programa_id:
            cr.execute("""
                       SELECT name
                       FROM sncp_orcamento_ppi_eixos
                       WHERE id=%d
                       """ % eixo_id)

            codigo_eixo = cr.fetchone()[0]

            cr.execute("""
                       SELECT name
                       FROM sncp_orcamento_ppi_objetivos
                       WHERE id=%d
                      """ % objetivo_id)

            codigo_objetivo = cr.fetchone()[0]

            cr.execute("""
                       SELECT name
                       FROM sncp_orcamento_ppi_programas
                       WHERE id=%d
                      """ % programa_id)

            codigo_programa = cr.fetchone()[0]

            if codigo_eixo == codigo_objetivo[:1] and codigo_objetivo == codigo_programa[:2]:
                name = codigo_programa

                if len(ids) != 0:
                    self.write(cr, uid, ids, {'name': name,
                                              'eixo_id': eixo_id,
                                              'programa_id': programa_id,
                                              'objetivo_id': objetivo_id, })

        return {
            'value': {
                'name': name,
                'eixo_id': eixo_id,
                'programa_id': programa_id,
                'objetivo_id': objetivo_id,
            }
        }

    def on_change_name_2(self, cr, uid, ids, name, name2, context=None):
        descricao = ''
        funcional_id = False
        if name and name2:
            codigo_funcional = unicode(name) + unicode(name2)

            cr.execute("""
            SELECT id,name
            FROM account_analytic_account
            WHERE code='%s' and tipo_dim='cf' and type='normal'
            """ % codigo_funcional)

            funcional = cr.fetchone()

            if funcional is not None:
                funcional_id = funcional[0]
                descricao = funcional[1]
                if len(ids) != 0:
                    self.write(cr, uid, ids, {'descricao': descricao, 'name2': name2,
                                              'funcional_id': funcional_id})

        return {
            'value': {
                'descricao': descricao,
                'name2': name2,
                'funcional_id': funcional_id
            }
        }

    def cria_dotacao(self, cr, uid, ids, context=None):
        db_sncp_orcamento_ppi_dotacoes = self.pool.get('sncp.orcamento.ppi.dotacoes')
        db_sncp_orcamento_ppi_anual = self.pool.get('sncp.orcamento.ppi.anual')
        obj = self.browse(cr, uid, ids[0])

        if not obj.inicio or not obj.fim:
            raise osv.except_osv(_(u'Aviso'), _(u'Defina as datas de início e fim.'))

        cr.execute("""
        SELECT id FROM account_analytic_account
        WHERE tipo_dim='ce' AND type='normal'
        """)

        economicas_ids = cr.fetchall()

        if len(economicas_ids) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não existem contas analíticas com a classificação económica.'))

        cr.execute("""
        SELECT id
        FROM account_analytic_account
        WHERE id NOT IN (SELECT name FROM sncp_orcamento_ppi_dotacoes WHERE accoes_id=%d)
        AND tipo_dim='ce' AND type='normal'
        """ % ids[0])

        economica_id = cr.fetchone()

        if economica_id is None:
            raise osv.except_osv(_(u'Aviso'), _(u'As contas analíticas com a classificação económica já foram todas'
                                                u' utilizadas para esta acção.'))

        self.write(cr, uid, ids, {'estado': 1})
        dotacoes_id = db_sncp_orcamento_ppi_dotacoes.create(cr, uid, {'name': economica_id[0],
                                                                      'accoes_id': ids[0]})

        data_inicio = datetime.strptime(obj.inicio, "%Y-%m-%d")
        data_fim = datetime.strptime(obj.fim, "%Y-%m-%d")

        for ano in range(data_inicio.year, data_fim.year + 1):
            db_sncp_orcamento_ppi_anual.create(cr, uid, {
                'name': dotacoes_id,
                'ano_planeado': ano,
            })

        return True

    def teste_existencia_ppi_accoes(self, cr):
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'insere_orcamento_ppi_imprimir_accoes'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_orcamento_ppi_imprimir_accoes(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'calcula_definido'""")
        result = cr.fetchone()
        if result is None:
            self.sql_calcula_definido(cr)

        cr.execute(
            """SELECT proname FROM pg_catalog.pg_proc
               WHERE proname = 'calcula_despesa_definido_n_definido_total_geral_accao'""")
        result = cr.fetchone()
        if result is None:
            self.sql_calcula_despesa_definido_n_definido_total_geral_accao(cr)

        cr.execute(
            """SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'insere_orcamento_ppi_imprimir_programas'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_orcamento_ppi_imprimir_programas(cr)

        cr.execute(
            """SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'insere_orcamento_ppi_imprimir_objetivos'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_orcamento_ppi_imprimir_objetivos(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'insere_orcamento_ppi_imprimir_eixos'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_orcamento_ppi_imprimir_eixos(cr)

        cr.execute(
            """SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'insere_orcamento_ppi_imprimir_total_geral'""")
        result = cr.fetchone()
        if result is None:
            self.sql_insere_orcamento_ppi_imprimir_total_geral(cr)

        return True

    _columns = {
        'name': fields.char(u'Código da Funcional'),
        'name2': fields.char(u'', size=5),
        'funcional_id': fields.many2one('account.analytic.account', u'Funcional',
                                        domain=[('tipo_dim', '=', 'cf'), ('type', '=', 'normal')], ),
        'descricao': fields.char(u'Descrição'),

        'eixo_id': fields.many2one('sncp.orcamento.ppi.eixos', u'Eixo'),
        'objetivo_id': fields.many2one('sncp.orcamento.ppi.objetivos', u'Programa'),
        'programa_id': fields.many2one('sncp.orcamento.ppi.programas', u'Objetivo'),

        'organica_id': fields.many2one('account.analytic.account', u'Orgânica',
                                       domain=[('tipo_dim', '=', 'uo'), ('type', '=', 'normal')], ),
        'inicio': fields.date(u'Data início'),
        'fim': fields.date(u'Data fim'),
        'responsavel_id': fields.many2one('hr.employee', u'Responsável'),
        'realizacao': fields.selection([
                                       ('admi', u'AD - Administração Direta'),
                                       ('empr', u'E - Empreitada'),
                                       ('forn', u'FO - Fornecimentos e Outros'),
                                       ('emprforn', u'EF - Empreitadas e Fornecimentos'),
                                       ], u'Forma de realização'),
        'execucao': fields.selection([
                                     ('nini', u'1 - Não iniciada'),
                                     ('proj', u'2 - Com projeto técnico'),
                                     ('adju', u'3 - Adjudicada'),
                                     ('ex49', u'4 - Execução física < 50%'),
                                     ('ex51', u'5 - Execução física > 50%'),
                                     ('conc', u'6 - Concluída')], u'Fase de execução'),
        'dotacoes_id': fields.one2many('sncp.orcamento.ppi.dotacoes', 'accoes_id', string=u'Económicas'),
        'fonte': fields.selection([
                                  ('Ac', u'Administração Central'),
                                  ('Aa', u'Administração Autárquica'),
                                  ('Ar', u'Administração Regional'),
                                  ('Fc', u'Fundos Comunitários'),
                                  ('Em', u'Empréstimo'),
                                  ('Sf', u'Sem financiamento'),
                                  ], u'Fonte'),
        'percent': fields.integer(u'Perc. Financiamento', size=3),
        'estado': fields.integer(u'')
        # 0 -- Datas alteráveis
        # 1 -- Datas não alteráveis
    }

    def sql_insere_orcamento_ppi_imprimir_accoes(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_orcamento_ppi_imprimir_accoes(ano integer)
        RETURNS boolean AS
        $$
        DECLARE
           accao   sncp_orcamento_ppi_accoes%ROWTYPE;
           dotacao sncp_orcamento_ppi_dotacoes%ROWTYPE;
           anual sncp_orcamento_ppi_anual%ROWTYPE;
           accoes RECORD;
           accao_id integer;
           descricao varchar;
           nome_responsavel varchar;
           organica_code varchar;
           funcional_code varchar;
           economica_code varchar;
           n_resp varchar;
           letra varchar;

           i integer;
           imprimir_ppi_id integer;
           montante_anos_seguintes numeric;
           montante_ano numeric;

           BEGIN
             FOR  accoes IN (SELECT DISTINCT PAC.id AS identificador FROM sncp_orcamento_ppi_accoes AS PAC
                    INNER JOIN sncp_orcamento_ppi_dotacoes AS OD ON OD.accoes_id=PAC.id
                    INNER JOIN sncp_orcamento_ppi_anual AS PAN ON PAN.name=OD.id
                            WHERE PAN.ano_planeado=$1)
               LOOP
              n_resp='';
              SELECT * INTO accao FROM sncp_orcamento_ppi_accoes WHERE id=accoes.identificador;

              descricao=(SELECT AAA.name FROM account_analytic_account AS AAA WHERE id=accao.funcional_id);

              nome_responsavel=(SELECT HR.name_related FROM hr_employee AS HR WHERE id=accao.responsavel_id);
              nome_responsavel=(SELECT INITCAP(nome_responsavel));

              organica_code=(SELECT AAA.code FROM account_analytic_account AS AAA WHERE id=accao.organica_id);
              funcional_code=(SELECT AAA.code FROM account_analytic_account AS AAA WHERE id=accao.funcional_id);

              FOR i IN 1..LENGTH(nome_responsavel) LOOP
                 letra=substring(nome_responsavel from i for 1);
                 IF ascii(letra)>=64 AND ascii(letra)<=90 THEN
                    n_resp=n_resp || letra;
                 END IF;
              END LOOP;

              FOR dotacao IN (SELECT * FROM sncp_orcamento_ppi_dotacoes WHERE accoes_id=accao.id)
              LOOP
                       economica_code=(SELECT AAA.code FROM account_analytic_account AS AAA WHERE id=dotacao.name);
                           montante_ano=(SELECT COALESCE(SOPA.montante,0.0) FROM sncp_orcamento_ppi_anual AS SOPA
                           WHERE SOPA.name=dotacao.id
                           AND SOPA.ano_planeado = $1);

                           IF montante_ano > 0 THEN
                                   INSERT INTO sncp_orcamento_ppi_imprimir(name,descricao,funcional_id,responsavel,
                                   realizacao,execucao,data_ini,data_fim,organica_code,organica_id,fonte_financ,
                                   perc_financ,economica_code,economica_id,total,linha)
                           VALUES(funcional_code,descricao,accao.funcional_id,n_resp,accao.realizacao,accao.execucao,
                           accao.inicio,accao.fim,organica_code,accao.organica_id,accao.fonte,accao.percent,
                           economica_code,dotacao.name,montante_ano,'accao');
                       imprimir_ppi_id = (SELECT currval('sncp_orcamento_ppi_imprimir_id_seq'));
                       montante_anos_seguintes=0.0;
                       FOR anual IN (SELECT * FROM sncp_orcamento_ppi_anual AS SOPA
                       WHERE SOPA.name=dotacao.id AND SOPA.ano_planeado > $1)
                       LOOP
                          IF anual.montante > 0 THEN
                                  IF anual.ano_planeado-$1=1 THEN
                                     UPDATE sncp_orcamento_ppi_imprimir
                                     SET montante1=anual.montante
                                     WHERE id=imprimir_ppi_id;
                                  END IF;

                                  IF anual.ano_planeado-$1=2 THEN
                                     UPDATE sncp_orcamento_ppi_imprimir
                                     SET montante2=anual.montante
                                     WHERE id=imprimir_ppi_id;
                                  END IF;

                                  IF anual.ano_planeado-$1=3 THEN
                                     UPDATE sncp_orcamento_ppi_imprimir
                                     SET montante3=anual.montante
                                     WHERE id=imprimir_ppi_id;
                                  END IF;

                                  IF anual.ano_planeado-$1>=4 THEN
                                     montante_anos_seguintes= montante_anos_seguintes+anual.montante;
                                  END IF;
                          END IF;
                       END LOOP;

                               IF montante_anos_seguintes > 0.0 THEN
                                  UPDATE sncp_orcamento_ppi_imprimir
                          SET montante4=montante_anos_seguintes
                          WHERE id=imprimir_ppi_id;
                                   END IF;

                        END IF;
              END LOOP;
               END LOOP;
               RETURN TRUE;
          END;
          $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_calcula_definido(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION calcula_definido(ano integer,organica_id integer,economica_id integer,
        funcional integer)
        RETURNS numeric AS $$
        DECLARE
        dotacao numeric;
        reforco numeric;
        abate numeric;
        BEGIN

           dotacao=COALESCE((SELECT SUM(OL.reforco)
                            FROM sncp_orcamento_linha AS OL
                            WHERE OL.organica_id=$2 AND OL.economica_id=$3 AND OL.funcional_id=$4
                            AND OL.orcamento_id IN (SELECT id FROM sncp_orcamento AS SO
                            WHERE SO.titulo='desp' AND SO.tipo_orc='orc' AND SO.ano=$1)),0.0);

           reforco=COALESCE((SELECT SUM(OL.reforco)
                     FROM sncp_orcamento_linha AS OL
                     WHERE OL.organica_id=$2 AND OL.economica_id=$3 AND OL.funcional_id=$4
                             AND OL.orcamento_id IN (SELECT id FROM sncp_orcamento AS SO
                             WHERE SO.titulo='desp' AND SO.tipo_orc IN ('rev','alt') AND SO.ano=$1)),0.0);

           abate=COALESCE((SELECT SUM(OL.anulacao)
                       FROM sncp_orcamento_linha AS OL
                           WHERE OL.organica_id=$2 AND OL.economica_id=$3 AND OL.funcional_id=$4
                           AND OL.orcamento_id IN (SELECT id FROM sncp_orcamento AS SO
                           WHERE SO.titulo='desp' AND SO.tipo_orc IN ('rev','alt') AND SO.ano=$1)),0.0);

          RETURN dotacao+reforco-abate;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_calcula_despesa_definido_n_definido_total_geral_accao(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION calcula_despesa_definido_n_definido_total_geral_accao(ano integer) RETURNS BOOLEAN
        AS $$
        DECLARE
           ppi_accao sncp_orcamento_ppi_imprimir%ROWTYPE;

           desp_real numeric;
           definido numeric;
           n_definido numeric;
           tot_ger numeric;

        BEGIN
             FOR ppi_accao IN (SELECT * FROM sncp_orcamento_ppi_imprimir WHERE linha='accao')
             LOOP
                desp_real=(SELECT SUM(montante)
                           FROM sncp_orcamento_historico
                           WHERE name < $1 AND organica_id = ppi_accao.organica_id AND
                           economica_id = ppi_accao.economica_id AND funcional_id = ppi_accao.funcional_id AND
                           categoria = '09pagam');

                definido=calcula_definido($1,ppi_accao.organica_id,ppi_accao.economica_id,ppi_accao.funcional_id);

                IF ppi_accao.total-definido > 0.0 THEN
                   n_definido=ppi_accao.total-definido;
                ELSE
                   n_definido=NULL;
                END IF;

                IF definido=0.0 THEN
                   definido=NULL;
                END IF;

                tot_ger=COALESCE(desp_real,0.0) + COALESCE(ppi_accao.total,0.0) + COALESCE(ppi_accao.montante1,0.0) +
                        COALESCE(ppi_accao.montante2,0.0) + COALESCE(ppi_accao.montante3,0.0) +
                        COALESCE(ppi_accao.montante4,0.0);

                IF tot_ger=0.0 THEN
                   tot_ger=NULL;
                END IF;

                UPDATE sncp_orcamento_ppi_imprimir
                SET despesa_realizada=desp_real,
                definida=definido,n_definida=n_definido,total_geral=tot_ger
                WHERE id=ppi_accao.id;

             END LOOP;
             RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_insere_orcamento_ppi_imprimir_programas(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_orcamento_ppi_imprimir_programas()
        RETURNS BOOLEAN AS $$
        DECLARE
        cod_accao RECORD;
        descricao varchar;
        codigo_procura varchar;
        despesa_realizada numeric;
        total numeric;
        definida numeric;
        n_definida numeric;
        montante1 numeric;
        montante2 numeric;
        montante3 numeric;
        montante4 numeric;
        BEGIN
             FOR cod_accao IN (SELECT DISTINCT substring(SOPI.name from 1 for 5) AS prog
             FROM sncp_orcamento_ppi_imprimir AS SOPI WHERE SOPI.linha='accao')
             LOOP
               descricao=(SELECT SOPP.descricao FROM sncp_orcamento_ppi_programas AS SOPP
               WHERE SOPP.name=cod_accao.prog);
               INSERT INTO sncp_orcamento_ppi_imprimir(name,descricao,linha)
               VALUES(cod_accao.prog,descricao,'programa');

               codigo_procura=cod_accao.prog || '.%';

               despesa_realizada=(SELECT SUM(COALESCE(SOPI.despesa_realizada,0.0))
               FROM sncp_orcamento_ppi_imprimir AS SOPI WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='accao');

               total=(SELECT SUM(COALESCE(SOPI.total,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='accao');

               definida=(SELECT SUM(COALESCE(SOPI.definida,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='accao');

               n_definida=(SELECT SUM(COALESCE(SOPI.n_definida,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='accao');

               montante1=(SELECT SUM(COALESCE(SOPI.montante1,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='accao');

               montante2=(SELECT SUM(COALESCE(SOPI.montante2,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='accao');

               montante3=(SELECT SUM(COALESCE(SOPI.montante3,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='accao');

               montante4=(SELECT SUM(COALESCE(SOPI.montante4,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='accao');

               INSERT INTO sncp_orcamento_ppi_imprimir(name,descricao,despesa_realizada,total,definida,n_definida,
               montante1,montante2,montante3,montante4,linha)
               VALUES(cod_accao.prog || '.ZZZZZ','TOTAL DO PROGRAMA ' || cod_accao.prog,despesa_realizada,total,
               definida,n_definida,montante1,montante2,montante3,montante4,'subtotalprograma');
             END LOOP;
             RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;
            """)
        return True

    def sql_insere_orcamento_ppi_imprimir_objetivos(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_orcamento_ppi_imprimir_objetivos()
        RETURNS BOOLEAN AS $$
        DECLARE
        cod_programa RECORD;
        descricao varchar;
        codigo_procura varchar;
        despesa_realizada numeric;
        total numeric;
        definida numeric;
        n_definida numeric;
        montante1 numeric;
        montante2 numeric;
        montante3 numeric;
        montante4 numeric;
        BEGIN
             FOR cod_programa IN (SELECT DISTINCT substring(SOPI.name from 1 for 2) AS obj
             FROM sncp_orcamento_ppi_imprimir AS SOPI WHERE SOPI.linha='programa')
             LOOP
               descricao=(SELECT SOPO.descricao FROM sncp_orcamento_ppi_objetivos AS SOPO
               WHERE SOPO.name=cod_programa.obj);
               INSERT INTO sncp_orcamento_ppi_imprimir(name,descricao,linha)
               VALUES(cod_programa.obj,descricao,'objetivo');

               codigo_procura=cod_programa.obj || '.%';

               despesa_realizada=(SELECT SUM(COALESCE(SOPI.despesa_realizada,0.0))
               FROM sncp_orcamento_ppi_imprimir AS SOPI WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalprograma');

               total=(SELECT SUM(COALESCE(SOPI.total,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalprograma');

               definida=(SELECT SUM(COALESCE(SOPI.definida,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalprograma');

               n_definida=(SELECT SUM(COALESCE(SOPI.n_definida,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalprograma');

               montante1=(SELECT SUM(COALESCE(SOPI.montante1,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalprograma');

               montante2=(SELECT SUM(COALESCE(SOPI.montante2,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalprograma');

               montante3=(SELECT SUM(COALESCE(SOPI.montante3,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalprograma');

               montante4=(SELECT SUM(COALESCE(SOPI.montante4,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalprograma');

               INSERT INTO sncp_orcamento_ppi_imprimir(name,descricao,despesa_realizada,total,definida,n_definida,
               montante1,montante2,montante3,montante4,linha)
               VALUES(cod_programa.obj || '.ZZZZZZZZ','TOTAL DO OBJETIVO ' || cod_programa.obj,despesa_realizada,total,
               definida,n_definida,montante1,montante2,montante3,montante4,'subtotalobjetivo');
             END LOOP;
             RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def sql_insere_orcamento_ppi_imprimir_eixos(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_orcamento_ppi_imprimir_eixos()
        RETURNS BOOLEAN AS $$
        DECLARE
        cod_objetivo RECORD;
        descricao varchar;
        codigo_procura varchar;
        despesa_realizada numeric;
        total numeric;
        definida numeric;
        n_definida numeric;
        montante1 numeric;
        montante2 numeric;
        montante3 numeric;
        montante4 numeric;
        BEGIN
             FOR cod_objetivo IN (SELECT DISTINCT substring(SOPI.name from 1 for 1) AS eixo
             FROM sncp_orcamento_ppi_imprimir AS SOPI WHERE SOPI.linha='objetivo')
             LOOP
               descricao=(SELECT SOPE.descricao FROM sncp_orcamento_ppi_eixos AS SOPE
               WHERE SOPE.name=cod_objetivo.eixo);
               INSERT INTO sncp_orcamento_ppi_imprimir(name,descricao,linha)
               VALUES(cod_objetivo.eixo,descricao,'eixo');

               codigo_procura=cod_objetivo.eixo || '%';

               despesa_realizada=(SELECT SUM(COALESCE(SOPI.despesa_realizada,0.0))
               FROM sncp_orcamento_ppi_imprimir AS SOPI WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalobjetivo');

               total=(SELECT SUM(COALESCE(SOPI.total,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalobjetivo');

               definida=(SELECT SUM(COALESCE(SOPI.definida,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalobjetivo');

               n_definida=(SELECT SUM(COALESCE(SOPI.n_definida,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalobjetivo');

               montante1=(SELECT SUM(COALESCE(SOPI.montante1,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalobjetivo');

               montante2=(SELECT SUM(COALESCE(SOPI.montante2,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalobjetivo');

               montante3=(SELECT SUM(COALESCE(SOPI.montante3,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalobjetivo');

               montante4=(SELECT SUM(COALESCE(SOPI.montante4,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
               WHERE SOPI.name LIKE codigo_procura
                          AND SOPI.linha='subtotalobjetivo');

               INSERT INTO sncp_orcamento_ppi_imprimir(name,descricao,despesa_realizada,total,definida,n_definida,
               montante1,montante2,montante3,montante4,linha)
               VALUES(cod_objetivo.eixo || 'ZZZZZZZZZZ','TOTAL DO EIXO ' || cod_objetivo.eixo,despesa_realizada,total,
               definida,n_definida,montante1,montante2,montante3,montante4,'subtotaleixo');
             END LOOP;
             RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;
        """)

        return True

    def sql_insere_orcamento_ppi_imprimir_total_geral(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION insere_orcamento_ppi_imprimir_total_geral()
        RETURNS BOOLEAN AS $$
        DECLARE
        despesa_realizada numeric;
        total numeric;
        definida numeric;
        n_definida numeric;
        montante1 numeric;
        montante2 numeric;
        montante3 numeric;
        montante4 numeric;
        BEGIN
        despesa_realizada=(SELECT SUM(COALESCE(SOPI.despesa_realizada,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
        WHERE SOPI.linha='subtotaleixo');

        total=(SELECT SUM(COALESCE(SOPI.total,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
        WHERE SOPI.linha='subtotaleixo');

        definida=(SELECT SUM(COALESCE(SOPI.definida,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
        WHERE SOPI.linha='subtotaleixo');

        n_definida=(SELECT SUM(COALESCE(SOPI.n_definida,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
        WHERE SOPI.linha='subtotaleixo');

        montante1=(SELECT SUM(COALESCE(SOPI.montante1,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
        WHERE SOPI.linha='subtotaleixo');

        montante2=(SELECT SUM(COALESCE(SOPI.montante2,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
        WHERE SOPI.linha='subtotaleixo');

        montante3=(SELECT SUM(COALESCE(SOPI.montante3,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
        WHERE SOPI.linha='subtotaleixo');

        montante4=(SELECT SUM(COALESCE(SOPI.montante4,0.0)) FROM sncp_orcamento_ppi_imprimir AS SOPI
        WHERE SOPI.linha='subtotaleixo');

        INSERT INTO sncp_orcamento_ppi_imprimir(name,descricao,despesa_realizada,total,definida,n_definida,montante1,
        montante2,montante3,montante4,linha)
        VALUES('ZZZZZZZZZZZZ','TOTAL GERAL',despesa_realizada,total,definida,n_definida,montante1,montante2,
        montante3,montante4,'totalgeral');

        RETURN TRUE;
        END
        $$ LANGUAGE plpgsql;
        """)
        return True

    def create(self, cr, uid, vals, context=None):
        db_sncp_orcamento_ppi_programas = self.pool.get('sncp.orcamento.ppi.programas')
        db_sncp_orcamento_ppi_eixos = self.pool.get('sncp.orcamento.ppi.eixos')
        db_sncp_orcamento_ppi_objetivos = self.pool.get('sncp.orcamento.ppi.objetivos')

        self.teste_existencia_ppi_accoes(cr)

        if 'name' not in vals:
            obj_eixo = db_sncp_orcamento_ppi_eixos.browse(cr, uid, vals['eixo_id'])
            obj_objetivo = db_sncp_orcamento_ppi_objetivos.browse(cr, uid, vals['objetivo_id'])
            obj_programa = db_sncp_orcamento_ppi_programas.browse(cr, uid, vals['programa_id'])

            if obj_eixo.name == obj_objetivo.name[:1] and obj_objetivo.name == obj_programa.name[:2]:
                vals['name'] = obj_programa.name
            else:
                raise osv.except_osv(_(u'Aviso'), _(u'Defina o eixo/objetivo/programa corretamente.'))

        codigo_funcional = unicode(vals['name']) + unicode(vals['name2'])

        cr.execute("""
        SELECT id FROM account_analytic_account
        WHERE code='%s' and tipo_dim='cf' and type='normal'
        """ % codigo_funcional)

        funcional_id = cr.fetchone()

        if funcional_id is not None:
            vals['funcional_id'] = funcional_id[0]

        return super(sncp_orcamento_ppi_accoes, self).create(cr, uid, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):

        cr.execute("""
        DELETE FROM sncp_orcamento_ppi_anual
        WHERE name IN (SELECT id FROM sncp_orcamento_ppi_dotacoes WHERE accoes_id=%d)
        """ % ids[0])

        cr.execute("""
        DELETE FROM sncp_orcamento_ppi_dotacoes
        WHERE accoes_id=%d
        """ % ids[0])

        return super(sncp_orcamento_ppi_accoes, self).unlink(cr, uid, ids, context=context)

    _order = 'name,name2'

    _sql_constraints = [
        ('ppi_accao_unique', 'unique (name,name2)', u'Acção já existente!')
    ]

    def _datas_validas(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        if obj.inicio:
            if obj.fim:
                if obj.inicio >= obj.fim:
                    raise osv.except_osv(_(u'Aviso'), _(u'Data inicial inferior à data final.'))

        return True

    def _name2_valido(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        ok = False

        if len(obj.name2) < 5:
            raise osv.except_osv(_(u'Aviso'), _(u'O código parcial deve ter comprimento 5.'))

        for i in range(0, len(obj.name2)):
            if i == 0 and obj.name2[i] == u'.':
                ok = True
            elif ord(obj.name2[i]) in range(48, 58) or ord(obj.name2[i]) in range(65, 91):
                ok = True
            else:
                ok = False
                break

        if ok is False:
            raise osv.except_osv(_(u'Aviso'), _(u'O código parcial da acção deve estar entre .0000 e .ZZZZ'
                                                u' contendo apenas algarismos e maiúsculas e o .!'))

        return True

    def _funcional_valida(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        if obj.name and obj.name2:
            if obj.eixo_id.name == obj.objetivo_id.name[:1] and obj.objetivo_id.name == obj.programa_id.name[:2]:
                codigo_funcional = unicode(obj.name) + unicode(obj.name2)
                cr.execute("""
                            SELECT id
                            FROM account_analytic_account
                            WHERE code='%s' and tipo_dim='cf' and type='normal'
                            """ % codigo_funcional)
                funcional_id = cr.fetchone()

                if funcional_id is None:
                    raise osv.except_osv(_(u'Aviso'), _(u'Não existe conta analítica funcional com este código.'))
            else:
                raise osv.except_osv(_(u'Aviso'), _(u'Escolha o eixo/objetivo/programa corretamente.'))

        elif not obj.name:
            raise osv.except_osv(_(u'Aviso'), _(u'Defina o eixo/objetivo/programa.'))

        return True

    def _fonte_perc_valido(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        if obj.fonte == 'Sf' and obj.percent != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Para fonte "Sem Financiamento" a percentagem deve ser 0.'))

        return True

    def _perc_positiva_valida(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        if obj.percent < 0:
            raise osv.except_osv(_(u'Aviso'), _(u'A percentagem deve ser positiva.'))

        return True

    _constraints = [
        (_datas_validas, u'', ['inicio', 'fim']),
        (_fonte_perc_valido, u'', ['fonte', 'percent']),
        (_perc_positiva_valida, u'', ['percent']),
        (_name2_valido, u'', ['name2']),
        (_funcional_valida, u'', ['name', 'name2']),
    ]


sncp_orcamento_ppi_accoes()
# ___________________________________________________ PPI ECONOMICAS ___________________________________


class sncp_orcamento_ppi_dotacoes(osv.Model):
    _name = 'sncp.orcamento.ppi.dotacoes'

    _columns = {
        'name': fields.many2one('account.analytic.account', u'Económica',
                                domain=[('tipo_dim', '=', 'ce'), ('type', '=', 'normal')]),
        'anos_id': fields.one2many('sncp.orcamento.ppi.anual', 'name',
                                   string=u'Anos'),
        'accoes_id': fields.many2one('sncp.orcamento.ppi.accoes'),
    }

    _order = 'name'

    _sql_constraints = [
        ('ppi_dotacao_unique', 'unique (name,accoes_id)', u'Económica já está registada!')
    ]

    def unlink(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])

        cr.execute("""
        SELECT id
        FROM sncp_orcamento_ppi_dotacoes
        WHERE accoes_id=%d and id != %d
        """ % (obj.accoes_id.id, obj.id))

        dotacoes_id = cr.fetchall()

        if len(dotacoes_id) == 0:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'Deve ter pelo menos uma conta analítica com a classificação económica.'))

        cr.execute("""
        DELETE FROM sncp_orcamento_ppi_anual
        WHERE name=%d
        """ % ids[0])

        return super(sncp_orcamento_ppi_dotacoes, self).unlink(cr, uid, ids, context=context)

sncp_orcamento_ppi_dotacoes()


# ___________________________________________________ PPI FONTES _______________________________________
class sncp_orcamento_ppi_anual(osv.Model):
    _name = 'sncp.orcamento.ppi.anual'
    _description = u"PPI Anual"

    _columns = {
        'name': fields.many2one('sncp.orcamento.ppi.dotacoes', u'PPI'),
        'ano_planeado': fields.integer(u'Ano planeado'),
        'montante': fields.float(u'Valor', digits=(12, 2)),
        'dummy': fields.char(u''),
    }

    _order = 'ano_planeado'

    _sql_constraints = [
        ('ppi_anual_unique', 'unique (ano_planeado,name)', u'Ano Planeado já está registado!')
    ]

    def _montante_positivo(self, cr, uid, ids, contect=None):
        obj = self.browse(cr, uid, ids[0])

        if obj.montante < 0.0:
            raise osv.except_osv(_(u'Aviso'), _(u'O montante não pode ser negativo.'))

        return True

    _constraints = [
        (_montante_positivo, u'', ['montante']),
    ]


sncp_orcamento_ppi_anual()


class sncp_orcamento_ppi(osv.Model):
    _name = 'sncp.orcamento.ppi'

    def imprimir_report(self, cr, uid, ids, context=None):
        cr.execute("""
        DELETE FROM sncp_orcamento_ppi WHERE id < %d
        """ % ids[0])

        cr.execute("""
        DELETE FROM sncp_orcamento_ppi_imprimir
        """)

        obj = self.browse(cr, uid, ids[0])

        cr.execute("""
        SELECT id
        FROM sncp_orcamento_ppi_accoes
        """)

        accoes_id = cr.fetchall()

        # VERIFICAR SE HÁ ACÇÕES SEM DOTAÇÕES
        for accao in accoes_id:
            cr.execute("""
             SELECT id
             FROM sncp_orcamento_ppi_dotacoes
             WHERE accoes_id=%d
             """ % accao[0])

            dotacoes_ids = cr.fetchall()
            if len(dotacoes_ids) == 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Existem acções sem dotações definidas.'))

        cr.execute("""
        SELECT DISTINCT PAC.id
        FROM sncp_orcamento_ppi_accoes AS PAC
        INNER JOIN sncp_orcamento_ppi_dotacoes AS OD ON OD.accoes_id=PAC.id
        INNER JOIN sncp_orcamento_ppi_anual AS PAN ON PAN.name=OD.id
        WHERE PAN.ano_planeado=%d
        """ % obj.name)

        accoes_ids = cr.fetchall()
        if len(accoes_ids) != 0:
            cr.execute("""
            SELECT insere_orcamento_ppi_imprimir_accoes(%d);
            """ % obj.name)

            cr.execute("""
            SELECT id
            FROM sncp_orcamento_ppi_imprimir
            """)

            ppis_ids = cr.fetchall()
            if len(ppis_ids) == 0:
                return True

            cr.execute("""
            SELECT calcula_despesa_definido_n_definido_total_geral_accao(%d);
            """ % obj.name)

            cr.execute("""
            SELECT insere_orcamento_ppi_imprimir_programas();
            """)

            cr.execute("""
            SELECT insere_orcamento_ppi_imprimir_objetivos();
            """)

            cr.execute("""
            SELECT insere_orcamento_ppi_imprimir_eixos();
            """)

            cr.execute("""
            SELECT insere_orcamento_ppi_imprimir_total_geral();
            """)

            ppis_ids = [elem[0] for elem in ppis_ids]

            datas = {'ids': ppis_ids, 'model': 'sncp.orcamento.ppi.imprimir', }

            return {
                'type': 'ir.actions.report.xml',
                'nodestroy': True,
                'report_name': 'sncp.orcamento.ppi.imprimir.report',
                'datas': datas,
            }

        return True

    _columns = {
        'name': fields.integer(u'Ano', size=4)
    }
sncp_orcamento_ppi()


class sncp_orcamento_ppi_imprimir(osv.Model):
    _name = 'sncp.orcamento.ppi.imprimir'

    _columns = {
        'name': fields.char(u'Código do eixo/objetivo/programa/accao/subtotais'),
        'descricao': fields.char(u'Descricao'),
        'funcional_id': fields.integer(u'Orgânica'),
        'responsavel': fields.char(u'Responsável'),
        'realizacao': fields.char(u'Forma de Realização'),
        'execucao': fields.char(u'Fase de Execução'),
        'data_ini': fields.char(u'Data de início'),
        'data_fim': fields.char(u'Data de fim'),
        'organica_code': fields.char(u'Código da orgânica'),
        'organica_id': fields.integer(u'Orgânica'),
        'fonte_financ': fields.char(u'Fonte de financiamento'),
        'perc_financ': fields.integer(u'Percentagem de financiamento'),
        'economica_code': fields.char(u'Código Económica'),
        'economica_id': fields.integer(u'Económica'),
        'despesa_realizada': fields.float(u'Despesa realizada', digits=(12, 2)),
        'total': fields.float(u'Total', digits=(12, 2)),
        'definida': fields.float(u'Definida', digits=(12, 2)),
        'n_definida': fields.float(u'Não definida', digits=(12, 2)),
        'total_geral': fields.float(u'Total Geral', digits=(12, 2)),
        'montante1': fields.float(u'Montante 1', digits=(12, 2)),
        'montante2': fields.float(u'Montante 2', digits=(12, 2)),
        'montante3': fields.float(u'Montante 3', digits=(12, 2)),
        'montante4': fields.float(u'Montante 4', digits=(12, 2)),
        'linha': fields.char(u'Secção'),
    }


sncp_orcamento_ppi_imprimir()