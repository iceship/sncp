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

from openerp.osv import fields, osv
from openerp.tools.translate import _


class sncp_receita_print_report(osv.TransientModel):
    _name = 'sncp.receita.print.report'
    _inherit = 'sncp.receita.print.report'
    """
    Procedimento para imprimir avisos:
    Carregar o relatório para a base de dados:
        >> Configurações >> Técnico >> Jasper Reports 7.0 >> Jasper Reports 7.0
    Definir o relatório como enviado para a mpressora
        >> Configurações >> Printing >> Reports
        Separador "Print"
            Action "Send to Printer"
            Printer "Escolhe a impressora preferida", se não existe nenhuma lançe o wizard:
             >> Configurações >> Printing >> Update Printers from CUPS
   """

    def imprimir_na_impressora(self, cr, uid, print_ids, obj_report, context):
        return super(sncp_receita_print_report, self).imprimir_na_impressora(cr, uid, print_ids, obj_report, context)

    def imprime_notificacao_regproc(self, cr, uid, vals, context=None):
        nao_enviado = ''
        db_sncp_comum_param = self.pool.get('sncp.comum.param')
        try:
            param_ids = db_sncp_comum_param.search(cr, uid, [('state', '=', 'draft')])
            if len(param_ids) == 0:
                raise osv.except_osv(_(u'Aviso'), _(u'A operação não pode ser concluida.\n'
                                                    u'Preencha os parâmetros por defeito no menu:\n'
                                                    u'Comum/Parâmetros.'))
            obj_param = db_sncp_comum_param.browse(cr, uid, param_ids[0])
            if obj_param.crr_notifica:

                # Extração de endereço
                nome = vals['partner'].name or ''
                rua = vals['partner'].street or ''
                rua2 = vals['partner'].street2 or ''
                cod = vals['partner'].zip or ''
                cidade = vals['partner'].city or ''
                pais = vals['partner'].country_id.name or ''
                ender = unicode(nome + '\n' + rua + ' ' + rua2 + '\n' + cod + ' ' + cidade + ' ' + pais)

                # Definição de impressora
                db_actions_report_xml = self.pool.get('ir.actions.report.xml')
                report_ids = db_actions_report_xml.search(cr, uid, [('model', '=', 'sncp.receita.print.report')])
                db_actions_report_xml.write(cr, uid, report_ids, {'printing_printer_id': obj_param.crr_printer_id.id})
                obj_report = db_actions_report_xml.browse(cr, uid, report_ids[0])

                # Preparação/impressão de relatório
                body = unicode(vals['assunto'] + '\n\n\n\n' + vals['body'])
                print_ids = []
                cr.execute(""" DELETE FROM sncp_receita_print_report""")
                print_ids.append(self.create(cr, uid, {'ender': ender, 'corpo': body}))
                self.imprimir_na_impressora(cr, uid, print_ids, obj_report, context)

        except (RuntimeError, TypeError, NameError):
            nao_enviado = vals['assunto']
        return nao_enviado

    _columns = {
        'ender': fields.text(u'Endereço 1'),
        'corpo': fields.text(u''),
    }

sncp_receita_print_report()