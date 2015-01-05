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

from openerp.osv import fields, osv

# _________________________________________________FATURAS APROVADAS__________________________________


class sncp_despesa_faturas_aprovadas(osv.Model):
    _name = 'sncp.despesa.faturas.aprovadas'
    _description = u"Faturas aprovadas"

    _columns = {
        'invoice_id': fields.many2one('account.invoice', u'Fatura de compras'),
        'partner_id': fields.related('invoice_id', 'partner_id', 'name',
                                     store=True, type="char", string=u"Parceiro de Negocio"),
        'supplier_invoice_number': fields.related('invoice_id', 'supplier_invoice_number',
                                                  store=True, type="char", string=u"Número da fatura"),
        'date_invoice': fields.related('invoice_id', 'date_invoice',
                                       store=True, type="char", string=u'Data da Fatura'),
        'date_due': fields.related('invoice_id', 'date_due',
                                   store=True, type="char", string=u'Data de vencimento'),
        'amount_total': fields.related('invoice_id', 'amount_total',
                                       store=True, type="char", string=u'Total da Fatura'),

        'user_id': fields.many2one('res.users', u'Aprovador'),
        'datahora': fields.datetime(u'Data de Aprovação'),
        'name': fields.char(u'Referência'),  # invoice_id.origin
        # composto pelo NIF e PN -- res.partner.vat
    }

sncp_despesa_faturas_aprovadas()