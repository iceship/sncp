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
from openerp.osv import fields, osv
from openerp.tools.translate import _


class formulario_sncp_tesouraria_pagamentos_reposicoes_diario(osv.Model):
    _name = 'formulario.sncp.tesouraria.pagamentos.reposicoes.diario'
    _description = u"Formulário de Reposições"

    send = {}

    def on_change_meio(self, cr, uid, ids, meio_pag_id):
        if meio_pag_id is not False:
            db_sncp_comum_meios_pagamento = self.pool.get('sncp.comum.meios.pagamento')
            obj = db_sncp_comum_meios_pagamento.browse(cr, uid, meio_pag_id)
            if len(ids) != 0:
                self.write(cr, uid, ids, {'ref_meio': obj.meio})
            return {'value': {'ref_meio': obj.meio}}
        return {'value': {'ref_meio': None}}

    def on_change_codigo(self, cr, uid, ids, passed_id, descr):
        obj = None
        if descr in ['caixa', 'cx']:
            db_sncp_tesouraria_caixas = self.pool.get('sncp.tesouraria.caixas')
            obj = db_sncp_tesouraria_caixas.browse(cr, uid, passed_id)
        elif descr in ['banco', 'bk']:
            db_sncp_tesouraria_contas_bancarias = self.pool.get('sncp.tesouraria.contas.bancarias')
            obj = db_sncp_tesouraria_contas_bancarias.browse(cr, uid, passed_id)
        elif descr in ['fundo', 'fm']:
            db_sncp_tesouraria_fundos_maneio = self.pool.get('sncp.tesouraria.fundos.maneio')
            obj = db_sncp_tesouraria_fundos_maneio.browse(cr, uid, passed_id)

        if len(ids) != 0:
            self.write(cr, uid, ids, {'bcfm': obj.codigo})
        return {}

    def wizard(self, cr, uid, ids):
        self.send['repo_id'] = ids[0]

        return {
            'name': u'<div style="width:500px;">Parâmetros de diário das reposições</div>',
            'id': 'repoabate',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'formulario.sncp.tesouraria.pagamentos.reposicoes.diario',
            'nodestroy': True,
            'target': 'new', }

    def end(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        self.send['meio_pag_id'] = obj.meio_pag_id.id
        self.send['meio_desc'] = obj.meio_desc
        self.send['ref_meio'] = obj.ref_meio
        self.send['bcfm'] = obj.bcfm
        self.send['banco_id'] = obj.banco_id.id
        self.send['caixa_id'] = obj.caixa_id.id
        self.send['fundo_id'] = obj.fundo_id.id
        self.send['name'] = obj.name
        self.send['diario_cob_id'] = obj.diario_cob_id.id
        self.send['data'] = obj.data
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return self.pool.get('sncp.despesa.pagamentos.reposicoes').cobrar(cr, uid, ids, self.send)

    def descartar(self, cr, uid, ids, context):
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return True

    _columns = {

        'meio_pag_id': fields.many2one('sncp.comum.meios.pagamento', u'Meio de Pagamento',
                                       domain=[('tipo', 'in', ['rec']), ('meio', 'not in', ['fm', 'dc'])],),
        'meio_desc': fields.related('meio_pag_id', 'name', type="char", string=u"Meio de Pagamento", store=True),
        'ref_meio': fields.char(u'Meio'),
        'bcfm': fields.char(u'Código'),

        'banco_id': fields.many2one('sncp.tesouraria.contas.bancarias', u'Banco',
                                    domain=[('tipo', 'in', ['ord']), ('state', 'in', ['act'])]),
        'caixa_id': fields.many2one('sncp.tesouraria.caixas', u'Caixa'),
        'fundo_id': fields.many2one('sncp.tesouraria.fundos.maneio', u'Fundo de Maneio',
                                    domain=[('ativo', '=', True)]),
        'name': fields.char(u'N.º Cheque/Outro', size=15),
        'diario_cob_id': fields.many2one('account.journal', u'Diário de cobrança da reposição'),
        'data': fields.datetime(u'Data e hora'),
    }

    _defaults = {
        'data': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour,
                        datetime.now().minute, datetime.now().second)),
    }

    def _check_ano(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        data = datetime.strptime(obj.data, "%Y-%m-%d %H:%M:%S")
        if data.year != datetime.now().year:
            raise osv.except_osv(_(u'Aviso'), _(u'A data têm que ser do ano corrente.'))
        else:
            return True

    def _diario_restrict(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.diario_cob_id.default_debit_account_id.id is False:
                raise osv.except_osv(_(u'Aviso'),
                                     _(u'Defina a conta a débito e/ou a crédito do diário '+\
                                       unicode(obj.diario_cob_id.name)+u'.'))
        else:
            return True

    _constraints = [
        (_check_ano, u'', ['data']),
        (_diario_restrict, u'', ['diario_cob_id'])]

formulario_sncp_tesouraria_pagamentos_reposicoes_diario()