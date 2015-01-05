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
from datetime import datetime, date
from openerp.osv import fields, osv


class teste_cond_pagam(osv.Model):
    _name = 'teste.cond.pagam'
    _description = u"Teste Condições de Pagamento"

    def da_data_vencimento(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids[0])
        dataemissao = datetime.strptime(record.dataemissao, "%Y-%m-%d")
        dataemissao = date(dataemissao.year, dataemissao.month, dataemissao.day)
        db_sncp_receita_cond_pagam = self.pool.get('sncp.comum.cond.pagam')

        vals = {
            'dataemissao': dataemissao,
            'cond_pagam_id': record.name.id,
        }
        datavencimento = db_sncp_receita_cond_pagam.da_data_vencimento(cr, uid, [], vals)
        self.write(cr, uid, ids, {'datavencimento': unicode(datavencimento)})
        return True

    _columns = {
        'name': fields.many2one('sncp.comum.cond.pagam', u'Código'),
        'dataemissao': fields.date(u'Data de emissão'),
        'datavencimento': fields.date(u'Data de vencimento'),
        'codigo': fields.related('name', u'Código', store=True)
    }

teste_cond_pagam()


class teste_juros(osv.Model):
    _name = 'teste.juros'
    _description = u"Teste Juros"

    def da_valor_juros(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids[0])
        datavencimento = datetime.strptime(record.datavencimento, "%Y-%m-%d")
        datavencimento = date(datavencimento.year, datavencimento.month, datavencimento.day)

        datapagamento = datetime.strptime(record.datapagamento, "%Y-%m-%d")
        datapagamento = date(datapagamento.year, datapagamento.month, datapagamento.day)

        db_sncp_receita_juros = self.pool.get('sncp.receita.juros')

        vals = {
            'datavencimento': datavencimento,
            'datapagamento': datapagamento,
            'valorbase': record.valorbase,
            'metodo_id': record.name.id,
        }
        montantejurosapagar = db_sncp_receita_juros.da_valor_juros(cr, uid, [], vals)
        self.write(cr, uid, ids, {'montantedejurosapagar': montantejurosapagar})
        return True

    _columns = {
        'name': fields.many2one('sncp.receita.juros', u'Código'),
        'valorbase': fields.float(u'Valor base', digits=(12, 2)),
        'datavencimento': fields.date(u'Data de Vencimento'),
        'datapagamento': fields.date(u'Data de Pagamento'),
        'montantedejurosapagar': fields.float(u'Montante de juros a pagar', digits=(12, 2)),
    }

teste_juros()