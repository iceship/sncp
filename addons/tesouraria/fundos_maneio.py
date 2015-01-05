# -*- encoding: utf-8 -*-
##############################################################################
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

from datetime import datetime
import decimal
from decimal import *
from openerp.osv import fields, osv
from openerp.tools.translate import _

# ________________________________________________________________FUNDOS DE MANEIO________________________


class sncp_tesouraria_fundos_maneio(osv.Model):
    _name = 'sncp.tesouraria.fundos.maneio'
    _description = u"Fundos de Maneio"

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'codigo'], context=context)
        res = []
        for record in reads:
            name = 'Fundo Maneio' + ' - ' + record['codigo']
            res.append((record['id'], name))
        return res

    def on_change_codigo(self, cr, uid, ids, codigo):
        if len(ids) != 0:
            self.write(cr, uid, ids, {'codigo': codigo.upper()})
        return {'value': {'codigo': codigo.upper()}}

    _rec_name = 'codigo'

    _columns = {
        'codigo': fields.char(u'Código do Fundo de Maneio', size=5),
        'name': fields.char(u'Descrição'),
        'empregado_id': fields.many2one('hr.employee', u'Responsável'),
        'conta_id': fields.many2one('account.account', u'Conta Patrimonial',
                                    domain=[('type', 'not in', ['view'])]),
        'diario_id': fields.many2one('account.journal', u'Diário'),
        'ativo': fields.boolean(u'Ativo'),
        'saldo': fields.float(u'Saldo', digits=(12, 2))
    }

    def create(self, cr, uid, vals, context=None):
        return super(sncp_tesouraria_fundos_maneio, self).create(cr, uid, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        cr.execute("""
        SELECT id
        FROM sncp_despesa_pagamentos_ordem
        WHERE fundo_id = %d
        """ % ids[0])

        ordem_pagamentos = cr.fetchall()

        if len(ordem_pagamentos) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode eliminar este fundo pois existem ordens'
                                                u' de pagamento associadas a este fundo.'))

        cr.execute("""
        SELECT id
        FROM sncp_tesouraria_movimentos
        WHERE fmaneio_id = %d
        """ % ids[0])

        movim_fundos_maneio = cr.fetchall()

        if len(movim_fundos_maneio) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode eliminar este fundo pois existem movimentos'
                                                u' de tesouraria associados a este fundo.'))

        cr.execute("""
        SELECT id
        FROM sncp_tesouraria_movim_fundos_maneio
        WHERE name = %d
        """ % ids[0])

        movim_fundos_maneio = cr.fetchall()

        if len(movim_fundos_maneio) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode eliminar este fundo pois existem movimentos'
                                                u' de fundos de maneio associados a este fundo.'))

        cr.execute("""
        SELECT id
        FROM sncp_tesouraria_movim_internos
        WHERE orig_fmaneio_id = %d OR dest_fmaneio_id = %d
        """ % (ids[0], ids[0]))

        movim_internos = cr.fetchall()

        if len(movim_internos) != 0:
            raise osv.except_osv(_(u'Aviso'), _(u'Não pode eliminar este fundo pois existem movimentos'
                                                u' internos associados a este fundo.'))

        return super(sncp_tesouraria_fundos_maneio, self).unlink(cr, uid, ids, context=context)

    _order = 'codigo'

    _sql_constraints = [
        ('fundo_codigo_unique', 'unique (codigo)', u'Fundo de Maneio com este código já está registado!')
    ]

sncp_tesouraria_fundos_maneio()
# ___________________________________RELAÇÃO TIPOS DE MOV (TESOUR -- FUNDOS DE MANEIO)________________________


class sncp_tesouraria_fundos_maneio_rel(osv.Model):
    _name = 'sncp.tesouraria.fundos.maneio.rel'
    _description = u"Relação Tipos de Movimento"

    _columns = {
        'name': fields.many2one('sncp.tesouraria.tipo.mov', u'Tipo de Movimento de Tesouraria'),
        'tipo_mov_fm': fields.selection([('con', u'Constituição'),
                                         ('rec', u'Reconstituição'),
                                         ('rep', u'Reposição')], u'Tipo de Movimento'),
        'campo': fields.char(u'', size=20),
    }

    _order = 'name'

    _sql_constraints = [
        ('tipo_mov_tes_unique', 'unique (name)',
         u'Este Tipo de Movimento já está associado a um Movimento do Fundo de Maneio!')
    ]

sncp_tesouraria_fundos_maneio_rel()
# _______________________________________________MOVIMENTOS DOS FUNDOS DE MANEIO___________________________


class sncp_tesouraria_movim_fundos_maneio(osv.Model):
    _name = 'sncp.tesouraria.movim.fundos.maneio'
    _description = u"Movimentos de Fundos de Maneio"

    def prosseguir(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'estado': 1})
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def on_change_tipo_mov_tes_id(self, cr, uid, ids, tipo_mov_tes_id):
        de_sncp_tesouraria_fundos_maneio_rel = self.pool.get('sncp.tesouraria.fundos.maneio.rel')
        rel_id = de_sncp_tesouraria_fundos_maneio_rel.search(cr, uid, [('name', '=', tipo_mov_tes_id)])
        obj = self.browse(cr, uid, ids[0])
        if len(rel_id) == 0:
            return {
                'value': {'tipo_mov_tes_id': 0},
                'warning': {'title': u'Aviso',
                            'message': u'Este tipo de movimento de tesouraria não está definido na tabela '
                                       u'Tesouraria/Configurações/Tipos de Movimento FM.'}
            }
        else:
            obj_rel = de_sncp_tesouraria_fundos_maneio_rel.browse(cr, uid, rel_id[0])

            # Bloco de verificação de ordem
            if obj_rel.tipo_mov_fm == 'con':
                cr.execute("""SELECT tipo_mov_fm FROM sncp_tesouraria_movim_fundos_maneio
                    WHERE name = %d
                    ORDER BY id DESC """ % obj.name.id)
                tipo_mov_fm = cr.fetchall()
                if len(tipo_mov_fm) == 1:
                    pass
                elif tipo_mov_fm[1][0] == 'con' or tipo_mov_fm[1][0] == 'rec':
                    raise osv.except_osv(_(u'Aviso'), _(u'Não pode constituir este Fundo de maneio, '
                                                        u'porque o mesmo já se encontra constituído.'))
            elif obj_rel.tipo_mov_fm == 'rep':
                cr.execute("""SELECT tipo_mov_fm FROM sncp_tesouraria_movim_fundos_maneio
                    WHERE name = %d
                    ORDER BY id DESC  """ % obj.name.id)
                tipo_mov_fm = cr.fetchall()
                if len(tipo_mov_fm) == 1:
                    raise osv.except_osv(_(u'Aviso'), _(u'Não pode repor este Fundo de maneio, '
                                                        u'porque o mesmo não está constituído.'))
                elif tipo_mov_fm[1][0] == 'rep':
                    raise osv.except_osv(_(u'Aviso'), _(u'Não pode repor este Fundo de maneio, '
                                                        u'porque o mesmo já se encontra reposto.'))
            elif obj_rel.tipo_mov_fm == 'rec':
                cr.execute("""
                    SELECT tipo_mov_fm FROM sncp_tesouraria_movim_fundos_maneio
                    WHERE name = %d
                    ORDER BY id DESC
                """ % obj.name.id)
                tipo_mov_fm = cr.fetchall()
                if len(tipo_mov_fm) == 1:
                    raise osv.except_osv(_(u'Aviso'), _(u'Não pode reconstituir este Fundo de maneio, '
                                                        u'porque o mesmo não está constituído.'))
                elif tipo_mov_fm[1][0] == 'rep':
                    raise osv.except_osv(_(u'Aviso'), _(u'Não pode reconstituir este Fundo de maneio, '
                                                        u'porque o mesmo já se encontra reposto.'))

            # Bloco de processamento
            #  Verificação de constituição
            if obj_rel.tipo_mov_fm == 'con':
                if obj.name.saldo != 0:
                    raise osv.except_osv(_(u'Aviso'), _(u'Não pode constituir este Fundo de maneio, '
                                                        u'porque o mesmo têm saldo positivo.'))
                self.write(cr, uid, ids, {'estado': 3, 'tipo_mov_fm': obj_rel.tipo_mov_fm,
                                          'tipo_mov_tes_id':  tipo_mov_tes_id})
                return self.constituicao(cr, uid, ids)
            # Verificação de reposição
            elif obj_rel.tipo_mov_fm == 'rep':
                self.write(cr, uid, ids, {'estado': 4, 'tipo_mov_fm': obj_rel.tipo_mov_fm,
                                          'tipo_mov_tes_id':  tipo_mov_tes_id})
                return self.reposicao(cr, uid, ids)
            else:
                self.write(cr, uid, ids, {'estado': 2, 'tipo_mov_fm': obj_rel.tipo_mov_fm,
                                          'tipo_mov_tes_id':  tipo_mov_tes_id})
                return {
                    'value': {'tipo_mov_fm': obj_rel.tipo_mov_fm, 'estado': 2}
                }

    def select_op(self, cr, uid, ids, context):
        # A constituição esta feita no on_change_tipo_mov_tes_id
        db_formulario_sncp_tesouraria_movim_fm = self.pool.get('formulario.sncp.tesouraria.movim.fm')
        obj = self.browse(cr, uid, ids[0])
        result = None
        # Reconstituição
        if obj.tipo_mov_fm == 'rec':
            cr.execute("""
                SELECT OP.id, OP.montante_iliq, OP.montante_desc, OP.montante_ret, OP.name
                FROM sncp_despesa_pagamentos_ordem AS OP
                WHERE OP.fundo_id = %d AND OP.state = 'pag' AND OP.id not in
                  (SELECT rel.ordem_pag_id FROM sncp_tesouraria_movim_fm_rel as rel)
            """ % obj.name.id)
            result = cr.fetchall()
            if len(result) == 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Nenhum montante a reconstituir.'))
        return db_formulario_sncp_tesouraria_movim_fm.wizard(cr, uid, ids, result)

    def atualiza_montante(self, cr, uid, ids, vals):
        self.write(cr, uid, ids, {'montante': vals['montante'], 'estado': 4})
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def reposicao(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        # Montante
        cr.execute("""
            SELECT COALESCE(montante ,0.0) FROM sncp_tesouraria_movim_fundos_maneio
            WHERE name = %d AND tipo_mov_fm = 'con'
            ORDER BY id DESC
            """ % obj.name.id)
        montante = cr.fetchone()[0]
        # OP's pagas pelo fundo
        cr.execute("""
            SELECT COALESCE(
              SUM(OP.montante_iliq - OP.montante_desc  - OP.montante_ret), 0.0)
            FROM sncp_despesa_pagamentos_ordem AS OP
            WHERE OP.fundo_id = %d AND OP.state = 'pag' AND OP.id not in
              (SELECT rel.ordem_pag_id FROM sncp_tesouraria_movim_fm_rel as rel)
        """ % obj.name.id)
        montante_op = cr.fetchone()[0]

        aux = decimal.Decimal(unicode(montante-montante_op))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_dif_op = float(aux)

        self.write(cr, uid, ids, {'montante': montante_dif_op})
        return {'value': {'tipo_mov_fm': 'rep', 'estado': 4, 'montante': montante_dif_op}
                }

    def constituicao(self, cr, uid, ids):

        return {'value': {'tipo_mov_fm': 'con', 'estado': 3}
                }

    def processa_fundo_maneio(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        db_ir_sequence = self.pool.get('ir.sequence')
        db_account_journal = self.pool.get('account.journal')
        db_account_move = self.pool.get('account.move')
        db_account_move_line = self.pool.get('account.move.line')
        db_sncp_tesouraria_movimentos = self.pool.get('sncp.tesouraria.movimentos')
        db_sncp_tesouraria_movim_fm_rel = self.pool.get('sncp.tesouraria.movim.fm.rel')
        db_sncp_tesouraria_fundos_maneio = self.pool.get('sncp.tesouraria.fundos.maneio')

        # Movimento contabilistico:
        if obj.tipo_mov_fm in ['con']:
            if obj.montante == 0.0:
                raise osv.except_osv(_(u'Aviso'), _(u'O montante têm que ser diferente de 0.'))
            referencia = u'Constituição '+unicode(obj.name.name)
        elif obj.tipo_mov_fm in ['rep']:
            referencia = u'Reposição '+unicode(obj.name.name)
        else:
            referencia = u'Reconstituição '+unicode(obj.name.name)
        datahora = datetime.strptime(obj.data_mov, "%Y-%m-%d %H:%M:%S")
        dicti = db_account_move.account_move_prepare(cr, uid, obj.name.diario_id.id, datahora.date(), referencia)
        obj_jornal = db_account_journal.browse(cr, uid, obj.name.diario_id.id)
        if obj_jornal.sequence_id.id:
            name = db_ir_sequence.next_by_id(cr, uid, obj_jornal.sequence_id.id)
        else:
            raise osv.except_osv(_(u'Aviso'), _(u'O diário '+unicode(obj_jornal.name)+
                                                u' não têm sequência de movimentos associada.'))
        dicti['name'] = name
        move_id = db_account_move.create(cr, uid, dicti)
        self.write(cr, uid, ids, {'movimento_id': move_id})

        if obj.tipo_mov_fm in ['con', 'rec']:
            db_account_move_line.create(cr, uid, {'account_id': obj.name.conta_id.id,
                                                  'date': dicti['date'], 'journal_id': dicti['journal_id'],
                                                  'period_id': dicti['period_id'], 'name': dicti['ref'],
                                                  'move_id': move_id, 'debit': obj.montante, })
            # Conta de passagem
            if obj.tipo_mov_tes_id.conta_id.id:
                db_account_move_line.create(cr, uid, {'account_id': obj.tipo_mov_tes_id.conta_id.id,
                                                      'date': dicti['date'], 'journal_id': dicti['journal_id'],
                                                      'period_id': dicti['period_id'], 'name': dicti['ref'],
                                                      'move_id': move_id, 'credit': obj.montante, })
                db_account_move_line.create(cr, uid, {'account_id': obj.tipo_mov_tes_id.conta_id.id,
                                                      'date': dicti['date'], 'journal_id': dicti['journal_id'],
                                                      'period_id': dicti['period_id'], 'name': dicti['ref'],
                                                      'move_id': move_id, 'debit': obj.montante, })
            db_account_move_line.create(cr, uid, {'account_id': obj.caixa_id.conta_id.id,
                                                  'date': dicti['date'], 'journal_id': dicti['journal_id'],
                                                  'period_id': dicti['period_id'], 'name': dicti['ref'],
                                                  'move_id': move_id, 'credit': obj.montante, })
        else:
            db_account_move_line.create(cr, uid, {'account_id': obj.caixa_id.conta_id.id,
                                                  'date': dicti['date'], 'journal_id': dicti['journal_id'],
                                                  'period_id': dicti['period_id'], 'name': dicti['ref'],
                                                  'move_id': move_id, 'debit': obj.montante, })
            # Conta de passagem
            if obj.tipo_mov_tes_id.conta_id.id:
                db_account_move_line.create(cr, uid, {'account_id': obj.tipo_mov_tes_id.conta_id.id,
                                                      'date': dicti['date'], 'journal_id': dicti['journal_id'],
                                                      'period_id': dicti['period_id'], 'name': dicti['ref'],
                                                      'move_id': move_id, 'credit': obj.montante, })
                db_account_move_line.create(cr, uid, {'account_id': obj.tipo_mov_tes_id.conta_id.id,
                                                      'date': dicti['date'], 'journal_id': dicti['journal_id'],
                                                      'period_id': dicti['period_id'], 'name': dicti['ref'],
                                                      'move_id': move_id, 'debit': obj.montante, })
            db_account_move_line.create(cr, uid, {'account_id': obj.name.conta_id.id,
                                                  'date': dicti['date'], 'journal_id': dicti['journal_id'],
                                                  'period_id': dicti['period_id'], 'name': dicti['ref'],
                                                  'move_id': move_id, 'credit': obj.montante, })
        # Reconstituição -- relações
        if obj.tipo_mov_fm in ['rec']:
            cr.execute("""SELECT ordem_pag_id FROM formulario_sncp_tesouraria_movim_fm_wizard
                WHERE movim_fm_id = %d and selec = TRUE""" % ids[0])
            result_op_ids = cr.fetchall()
            for op_id in result_op_ids:
                db_sncp_tesouraria_movim_fm_rel.create(cr, uid, {
                    'movim_fm_id': ids[0],
                    'ordem_pag_id': op_id[0],
                })
            # Destroi as linhas do wizard
            cr.execute("""SELECT form_id FROM formulario_sncp_tesouraria_movim_fm_wizard
                    WHERE movim_fm_id = %d
                    LIMIT 1""" % (ids[0]))
            form_id = cr.fetchone()[0]
            cr.execute("""DELETE FROM formulario_sncp_tesouraria_movim_fm_wizard
                          WHERE form_id =%d            """ % form_id)
            cr.execute("""DELETE FROM formulario_sncp_tesouraria_movim_fm
                          WHERE id = %d            """ % form_id)

        # Cria Movimento de tesouraria
        caixa_id = [0, 0]
        banco_id = [0, 0]
        fmaneio_id = [0, 0]
        if obj.tipo_mov_fm in ['con', 'rec']:
            caixa_id[0] = obj.caixa_id.id
            fmaneio_id[1] = obj.name.id
        else:
            caixa_id[1] = obj.caixa_id.id
            fmaneio_id[0] = obj.name.id

        values = {'datahora': datahora,
                  'name': name,
                  'montante': obj.montante,
                  'em_cheque': 0.0,
                  'montante_ot': 0,
                  'origem': 'movtes',
                  'origem_id': obj.tipo_mov_tes_id.id,
                  'caixa_id': caixa_id,
                  'banco_id': banco_id,
                  'fmaneio_id': fmaneio_id, }
        db_sncp_tesouraria_movimentos.cria_movimento_tesouraria(cr, uid, ids, values)

        # Atualiza saldo FM
        if obj.tipo_mov_fm in ['con', 'rec']:
            montante = obj.montante
        else:
            montante = -obj.montante
        obj_maneio = db_sncp_tesouraria_fundos_maneio.browse(cr, uid, obj.name.id)

        aux = decimal.Decimal(unicode(obj_maneio.saldo+montante))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_maneio = float(aux)

        db_sncp_tesouraria_fundos_maneio.write(cr, uid, obj.name.id, {'saldo': montante_maneio})
        self.write(cr, uid, ids, {'estado': 5})
        return self.imprimir(cr, uid, ids, context)

    def imprimir(self, cr, uid, ids, context):
        datas = {'ids': ids,
                 'model': 'sncp.tesouraria.movim.fundos.maneio', }
        return {
            'type': 'ir.actions.report.xml',
            'nodestroy': True,
            'report_name': 'sncp.tesouraria.movim.fundos.maneio.report',
            'datas': datas,
        }

    def eliminar(self, cr, uid, ids, context):
        # A determinação de movimentos que podem ser eliminados ocorre na função
        # tesouraria/mapas/sncp_tesouraria_folha_caixa.encerra_folha()
        db_sncp_tesouraria_fundos_maneio = self.pool.get('sncp.tesouraria.fundos.maneio')
        obj = self.browse(cr, uid, ids[0])
        # Apagar os movimentos
        mov_id = obj.movimento_id.id
        nome = obj.movimento_id.name
        if mov_id is False:
            return self.unlink(cr, uid, ids)

        cr.execute("""SELECT montante, natureza FROM sncp_tesouraria_movimentos
                    WHERE name = '%s' AND meio = 'fm' """ % nome)
        result = cr.fetchone()
        cr.execute("""DELETE FROM sncp_tesouraria_movimentos WHERE name = '%s'""" % nome)

        # Atualizar saldo FM
        if result is not None:
            if result[1] in ['entra']:
                montante = - result[0]
            else:
                montante = result[0]
        else:
            montante = 0.0

        obj_maneio = db_sncp_tesouraria_fundos_maneio.browse(cr, uid, obj.name.id)

        aux = decimal.Decimal(unicode(obj_maneio.saldo+montante))
        aux = aux.quantize(Decimal('0.01'), ROUND_HALF_UP)
        montante_maneio = float(aux)

        db_sncp_tesouraria_fundos_maneio.write(cr, uid, obj.name.id, {'saldo': montante_maneio})

        # Reconstituição apaga relação
        if obj.tipo_mov_fm == 'rec':
            cr.execute("""DELETE FROM sncp_tesouraria_movim_fm_rel WHERE movim_fm_id = %d""" % ids[0])

        # Apaga movimento contabilistico
        cr.execute("""SELECT id FROM account_move WHERE name = '%s'""" % nome)
        move_id = cr.fetchone()

        if move_id is not None:
            cr.execute("""DELETE FROM account_move_line WHERE move_id = %d""" % move_id)
            cr.execute("""DELETE FROM account_move WHERE id = %d""" % move_id)

        return self.unlink(cr, uid, ids)

    _columns = {
        'name': fields.many2one('sncp.tesouraria.fundos.maneio', u'Fundo de maneio',
                                domain=[('ativo', '=', True)]),
        'codigo': fields.related('name', 'codigo', type="char", store=True, string=u'Código'),
        'desc': fields.related('name', 'name', type="char", store=True, string=u'Descrição'),
        'empregado_id': fields.related('name', 'empregado_id', 'resource_id', 'name', type="char", store=True,
                                       string=u'Responsável'),
        'data_mov': fields.datetime(u'Data de Movimento'),
        'tipo_mov_fm': fields.selection([('con', u'Constituição'),
                                         ('rec', u'Reconstituição'),
                                         ('rep', u'Reposição')], u'Tipo de Movimento'),
        'tipo_mov_tes_id': fields.many2one('sncp.tesouraria.tipo.mov', u'Tipo de Movimento de Tesouraria'),
        'montante': fields.float(u'Montante', digits=(12, 2)),
        'caixa_id': fields.many2one('sncp.tesouraria.caixas', u'Caixa'),
        'movimento_id': fields.many2one('account.move', u'Movimento Contábil'),
        # Variaveis do estado
        'estado': fields.integer(u'Responsável de readonly dos campos e botões'),
        # 0 -- editaveis
        # 1 -- readonly
        # 2 -- botão "Seleccionar OP"
        # 3 -- constituição\
        #                   processar
        # 4 -- não da nada /
        # 5 -- fechado pode ser eliminado
        # 6 -- fechado e não pode ser eliminado
    }

    def sql_fu_extenso_euro(self, cr):
        cr.execute("""
        CREATE OR REPLACE FUNCTION fu_extenso_euro(num numeric(20,2)) returns text as $$
        DECLARE
           val_extenso text;
           resultado text;
        BEGIN
          val_extenso=fu_extenso($1,'euro','euros');
          resultado=upper(substring( val_extenso from 1 for 1)) || lower(substring( val_extenso from 2 ));
          return resultado;
        END;
        $$ LANGUAGE plpgsql
           IMMUTABLE
           RETURNS NULL ON NULL INPUT ;
        """)
        return True

    def sql_fu_extenso(self, cr):
        cr.execute("""
        CREATE or replace FUNCTION fu_extenso(num numeric(20,2) , moeda text , moedas text) returns text as $$
        declare
        w_int char(21) ;
        x integer ;
        v integer ;
        w_ret text ;
        w_ext text ;
        w_apoio text ;
        m_cen text[] := array['quatrilião','quatriliões','trilião','triliões','bilião','biliões','milhão','milhões',
        'mil','mil'] ;
        begin
          w_ret := '' ;
          w_int := to_char(num * 100 , 'fm000000000000000000 00') ;
          for x in 1..5 loop
              v := cast(substr(w_int,(x-1)*3 + 1,3) as integer) ;
              if v > 0 then
                 if v > 1 then
                    w_ext := m_cen[(x-1)*2+2] ;
                   else
                    w_ext := m_cen[(x-1)*2+1] ;
                 end if ;
                 w_ret := w_ret || fu_extenso_blk(substr(w_int,(x-1)*3 + 1,3)) || ' ' || w_ext ||' ' ;
              end if ;
          end loop ;
          v := cast(substr(w_int,16,3) as integer) ;
          if v > 0 then
             if v > 1 then
                w_ext := moedas ;
               else
                if w_ret = '' then
                   w_ext := moeda ;
                  else
                   w_ext := moedas ;
                end if ;
             end if ;
             w_apoio := fu_extenso_blk(substr(w_int,16,3)) || ' ' || w_ext ;
             if w_ret = '' then
                w_ret := w_apoio ;
               else
                if v > 100 then
                   if w_ret = '' then
                      w_ret := w_apoio ;
                     else
                      w_ret := w_ret || w_apoio ;
                   end if ;
                  else
                   w_ret := btrim(w_ret,', ') || ' e ' || w_apoio ;
                end if ;
             end if ;
            else
             if w_ret <> '' then
                if substr(w_int,13,6) = '000000' then
                   w_ret := btrim(w_ret,', ') || ' de ' || moedas ;
                  else
                   w_ret := btrim(w_ret,', ') || ' ' || moedas ;
                end if ;
             end if ;
          end if ;
          v := cast(substr(w_int,20,2) as integer) ;
          if v > 0 then
             if v > 1 then
                w_ext := 'cêntimos' ;
               else
                w_ext := 'cêntimo' ;
             end if ;
             w_apoio := fu_extenso_blk('0'||substr(w_int,20,2)) || ' ' || w_ext ;
             if w_ret = '' then
                w_ret := w_apoio  || ' de ' || moeda;
               else
                w_ret := w_ret || ' e ' || w_apoio ;
             end if ;
          end if ;
          return w_ret ;
        end ;
        $$ LANGUAGE plpgsql
           IMMUTABLE
           RETURNS NULL ON NULL INPUT ;
        """)
        return True

    def sql_fu_extenso_blk(self, cr):
        cr.execute("""
        CREATE or replace FUNCTION fu_extenso_blk(num char(3)) returns text as $$
        declare
        w_cen integer ;
        w_dez integer ;
        w_dez2 integer ;
        w_uni integer ;
        w_tcen text ;
        w_tdez text ;
        w_tuni text ;
        w_ext text ;
        m_cen text[] := array['','cento','duzentos','trezentos','quatrocentos','quinhentos','seiscentos','setecentos',
        'oitocentos','novecentos'];
        m_dez text[] := array['','dez','vinte','trinta','quarenta','cinquenta','sessenta','setenta','oitenta',
        'noventa'] ;
        m_uni text[] := array['','um','dois','três','quatro','cinco','seis','sete','oito','nove','dez','onze','doze',
        'treze','catorze','quinze','dezasseis','dezassete','dezoito','dezanove'] ;
        begin
          w_cen := cast(substr(num,1,1) as integer) ;
          w_dez := cast(substr(num,2,1) as integer) ;
          w_dez2 := cast(substr(num,2,2) as integer) ;
          w_uni := cast(substr(num,3,1) as integer) ;
          if w_cen = 1 and w_dez2 = 0 then
             w_tcen := 'Cem' ;
             w_tdez := '' ;
             w_tuni := '' ;
            else
             if w_dez2 < 20 then
                w_tcen := m_cen[w_cen + 1] ;
                w_tdez := m_uni[w_dez2 + 1] ;
                w_tuni := '' ;
               else
                w_tcen := m_cen[w_cen + 1] ;
                w_tdez := m_dez[w_dez + 1] ;
                w_tuni := m_uni[w_uni + 1] ;
             end if ;
          end if ;
          w_ext := w_tcen ;
          if w_tdez <> '' then
             if w_ext = '' then
                w_ext := w_tdez ;
               else
                w_ext := w_ext || ' e ' || w_tdez ;
             end if ;
          end if ;
          if w_tuni <> '' then
             if w_ext = '' then
                w_ext := w_tuni ;
               else
                w_ext := w_ext || ' e ' || w_tuni ;
             end if ;
          end if ;
          return w_ext ;
        end ;
        $$ LANGUAGE plpgsql
           IMMUTABLE
           RETURNS NULL ON NULL INPUT ;
        """)
        return True

    def teste_existencia_movim_fundos_maneio(self, cr):
        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'fu_extenso_euro'""")
        result = cr.fetchone()
        if result is None:
            self.sql_fu_extenso_euro(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'fu_extenso'""")
        result = cr.fetchone()
        if result is None:
            self.sql_fu_extenso(cr)

        cr.execute("""SELECT proname FROM pg_catalog.pg_proc  WHERE proname = 'fu_extenso_blk'""")
        result = cr.fetchone()
        if result is None:
            self.sql_fu_extenso_blk(cr)

        return True

    def create(self, cr, uid, vals, context=None):
        self.teste_existencia_movim_fundos_maneio(cr)
        return super(sncp_tesouraria_movim_fundos_maneio, self).create(cr, uid, vals, context=context)

    _order = 'name,empregado_id,data_mov'

    _defaults = {
        'estado': 0,
        'data_mov': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day,
                            datetime.now().hour, datetime.now().minute, datetime.now().second))}

sncp_tesouraria_movim_fundos_maneio()
# ___________________________________RELAÇÃO DE MOVIMENTOS COM ORDENS DE PAGAMENTO_________________________


class sncp_tesouraria_movim_fm_rel(osv.Model):
    _name = 'sncp.tesouraria.movim.fm.rel'
    _description = u"Relação entre Mov. Fundos de Maneio e Ordens de Pagamento"

    _columns = {
        'movim_fm_id': fields.many2one('sncp.tesouraria.movim.fundos.maneio'),
        'ordem_pag_id': fields.many2one('sncp.despesa.pagamentos.ordem')
    }

sncp_tesouraria_movim_fm_rel()