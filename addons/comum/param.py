# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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


# ______________________________________________________PARAMETROS______________________________________
class sncp_comum_param(osv.Model):
    _name = 'sncp.comum.param'
    _description = u"Parâmetros"

    _columns = {
        'datahora': fields.datetime(u'Em vigor até'),
        'name': fields.char(u'Descrição', size=50),
        'emp_info_cab': fields.many2one('hr.employee', u'Informação de Cabimento'),
        'emp_info_com': fields.many2one('hr.employee', u'Informação de Compromisso'),
        'emp_tesoureiro': fields.many2one('hr.employee', u'Tesoureira/o'),
        'otes_mpag': fields.many2one('sncp.comum.meios.pagamento', u'Meio de recebimento padrão',
                                     domain=[('meio', 'not in', ['dc']), ('tipo', 'in', ['rec'])]),
        'desp_mpag': fields.many2one('sncp.comum.meios.pagamento', u'Meio de pagamento padrão',
                                     domain=[('meio', 'not in', ['dc']), ('tipo', 'in', ['pag'])]),
        'diario_fat_juros': fields.many2one('account.journal', u'Faturas de Juros',
                                            domain=[('type', '=', 'sale')]),
        'ri_sequence_id': fields.many2one('ir.sequence', u'Sequência para Requisições Internas'),
        'ri_diario_id': fields.many2one('account.journal', u'Stocks para Requisições Internas'),
        'an_sequence_id': fields.many2one('ir.sequence', u'Sequência para Actos Notariais'),
        'aquis_sequence_id': fields.many2one('ir.sequence', u'Sequência para Aquisições'),
        'alien_sequence_id': fields.many2one('ir.sequence', u'Sequência para Alienações'),
        'state': fields.selection([('draft', u'Atual'),
                                   ('fechado', u'Fechado')]),
        'diario_liq_id': fields.many2one('account.journal', u'Liquidação'),
        'diario_liq_rec_id': fields.many2one('account.journal', u'Liquidação da Receita'),
        'diario_cob_rec_id': fields.many2one('account.journal', u'Cobrança da Receita'),
        'crr_printer_id': fields.many2one('printing.printer', u'Impressora para os avisos',
                                          domain=[('status', '=', 'available')]),
        'crr_notifica': fields.boolean(u'Imprimir carta de aviso se Parceiro não tiver endereço de correio eletrónico'),
    }

    def write(self, cr, uid, ids, new_vals, context=None):
        obj = self.browse(cr, uid, ids[0])
        old_vals = {
            'datahora': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day,
                                         datetime.now().hour, datetime.now().minute, datetime.now().second)),
            'name': obj.name,
            'emp_info_cab': obj.emp_info_cab.id,
            'emp_info_com': obj.emp_info_com.id,
            'emp_tesoureiro': obj.emp_tesoureiro.id,
            'otes_mpag': obj.otes_mpag.id,
            'desp_mpag': obj.desp_mpag.id,
            'diario_fat_juros': obj.diario_fat_juros.id,
            'ri_sequence_id': obj.ri_sequence_id.id,
            'an_sequence_id': obj.an_sequence_id.id,
            'aquis_sequence_id': obj.aquis_sequence_id.id,
            'alien_sequence_id': obj.alien_sequence_id.id,
            'ri_diario_id': obj.ri_diario_id.id,
            'diario_liq_id': obj.diario_liq_id.id,
            'diario_liq_rec_id': obj.diario_liq_rec_id.id,
            'diario_cob_rec_id': obj.diario_cob_rec_id.id,
            'crr_printer_id': obj.crr_printer_id.id,
            'crr_notifica': obj.crr_notifica,
            'state': 'fechado',
        }

        if 'name' not in new_vals:
            new_vals['name'] = old_vals['name']

        if 'emp_info_cab' not in new_vals:
            new_vals['emp_info_cab'] = old_vals['emp_info_cab']

        if 'emp_info_com' not in new_vals:
            new_vals['emp_info_com'] = old_vals['emp_info_com']

        if 'emp_tesoureiro' not in new_vals:
            new_vals['emp_tesoureiro'] = old_vals['emp_tesoureiro']

        if 'otes_mpag' not in new_vals:
            new_vals['otes_mpag'] = old_vals['otes_mpag']

        if 'desp_mpag' not in new_vals:
            new_vals['desp_mpag'] = old_vals['desp_mpag']

        if 'diario_fat_juros' not in new_vals:
            new_vals['diario_fat_juros'] = old_vals['diario_fat_juros']

        if 'ri_sequence_id'not in new_vals:
            new_vals['ri_sequence_id'] = old_vals['ri_sequence_id']

        if 'an_sequence_id' not in new_vals:
            new_vals['an_sequence_id'] = old_vals['an_sequence_id']

        if 'aquis_sequence_id' not in new_vals:
            new_vals['aquis_sequence_id'] = old_vals['aquis_sequence_id']

        if 'alien_sequence_id' not in new_vals:
            new_vals['alien_sequence_id'] = old_vals['alien_sequence_id']

        if 'ri_diario_id' not in new_vals:
            new_vals['ri_diario_id'] = old_vals['ri_diario_id']

        if 'diario_liq_id' not in new_vals:
            new_vals['diario_liq_id'] = old_vals['diario_liq_id']

        if 'diario_liq_rec_id' not in new_vals:
            new_vals['diario_liq_rec_id'] = old_vals['diario_liq_rec_id']

        if 'diario_cob_rec_id' not in new_vals:
            new_vals['diario_cob_rec_id'] = old_vals['diario_cob_rec_id']

        if 'crr_printer_id' not in new_vals:
            new_vals['crr_printer_id'] = old_vals['crr_printer_id']

        if 'crr_notifica' not in new_vals:
            new_vals['crr_notifica'] = old_vals['crr_notifica']

        new_vals['state'] = 'draft'
        self.create(cr, uid, new_vals)
        return super(sncp_comum_param, self).write(cr, uid, ids, old_vals)

    _order = 'state,datahora desc'

