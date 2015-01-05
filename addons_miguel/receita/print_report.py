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
import re
from openerp.osv import fields, osv
from openerp import netsvc
from openerp.tools.translate import _
from dateutil.relativedelta import *
from ..base_report_to_printer.report_service import virtual_report_spool

# __________________________________________       METODOS EXTERNOS      _______________________________________


def cria_aviso(self, cr, uid, lista_obj, body):
    for obj in lista_obj:
        modelo = obj._name
        model_id = self.pool.get('ir.model').search(cr, uid, [('model', '=', unicode(modelo))])
        dicti = obj._model.read(cr, uid, obj.id)
        value_report = ''
        # Etiquetas complexas
        re_name = re.compile('\[+([A-Z]){6}([0-9 \+\-])+\]')
        re_number = re.compile('[^A-Z\[]')
        result = re.finditer(re_name, body)
        for pos in result:
            # expr = result.string[pos[0]: pos[1]]
            expr = pos.string[pos.start(): pos.end()]
            string = re.search(re_number, expr)
            if string:
                numero = eval(expr[string.start(): len(expr)-1])
                etiqueta = expr[1:7]
                cr.execute("""SELECT path FROM sncp_comum_etiquetas
                              WHERE name = '%s' AND model_id = %d""" % (etiqueta, model_id[0]))
                tail = cr.fetchone()
                if tail:
                    path = 'obj.' + unicode(tail[0])
                    pos = tail[0].find('.')
                    if pos == -1:
                        chave = tail[0]
                    else:
                        chave = tail[0][:pos]
                    if chave in dicti:
                        value = eval(path)
                        if type(value) is int:
                            value_report = eval(unicode(value) + '+' + unicode(numero))
                        elif type(value) is str:
                            value_bd = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                            value_report = (value_bd + relativedelta(days=numero)).date()
                        body = body.replace(expr, unicode(value_report))

        # Etiquetas simples
        cr.execute("""SELECT name,path FROM sncp_comum_etiquetas WHERE model_id = %d OR model_id IS NULL """
                   % model_id[0])
        etiquetas = cr.fetchall()
        for label in etiquetas:
            path = 'obj.' + unicode(label[1])
            pos = label[1].find('.')
            if pos == -1:
                chave = label[1]
            else:
                chave = label[1][:pos]

            if chave in dicti:
                value = eval(path)
                if value:
                    body = body.replace(('[' + label[0] + ']'), unicode(value))

    return body


class sncp_receita_print_report(osv.TransientModel):
    _name = 'sncp.receita.print.report'
    _description = u"Imprimir Relatórios"
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

    def avisa(self, cr, uid, context=None):
        db_sncp_receita_controlo_config = self.pool.get('sncp.receita.controlo.config')
        db_sncp_receita_controlo = self.pool.get('sncp.receita.controlo')
        db_mail_mail = self.pool.get('mail.mail')
        lista_nao_enviados = []
        assunto = u''

        # Bloco de aviso ao Parceiro de negócio
        # Bloco de aviso ao Parceiro de negócio
        cr.execute("""SELECT RC.sector_id, RC.id, RCC.aviso_prev FROM sncp_receita_controlo AS RC
            LEFT JOIN sncp_receita_controlo_config AS RCC ON RCC.id = RC.sector_id
            WHERE RC.avisado is FALSE AND RC.fim <= CURRENT_DATE + RCC.aviso_prev""")
        dados_aviso = cr.fetchall()
        for aviso in dados_aviso:
            if aviso[2] > 0:
                try:
                    # ( 0 -- config_id, 1 -- controlo_id)
                    obj_config = db_sncp_receita_controlo_config.browse(cr, uid, aviso[0])
                    obj_controlo = db_sncp_receita_controlo.browse(cr, uid, aviso[1])
                    body = obj_config.aviso_texto

                    # Extrair/Manter Renovação
                    re_renov_ini = re.compile('\{+(RENOV_INI)\}')
                    re_renov_fim = re.compile('\{+(RENOV_FIM)\}')
                    if re.search(re_renov_ini, body) and re.search(re_renov_fim, body):
                        if obj_controlo.renovacoes < obj_config.renova_limite or obj_config.renova_limite == -1:
                            x = body[re.search(re_renov_ini, body).end(): re.search(re_renov_fim, body).start()]
                            y = body[re.search(re_renov_fim, body).end():]
                            body = body[:re.search(re_renov_ini, body).start()] + x + y
                        else:
                            z = body[re.search(re_renov_fim, body).end():]
                            body = body[:re.search(re_renov_ini, body).start()] + z

                    # Bloco de envio de e-mail
                    if obj_controlo.partner_id.email:

                        # Extrair assunto
                        re_ass_ini = re.compile('\{+(ASSUN_INI)\}')
                        re_ass_fim = re.compile('\{+(ASSUN_FIM)\}')
                        if re.search(re_ass_ini, body) and re.search(re_ass_fim, body):
                            assunto = body[re.search(re_ass_ini, body).end():re.search(re_ass_fim, body).start()]
                            assunto = cria_aviso(self, cr, uid, [obj_config, obj_controlo], assunto)
                            body = body[:re.search(re_ass_ini, body).start()]+body[re.search(re_ass_fim, body).end():]

                        # Extrair cabeçalho
                        re_ender_ini = re.compile('\{+(ENDER_INI)\}')
                        while re.search(re_ender_ini, body):
                            re_ender_fim = re.compile('\{+(ENDER_FIM)\}')
                            z = body[re.search(re_ender_fim, body).end():]
                            body = body[: re.search(re_ender_ini, body).start()] + z
                            re_ender_ini = re.compile('\{+(ENDER_INI)\}')

                        # Bloco de passagem para html
                        body = cria_aviso(self, cr, uid, [obj_config, obj_controlo], body)
                        body_html = '<html><body>' + body.replace('\n', '<br>') + '</body></html>'
                        datahora = unicode(datetime.now())
                        if datahora.find('.') != -1:
                            datahora = datahora[:datahora.find('.')]

                        values_email = {
                            'attachment_ids': [[6, False, []]],
                            'auto_delete': False,
                            'body_html': unicode(body_html),
                            'email_to': unicode(obj_controlo.partner_id.email),
                            'date': unicode(datahora),
                            'author_id': uid,
                            'type': 'email',
                            'email_from': u'openerp.notification@gmail.com',
                            'subject': unicode(assunto)}
                        mail_id = db_mail_mail.create(cr, uid, values_email)
                        db_mail_mail.send(cr, uid, [mail_id])
                        db_sncp_receita_controlo.write(cr, uid, [aviso[1]], {'avisado': True}, context)

                    # Bloco de envio da carta em papel
                    else:
                        db_sncp_comum_param = self.pool.get('sncp.comum.param')

                        param_ids = db_sncp_comum_param.search(cr, uid, [('state', '=', 'draft')])
                        if len(param_ids) == 0:
                            raise osv.except_osv(_(u'Aviso'),
                                                 _(u'A operação não pode ser concluída.\n'
                                                   u'Preencha os parâmetros por defeito no menu:\n'
                                                   u'Comum/Parâmetros.'))
                        obj_param = db_sncp_comum_param.browse(cr, uid, param_ids[0])
                        if obj_param.crr_notifica:
                            body = cria_aviso(self, cr, uid, [obj_config, obj_controlo], body)

                            # Extração de endereço
                            re_ender_ini = re.compile('\{+(ENDER_INI)\}')
                            re_ender_fim = re.compile('\{+(ENDER_FIM)\}')
                            z = body[re.search(re_ender_ini, body).end(): re.search(re_ender_fim, body).start()]
                            ender = body[:re.search(re_ender_ini, body).start()] + z

                            body = body[re.search(re_ender_fim, body).end():]

                            # Tratamento de assunto
                            re_ass_ini = re.compile('\{+(ASSUN_INI)\}')
                            re_ass_fim = re.compile('\{+(ASSUN_FIM)\}')
                            x = body[re.search(re_ass_ini, body).end():re.search(re_ass_fim, body).start()]
                            y = body[re.search(re_ass_fim, body).end():]
                            body = body[:re.search(re_ass_ini, body).start()] + 'Assunto:' + x + y

                            # Definição de impressora
                            db_action_report_xml = self.pool.get('ir.action.report.xml')
                            report_ids = db_action_report_xml.search(cr, uid, [('model', '=',
                                                                                'sncp.receita.print.report')])
                            db_action_report_xml.write(cr, uid, report_ids,
                                                       {'printing_printer_id': obj_param.crr_printer_id.id})
                            obj_report = db_action_report_xml.browse(cr, uid, report_ids[0])

                            # Preparação/impressão de relatório
                            body = cria_aviso(self, cr, uid, [obj_config, obj_controlo], body)
                            print_ids = list()
                            print_ids.append(self.create(cr, uid, {'ender': ender, 'corpo': body}))
                            vrs = virtual_report_spool(name='report')
                            obj = netsvc.LocalService('report.'+obj_report.report_name)
                            context['active_id'] = print_ids[0]
                            context['active_ids'] = print_ids
                            context['active_model'] = 'sncp.receita.print.report'
                            (result, formato) = obj.create(cr, uid, print_ids, {'report_type': u'pdf', }, context)
                            vrs.id = 1
                            vrs._reports = dict()
                            vrs._reports[vrs.id] = {}
                            vrs._reports[vrs.id]['result'] = result
                            vrs._reports[vrs.id]['exception'] = None
                            vrs._reports[vrs.id]['format'] = formato
                            vrs._reports[vrs.id]['state'] = True
                            vrs._reports[vrs.id]['uid'] = uid
                            vrs._reports[vrs.id]['report_name'] = 'sncp.receita.print.report.report'
                            virtual_report_spool.exp_report_get(vrs, cr.dbname, uid, 1)
                    # Conclusão
                    db_sncp_receita_controlo.write(cr, uid, aviso[1], {'avisado': True})

                except (RuntimeError, TypeError, NameError):
                    lista_nao_enviados.append(aviso[1])

        # Bloco de notificação de caducidade
        cr.execute("""SELECT RC.sector_id, RC.id FROM sncp_receita_controlo AS RC
            LEFT JOIN sncp_receita_controlo_config AS RCC ON RCC.id = RC.sector_id
            WHERE RC.caduc_notific is FALSE AND RC.fim <= CURRENT_DATE""")
        dados_caducidade = cr.fetchall()
        for caducidade in dados_caducidade:
            try:
                obj_config = db_sncp_receita_controlo_config.browse(cr, uid, caducidade[0])
                obj_controlo = db_sncp_receita_controlo.browse(cr, uid, caducidade[1])

                if obj_config.caduc_notif1_id.id is not False:
                    body = cria_aviso(self, cr, uid, [obj_config, obj_controlo],
                                      obj_config.caduc_notif_texto)
                    body_html = '<html><body>' + body.replace('\n', '<br>') + '</body></html>'
                    datahora = unicode(datetime.now())
                    if datahora.find('.') != -1:
                        datahora = datahora[:datahora.find('.')]
                    values_email = {
                        'attachment_ids': [[6, False, []]],
                        'auto_delete': False,
                        'body_html': unicode(body_html),
                        'email_to': unicode(obj_config.caduc_notif1_id.user_email),
                        'date': unicode(datahora),
                        'author_id': uid,
                        'type': 'email',
                        'email_from': u'openerp.notification@gmail.com',
                        'subject': u'Notificação de Caducidade de Controlo'}
                    if obj_config.caduc_notif2_id.id is not False:
                        values_email['email_cc'] = obj_config.caduc_notif2_id.partner_id.email
                    if obj_config.caduc_notif3_id.id is not False:
                        values_email['email_cc'] = values_email['email_cc'] + '; ' + \
                            obj_config.caduc_notif3_id.partner_id.email

                    mail_id = db_mail_mail.create(cr, uid, values_email)
                    db_mail_mail.send(cr, uid, [mail_id])
                    db_sncp_receita_controlo.write(cr, uid, caducidade[1], {'state': 'done', 'caduc_notific': True})

            except (RuntimeError, TypeError, NameError):
                lista_nao_enviados.append(caducidade[1])

        # Bloco de aviso ao administrador
        if len(lista_nao_enviados) > 0:
            cr.execute("""SELECT email FROM res_partner WHERE id IN (
                                  SELECT partner_id FROM res_users WHERE login = 'admin')""")
            email = cr.fetchone()
            text = u''
            for controlo in lista_nao_enviados:
                obj_controlo = db_sncp_receita_controlo.browse(cr, uid, controlo)
                z = unicode(obj_controlo.partner_id.name) + '<br>'
                text = text + unicode(obj_controlo.sector_id.name) + ' de ' + z

            body_html = '<html><body>' + \
                        u'Não foi possível enviar os avisos para os Controlos seguintes:<br>' + text + \
                        u' Verifique se o separador Caducidade está preenchido.' + \
                        '</body></html>'

            if email is not None:
                datahora = unicode(datetime.now())
                if datahora.find('.') != -1:
                    datahora = datahora[:datahora.find('.')]
                values_email = {
                    'attachment_ids': [[6, False, []]],
                    'auto_delete': False,
                    'body_html': unicode(body_html),
                    'email_to': unicode(email[0]),
                    'date': unicode(datahora),
                    'author_id': uid,
                    'type': 'email',
                    'email_from': u'openerp.notification@gmail.com',
                    'subject': u'Controlos não notificados'}
                mail_id = db_mail_mail.create(cr, uid, values_email)
                db_mail_mail.send(cr, uid, [mail_id])
            else:
                db_mail_message = self.pool.get('mail.message')
                db_mail_notification = self.pool.get('mail.notification')
                db_res_users = self.pool.get('res.users')
                utilizador = db_res_users.browse(cr, uid, uid)
                data = unicode(datetime.now())
                if data.find('.') != -1:
                    data = data[:data.find('.')]
                body_html = '<html><body>' + \
                            u'Não foi possível enviar os avisos para os Controlos seguintes:<br>' + text + \
                            u' Verifique se o separador Caducidade está preenchido. ' +\
                            u' Defina o email do utilizador desta sessão.' +\
                            '</body></html>'

                vals_message = {'type': 'comment',
                                'email_from': u'Notificação Automática',
                                'author_id': uid,
                                'subject': u'Considere definir email do administrador (utilizador desta sessão) '
                                           u'para evitar erros futuros',
                                'date': data,
                                'body': body_html, }

                message_id = db_mail_message.create(cr, uid, vals_message)

                vals_notification = {
                    'partner_id': utilizador.partner_id.id,
                    'read': False,
                    'message_id': message_id,
                }
                db_mail_notification.create(cr, uid, vals_notification)

        return True

    _columns = {
        'ender': fields.text(u'Endereço 1'),
        'corpo': fields.text(u''),
    }

sncp_receita_print_report()