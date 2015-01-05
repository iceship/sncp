# -*- encoding: utf-8 -*-
##############################################################################
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
from openerp.osv import fields, osv
from datetime import datetime
from openerp.tools.translate import _


class formulario_sncp_despesa_cabimento_diario(osv.Model):
    _name = 'formulario.sncp.despesa.cabimento.diario'
    _description = u"Formulário do cabimento"

    send = {}

    def wizard(self, cr, uid, ids, context):
        self.send['cabimento_id'] = ids[0]
        """Method is used to show form view in new windows"""
        return {
            'name': u'<div style="width:500px;">Parâmetros de contabilização do cabimento</div>',
            'id': 'doisnomeqq',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'formulario.sncp.despesa.cabimento.diario',
            'nodestroy': True,
            'context': context,
            'target': 'new', }

    def end(self, cr, uid, ids, context=None,):
        rec = self.browse(cr, uid, ids[0])
        self.send['ref'] = rec.name
        self.send['datahora'] = rec.datahora
        self.send['diario_id'] = rec.diario_id.id
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return self.pool.get('sncp.despesa.cabimento').cabimento_cont(cr, uid, [self.send['cabimento_id']], context,
                                                                      self.send)

    def descartar(self, cr, uid, ids, context):
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return True

    _columns = {
        'name': fields.char(u'Referência'),
        'datahora': fields.datetime(u'Data e hora'),
        'diario_id': fields.many2one('account.journal', u'Diário de lançamento')
    }

    def get_journal_id(self, cr):
        cr.execute("""SELECT id FROM account_journal WHERE code = 'CAB'""")
        return cr.fetchone()

    _defaults = {
        'datahora': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour,
                            datetime.now().minute, datetime.now().second)),
        'diario_id': lambda self, cr, uid, ids: self.get_journal_id(cr),
    }

    def _check_ano(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        data = datetime.strptime(obj.datahora, "%Y-%m-%d %H:%M:%S")
        if data.year != datetime.now().year:
            raise osv.except_osv(_(u'Aviso'), _(u'A data têm que ser do ano corrente.'))
        else:
            return True

    def _diario_restrict(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.diario_id.default_credit_account_id.id is False and \
           obj.diario_id.default_debit_account_id.id is False:
            raise osv.except_osv(_(u'Aviso'), _(u'Defina a conta a débito e/ou a crédito do diário '
                                                + unicode(obj.diario_id.name)+u'.'))
        else:
            return True

    _constraints = [
        (_check_ano, u'', ['datahora']),
        (_diario_restrict, u'', ['diario_id'])]

formulario_sncp_despesa_cabimento_diario()