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


class formulario_ordem_compra_select_compromisso(osv.Model):
    _name = 'formulario.ordem.compra.select.compromisso'
    _description = u"Formulário da Ordem de Compra"

    def lista_compromissos(self, cr, uid, context):
        cr.execute("""SELECT id, compromisso FROM sncp_despesa_compromisso
                      WHERE state='proc' AND id NOT IN(
                        SELECT name FROM sncp_despesa_compromisso_relacoes)""")
        # Confirmar se existe limitação por estado
        result = cr.fetchall()
        resultado = []
        if len(result) == 0:
            resultado.append((u'0', u'Não existe nenhum compromisso para vincular a ordem.'))
        else:
            for res in result:
                resultado.append((unicode(res[0]), unicode(res[1])))

        resultado = list(set(resultado))
        return resultado

    def wizard(self, cr, uid, ids, context=None):
        ordem_compra_id = ids[0]
        ids = self.search(cr, uid, [('ordem_compra_id', '=', ordem_compra_id)])
        if len(ids) == 0:
            ids.append(self.create(cr, uid, {
                'ordem_compra_id': ordem_compra_id,
            }))
        return {'name': '<div style="width:500px;">Seleciona Compromisso pretendido</div>',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'formulario.ordem.compra.select.compromisso',
                'nodestroy': True,
                'target': 'new',
                'res_id': ids[0], }

    def continuar(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        lista = [obj.ordem_compra_id.id]
        compromisso_ref = int(obj.compromisso_ref)
        return self.pool.get('purchase.order').verificar_comportamento(cr, uid, lista,
                                                                       compromisso_ref)

    def descartar(self, cr, uid, ids, context):
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return True

    _columns = {'ordem_compra_id': fields.many2one('purchase.order'),
                'compromisso_ref': fields.selection(lista_compromissos, u'Compromisso'), }

formulario_ordem_compra_select_compromisso()