# -*- encoding: utf-8 -*-
# #############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2012 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime
from openerp.osv import fields, osv


class formulario_sncp_orcamento_diario(osv.Model):
    _name = 'formulario.sncp.orcamento.diario'
    _description = u"Formulário do Orçamento"

    send = {}

    def wizard(self, cr, uid, ids, context=None):
        self.send['orcamento_id'] = ids
        """Method is used to show form view in new windows"""
        return {
            'name': '<div style="width:500px;">Parâmetros de contabilização do orçamento</div>',
            'id': 'umnomeqq',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'formulario.sncp.orcamento.diario',
            'nodestroy': True,
            'target': 'new',
        }

    def end(self, cr, uid, ids, context=None, ):
        rec = self.browse(cr, uid, ids[0])
        self.send['ref'] = rec.name
        self.send['data'] = rec.data
        self.send['diario_id'] = rec.diario_id.id
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return self.pool.get('sncp.orcamento').orcamento_accounted(cr, uid, ids, self.send)

    def descartar(self, cr, uid, ids, context):
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return True

    _columns = {
        'name': fields.char(u'Referência', ),
        'data': fields.date(u'Data'),
        'diario_id': fields.many2one('account.journal', u'Diário de lançamento')
    }

    def get_journal_id(self, cr, journal):
        cr.execute(
            """SELECT id FROM account_journal WHERE code = '%s'""" % journal)
        return cr.fetchone()

    _defaults = {
        'data': unicode(datetime.now().date()),
        'diario_id': lambda self, cr, uid, ids: self.get_journal_id(cr, "ORC"),
    }

formulario_sncp_orcamento_diario()