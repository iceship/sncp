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
from datetime import datetime, date
from openerp.tools.translate import _


class formulario_sncp_despesa_compromisso_diario(osv.Model):
    _name = 'formulario.sncp.despesa.compromisso.diario'
    _description = u"Formulário do compromisso"

    def wizard(self, cr, uid, ids, context, vals):
        compromisso_id = ids[0]
        nids = self.search(cr, uid, [('compromisso_id', '=', compromisso_id)])
        if len(nids) == 0:
            nids.append(self.create(cr, uid, {'tipo': vals['tipo'], 'compromisso_id': compromisso_id}))
        if datetime.now().year == vals['ano_fim']:
            self.write(cr, uid, nids, {'res': 1})
        elif datetime.now().year in range(vals['ano_ini']+1, vals['ano_fim']):
            self.write(cr, uid, nids, {'res': 2})
        elif datetime.now().year < vals['ano_ini']:
            self.write(cr, uid, nids, {'res': 3})
        return {
            'name': u'<div style="width:500px;">Parâmetros de diário do compromisso</div>',
            'id': 'rrr',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'formulario.sncp.despesa.compromisso.diario',
            'res_id': nids[0],
            'nodestroy': True,
            'target': 'new',
            'context': context, }

    def descartar(self, cr, uid, ids, context):
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return True

    def end(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        vals = {'ref': obj.name,
                'datahora': obj.datahora,
                'dia_mes_pag': obj.dia_mes_pag,
                'diario_id': obj.diario_id.id,
                'diario_fut_id': obj.diario_fut_id.id}
        return self.pool.get('sncp.despesa.compromisso').compromisso_proc(cr, uid, [obj.compromisso_id.id], context,
                                                                          vals)

    _columns = {
        'name': fields.char(u'Referência'),
        'datahora': fields.datetime(u'Data e hora'),
        'tipo': fields.char(u'tipo'),
        'dia_mes_pag': fields.integer(u'Dia para pagamento'),
        'res': fields.integer(u'res'),
        'diario_id': fields.many2one('account.journal', u'Diário de lançamento'),
        'diario_fut_id': fields.many2one('account.journal', u'Diário de lançamento para os anos seguintes'),
        'compromisso_id': fields.many2one('sncp.despesa.compromisso', u'Compromisso'),
    }

    def get_journal_id(self, cr, journal):
        cr.execute("""SELECT id FROM account_journal WHERE code = '%s'""" % journal)
        return cr.fetchone()

    _defaults = {
        'dia_mes_pag': 1,
        'datahora': unicode(datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour,
                            datetime.now().minute, datetime.now().second)),
        'diario_id': lambda self, cr, uid, ids: self.get_journal_id(cr, "COM"),
        'diario_fut_id': lambda self, cr, uid, ids: self.get_journal_id(cr, "COF"),
    }

    def _dia_limitado_mes(self, cr, uid, ids, context=None):
        datacorrente = date.today()
        record = self.browse(cr, uid, ids[0])
        mes = {1: u'Janeiro', 2: u'Fevereiro', 3: u'Março', 4: u'Abril',
               5: u'Maio', 6: u'Junho', 7: u'Julho', 8: u'Agosto',
               9: u'Setembro', 10: u'Outubro', 11: u'Novembro', 12: u'Dezembro'}
        if datacorrente.month in [1, 3, 5, 7, 8, 10, 12]:
            if record.dia_mes_pag in range(1, 32):
                return True
            else:
                raise osv.except_osv(_(u'Aviso'), _(u'O mês'+mes[datacorrente.month]+u' vai do dia 1 ao 31.'))

        elif datacorrente.month in [4, 6, 9, 11]:
            if record.dia_mes_pag in range(1, 31):
                return True
            else:
                raise osv.except_osv(_(u'Aviso'),
                                     _(u'O mês '+mes[datacorrente.month] + u' vai do dia 1 ao 30.'))
        else:
            if datacorrente.year % 4 == 0:
                if record.dia_mes_pag in range(1, 30):
                    return True
                else:
                    raise osv.except_osv(_(u'Aviso'), _(u'O mês '+mes[datacorrente.month]+u' vai do dia 1 ao 29.'))
            else:
                if record.dia_mes_pag in range(1, 29):
                    return True
                else:
                    raise osv.except_osv(_(u'Aviso'), _(u'O mês '+mes[datacorrente.month]+u' vai do dia 1 ao 28.'))

    def _check_ano(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        data = datetime.strptime(obj.datahora, "%Y-%m-%d %H:%M:%S")
        if data.year != datetime.now().year:
            raise osv.except_osv(_(u'Aviso'), _(u'A data têm que ser do ano corrente.'))
        else:
            return True

    def _diario_restrict(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.diario_id.id is not False:
            if obj.diario_id.default_credit_account_id.id is False and \
               obj.diario_id.default_debit_account_id.id is False:
                raise osv.except_osv(_(u'Aviso'),
                                     _(u'Defina a conta a débito e/ou a crédito do diário '
                                       + unicode(obj.diario_id.name)+u'.'))
            else:
                return True

    _constraints = [
        (_dia_limitado_mes, u'', ['dia_mes_pag']),
        (_check_ano, u'', ['datahora']),
        (_diario_restrict, u'', ['diario_id', 'diario_fut_id'])]

formulario_sncp_despesa_compromisso_diario()
