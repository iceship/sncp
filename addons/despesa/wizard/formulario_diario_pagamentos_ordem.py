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


class formulario_sncp_despesa_pagamentos_ordem_diario(osv.Model):
    _name = 'formulario.sncp.despesa.pagamentos.ordem.diario'
    _description = u"Formulário da Ordem de Pagamento"

    send = {}

    def wizard(self, cr, uid, ids):
        db_sncp_comum_param = self.pool.get('sncp.comum.param')
        param_ids = db_sncp_comum_param.search(cr, uid, [('state', '=', 'draft')])
        if len(param_ids) == 0:
            raise osv.except_osv(_(u'Aviso'), _(u'A operação não pode ser concluída.\n'
                                                u'Preencha os parâmetros por defeito no menu:\n'
                                                u'Comum/Parâmetros.'))
        self.send['opag_id'] = ids

        parametros = db_sncp_comum_param.browse(cr, uid, param_ids[0])
        db_sncp_despesa_descontos_retencoes_rel_grec = self.pool.get('sncp.despesa.descontos.retencoes.rel.grec')
        retencoes_rel_grec_id = db_sncp_despesa_descontos_retencoes_rel_grec.search(cr, uid, [('opag_id', '=', ids[0])])

        if parametros.diario_liq_id.id is False:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'Considere definir o diário de liquidação '
                                   u'da ordem de pagamento em Comum/Parâmetros.'))

        if len(retencoes_rel_grec_id) == 0:
            form_id = self.create(cr, uid, {'estado': 0, 'opag_id': ids[0],
                                            'diario_liq': parametros.diario_liq_id.id})
        else:
            form_id = self.create(cr, uid, {'estado': 1, 'opag_id': ids[0],
                                            'diario_liq': parametros.diario_liq_id.id})
        return {
            'name': u'<div style="width:500px;">Parâmetros de Pagamento</div>',
            'id': 'pdop',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'formulario.sncp.despesa.pagamentos.ordem.diario',
            'res_id': form_id,
            'nodestroy': True,
            'target': 'new', }

    def end(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids[0])

        self.send['datatransacao'] = record.name
        self.send['diario_liq'] = record.diario_liq.id
        self.send['diario_pag'] = record.diario_pag.id

        if record.estado == 0:
            self.send['estado'] = record.estado
        else:
            self.send['diario_liq_guia_rec'] = record.diario_liq_guia_rec.id
            self.send['departamento_id'] = record.departamento_id.id
            self.send['diario_pag_guia_rec'] = record.diario_pag_guia_rec.id
            self.send['estado'] = record.estado

        self.unlink(cr, uid, ids, context=context)
        return self.pool.get('sncp.despesa.pagamentos.ordem').pag_ord_liq(cr, uid, ids, self.send)

    def descartar(self, cr, uid, ids, context):
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return True

    _columns = {
        'opag_id': fields.many2one('sncp.despesa.pagamentos.ordem', u''),
        'name': fields.datetime(u'Data da Transação'),
        'diario_liq': fields.many2one('account.journal', u'Diário de liquidação'),
        'diario_pag': fields.many2one('account.journal', u'Diário de pagamento'),
        'diario_liq_guia_rec': fields.many2one('account.journal', u'OT - Diário de liquidação da Guia de Receita'),
        'departamento_id': fields.many2one('hr.department', u'Departamento'),
        'diario_pag_guia_rec': fields.many2one('account.journal', u'OT - Diário de pagamento da Guia de Receita'),
        'estado': fields.integer(u'estado'),
        # 0 - nao aparecem nem guia de recebimento nem ordem de pagamento nem departamento
        # 1 - guia de recebimento e departamento
        # 2 - guia de recebimento e ordem de pagamento e departamento
    }

    def get_journal_id(self, cr, journal):
        cr.execute("""SELECT id FROM account_journal WHERE code = '%s'""" % journal)
        return cr.fetchone()

    _defaults = {
        'name': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour,
                        datetime.now().minute, datetime.now().second)),
        'diario_pag': lambda self, cr, uid, ids: self.get_journal_id(cr, "PAG"),
        'diario_liq_guia_rec': lambda self, cr, uid, ids: self.get_journal_id(cr, "GRC"),
        'diario_pag_guia_rec': lambda self, cr, uid, ids: self.get_journal_id(cr, "OTS"),
    }

    def _check_ano(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        data = datetime.strptime(obj.name, "%Y-%m-%d %H:%M:%S")
        if data.year != datetime.now().year:
            raise osv.except_osv(_(u'Aviso'), _(u'A data têm que ser do ano corrente.'))
        else:
            return True

    def _diario_restrict(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.diario_liq.id is not False:
            if obj.diario_liq.default_credit_account_id.id is False:
                raise osv.except_osv(_(u'Aviso'),
                                     _(u'Defina a conta a crédito e/ou a débito do diário '
                                       + unicode(obj.diario_id.name)+u'.'))

        if obj.diario_liq_guia_rec.id is not False:
            if obj.diario_liq_guia_rec.default_debit_account_id.id is False:
                raise osv.except_osv(_(u'Aviso'), _(u'Defina a conta a débito e/ou a crédito do diário '
                                                    + unicode(obj.diario_id.name)+u'.'))
        return True

    _constraints = [
        (_check_ano, u'', ['name']),
        (_diario_restrict, u'', ['diario_liq', 'diario_liq_guia_rec'])
    ]

formulario_sncp_despesa_pagamentos_ordem_diario()