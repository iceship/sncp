# -*- encoding: utf-8 -*-
# #############################################################################
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
from dateutil.relativedelta import *
from dateutil.rrule import *
import re
from openerp.osv import fields, osv
from openerp.tools.translate import _
import guia
# __________________________________________       METODOS EXTERNOS      _______________________________________


def test_partner_id(self, cr, uid, partner_id):
    db_res_partner = self.pool.get('res.partner')
    obj_partner = db_res_partner.browse(cr, uid, partner_id)
    message = u''

    if obj_partner.property_account_receivable.id is False:
            message += u'Contabilidade/Conta a receber (Cliente)\n'

    if obj_partner.property_account_payable.id is False:
        message += u'Contabilidade/Conta a receber (Fornecedor)\n'

    if len(message) != 0:
        raise osv.except_osv(_(u'Aviso'), _(u'Para evitar futuros erros na execução do programa '
                                            u'deverá preencher os seguintes campos do parceiro de negócio:\n'+message
                                            + u'.'))
    return True


def cria_notificacao(self, cr, uid, lista_obj, body):
    for obj in lista_obj:
        modelo = obj._name
        model_id = self.pool.get('ir.model').search(cr, uid, [('model', '=', unicode(modelo))])
        cr.execute("""SELECT name,path FROM sncp_comum_etiquetas
                      WHERE model_id = %d OR model_id IS NULL """ % model_id[0])
        etiquetas = cr.fetchall()
        dicti = obj._model.read(cr, uid, obj.id)
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


def trata_info(self, cr, uid, guia_id, context):
    cr.execute("""SELECT K.product_id, K.config, K.parceiro, COUNT(K.controlo) AS iteracoes FROM
    (SELECT AIL.product_id, RC.id AS controlo, RCC.id AS config, RC.partner_id AS parceiro
     FROM account_invoice_line AS AIL
        LEFT JOIN sncp_comum_codigos_contab AS CCC ON CCC.item_id = AIL.product_id
        LEFT JOIN sncp_receita_controlo_config AS RCC ON RCC.cod_contab_id = CCC.id
        LEFT JOIN sncp_receita_controlo AS RC ON RC.sector_id = RCC.id
        WHERE AIL.natureza = CCC.natureza AND AIL.invoice_id IN
        (SELECT fatura_id FROM sncp_receita_guia_rec_rel WHERE guia_id=%d)
        AND ( (RC.id IS NULL) OR (RC.partner_id=(SELECT partner_id FROM sncp_receita_guia_rec WHERE id=%d)))
        ) AS K
     WHERE K.config IS NOT NULL
     GROUP BY K.product_id, K.config, K.parceiro""" % (guia_id, guia_id))
    result = cr.fetchall()
    # result = [( 0 -- produto, 1 -- config(setor), 2 -- parceiro, 3 -- contador)]
    db_sncp_receita_controlo_config = self.pool.get('sncp.receita.controlo.config')
    db_sncp_receita_controlo = self.pool.get('sncp.receita.controlo')
    db_sncp_receita_guia_rec = self.pool.get('sncp.receita.guia.rec')
    db_mail_mail = self.pool.get('mail.mail')

    obj_guia = db_sncp_receita_guia_rec.browse(cr, uid, guia_id)

    for res in result:
        obj_config = db_sncp_receita_controlo_config.browse(cr, uid, res[1])
        values_email = {}
        if res[3] == 0:
            # Bloco de Notificação de Novo Controlo
            if obj_config.novo_notif1_id.id is not False:
                body = cria_notificacao(self, cr, uid, [obj_config, obj_guia], obj_config.novo_notif_texto)
                body_html = '<html><body>' + body.replace('\n', '<br>') + '</body></html>'
                datahora = unicode(datetime.now())
                if datahora.find('.') != -1:
                    datahora = datahora[:datahora.find('.')]
                values_email = {
                    'attachment_ids': [[6, False, []]],
                    'auto_delete': False,
                    'body_html': unicode(body_html),
                    'email_to': unicode(obj_config.novo_notif1_id.partner_id.email),
                    'date': unicode(datahora),
                    'author_id': uid,
                    'type': 'email',
                    'email_from': u'openerp.notification@gmail.com',
                    'subject': u'Notificação de Novo Controlo'}
                if obj_config.novo_notif2_id.id is not False:
                    values_email['email_cc'] = obj_config.novo_notif2_id.partner_id.email
                if obj_config.novo_notif3_id.id is not False:
                    values_email['email_cc'] = values_email['email_cc'] + '; ' + obj_config.novo_notif3_id.partner_id.email

                mail_id = db_mail_mail.create(cr, uid, values_email)
                db_mail_mail.send(cr, uid, [mail_id])

        elif res[3] == 1:
            # Renovar único automaticamente
            cr.execute("""SELECT id FROM sncp_receita_controlo
                          WHERE sector_id = %d AND partner_id = %d""" % (res[1], res[2]))
            controlo = cr.fetchone()[0]
            obj_controlo = db_sncp_receita_controlo.browse(cr, uid, controlo)
            if obj_controlo.renovacoes < obj_config.renova_limite or obj_config.renova_limite == -1:
                if obj_config.renov_notif1_id.id is not False:
                    body = cria_notificacao(self, cr, uid, [obj_config, obj_guia, obj_controlo],
                                            obj_config.renov_notif_texto)
                    body_html = '<html><body>' + body.replace('\n', '<br>') + '</body></html>'
                    datahora = unicode(datetime.now())
                    if datahora.find('.') != -1:
                        datahora = datahora[:datahora.find('.')]
                    values_email = {
                        'attachment_ids': [[6, False, []]],
                        'auto_delete': False,
                        'body_html': unicode(body_html),
                        'email_to': unicode(obj_config.renov_notif1_id.partner_id.email),
                        'date': unicode(datahora),
                        'author_id': uid,
                        'type': 'email',
                        'email_from': u'openerp.notification@gmail.com',
                        'subject': u'Notificação de Renovação de Controlo'}
                    if obj_config.renov_notif2_id.id is not False:
                        values_email['email_cc'] = obj_config.renov_notif2_id.partner_id.email
                    if obj_config.renov_notif3_id.id is not False:
                        notificado3 = obj_config.renov_notif3_id.partner_id.email
                        values_email['email_cc'] = values_email['email_cc'] + '; ' + notificado3

                    mail_id = db_mail_mail.create(cr, uid, values_email)
                    db_mail_mail.send(cr, uid, [mail_id])
                # Bloco de renovação automatica
                if obj_controlo.fim:
                    data = obj_controlo.fim
                else:
                    data = unicode(datetime.now())
                    if data.find('.') != -1:
                        data = data[:data.find('.')]
                vals = {
                    'data_reinicio': data,
                    'guia_id': guia_id,
                    'data_despacho': data,
                }
                db_sncp_receita_controlo.renovar_termo(cr, uid, [controlo], context, vals)
            else:
                # Bloco de Notificação de Novo Controlo
                if obj_config.novo_notif1_id.id is not False:
                    body = cria_notificacao(self, cr, uid, [obj_config, obj_guia], obj_config.novo_notif_texto)
                    body_html = '<html><body>' + body.replace('\n', '<br>') + '</body></html>'
                    datahora = unicode(datetime.now())
                    if datahora.find('.') != -1:
                        datahora = datahora[:datahora.find('.')]
                    values_email = {
                        'attachment_ids': [[6, False, []]],
                        'auto_delete': False,
                        'body_html': unicode(body_html),
                        'email_to': unicode(obj_config.novo_notif1_id.partner_id.email),
                        'date': unicode(datahora),
                        'author_id': uid,
                        'type': 'email',
                        'email_from': u'openerp.notification@gmail.com',
                        'subject': u'Notificação de Novo Controlo'}
                    if obj_config.novo_notif2_id.id is not False:
                        values_email['email_cc'] = obj_config.novo_notif2_id.partner_id.email
                    if obj_config.novo_notif3_id.id is not False:
                        notificado3 = obj_config.novo_notif3_id.partner_id.email
                        values_email['email_cc'] = values_email['email_cc'] + '; ' + notificado3

                    mail_id = db_mail_mail.create(cr, uid, values_email)
                    db_mail_mail.send(cr, uid, [mail_id])
        else:
            # Avisar sobre renovação multipla
            cr.execute("""SELECT id FROM sncp_receita_controlo
                          WHERE sector_id = %d AND partner_id = %d""" % (res[1], res[2]))
            controlos = cr.fetchall()
            for controlo in controlos:
                obj_controlo = db_sncp_receita_controlo.browse(cr, uid, controlo[0])
                if obj_controlo.renovacoes < obj_config.renova_limite or obj_config.renova_limite == -1:
                    if obj_config.renov_notif1_id.id is not False:
                        body = cria_notificacao(self, cr, uid, [obj_config, obj_guia, obj_controlo],
                                                obj_config.renov_notif_texto)
                        body_html = '<html><body>' + body.replace('\n', '<br>') + '</body></html>'
                        datahora = unicode(datetime.now())
                        if datahora.find('.') != -1:
                            datahora = datahora[:datahora.find('.')]
                        values_email = {
                            'attachment_ids': [[6, False, []]],
                            'auto_delete': False,
                            'body_html': unicode(body_html),
                            'email_to': unicode(obj_config.renov_notif1_id.partner_id.email),
                            'date': unicode(datahora),
                            'author_id': uid,
                            'type': 'email',
                            'email_from': u'openerp.notification@gmail.com',
                            'subject': u'Notificação de Renovação de Controlo'}
                        if obj_config.renov_notif2_id.id is not False:
                            values_email['email_cc'] = obj_config.renov_notif2_id.partner_id.email
                        if obj_config.renov_notif3_id.id is not False:
                            notificado3 = obj_config.renov_notif3_id.partner_id.email
                            values_email['email_cc'] = values_email['email_cc'] + '; ' + notificado3

                        mail_id = db_mail_mail.create(cr, uid, values_email)
                        db_mail_mail.send(cr, uid, [mail_id])
    return True


# _________________________________________________ Configuração de Controlo _______________________________
class sncp_receita_controlo_config(osv.Model):
    _name = 'sncp.receita.controlo.config'
    _description = u"Configuração de Controlo"

    def on_change_renova(self, cr, uid, ids, renova):
        if renova is False:
            self.write(cr, uid, ids, {'automatica': False, 'renova_limite': 0,
                                      'renova_req': False, 'renova_aprov_id': 0})
            return {'value': {
                'automatica': False,
                'renova_limite': 0,
                'renova_req': False,
                'renova_aprov_id': 0,
            }}
        else:
            self.write(cr, uid, ids, {'renova_limite': 0, })
            return {'value': {'renova_limite': -1, }}

    def on_change_renova_req(self, cr, uid, ids, renova_req):
        if renova_req is False:
            self.write(cr, uid, ids, {'renova_aprov_id': 0})
            return {'value': {
                'renova_aprov_id': 0,
            }}
        else:
            return {}

    def on_change_validade_tipo(self, cr, uid, ids, validade_tipo):
        if validade_tipo == 'indfty':
            self.write(cr, uid, ids, {'renova': False, 'validade_num': 0})
            return {'value': {
                'renova': False,
                'validade_num': 0,
            }}
        else:
            self.write(cr, uid, ids, {'pagam_tipo': '4each'})
            return {'value': {
                'pagam_tipo': '4each',
            }}

    def on_change_automatica(self, cr, uid, ids, automatica):
        if automatica is True:
            self.write(cr, uid, ids, {'renova_req': False, 'renova_aprov_id': 0})
            return {'value': {
                'renova_req': False,
                'renova_aprov_id': 0,
            }}
        else:
            return {}

    def on_change_user_id(self, cr, uid, ids, user_id):
        if user_id is False:
            return {}
        db_res_users = self.pool.get('res.users')
        obj_user = db_res_users.browse(cr, uid, user_id)
        if obj_user.partner_id.email is False:
            return {'warning': {'title': 'Aviso',
                                'message': u'Utilizador ' + obj_user.partner_id.name +
                                           u' não têm endereço de Correio Eletrónico.'}}
        return {}

    _columns = {
        'name': fields.char(u'Controlo', size=64),
        'tipo_controlo': fields.selection([('1', u'Estacionamento de moradores'),
                                           ('2', u'Estacionamento privativo'),
                                           ('3', u'Ocupação de espaço público'),
                                           ('4', u'Publicidade'),
                                           ('5', u'Máquinas de diversão'),
                                           ('6', u'Venda ambulante'),
                                           ('7', u'Arrendamentos'), ], u'Tipo de Controlo'),
        'cod_contab_id': fields.many2one('sncp.comum.codigos.contab', u'Código de Contabilização',
                                         domain=[('natureza', 'in', ['rec', 'ots'])], ),
        'validade_num': fields.integer(u'Validade do Contrato/Licença'),
        'validade_tipo': fields.selection([('days', u'Dias'), ('wdays', u'Dias Úteis'),
                                           ('weeks', u'Semanas'), ('months', u'Meses'),
                                           ('indfty', u'Indeterminado')], u'Unidade'),
        'renova': fields.boolean(u'Renovável'),
        'automatica': fields.boolean(u'Automaticamente'),
        'renova_limite': fields.integer(u'Máximo de renovações'),
        'renova_req': fields.boolean(u'Renovação a Requerimento'),
        'renova_aprov_id': fields.many2one('res.users', u'Por despacho de'),
        'pagam_tipo': fields.selection([('4each', u'Em cada renovação'),
                                        ('daily', u'Diariamente'),
                                        ('weekly', u'Semanalmente'),
                                        ('fortnightly', u'Quinzenalmente'),
                                        ('monthly', u'Mensalmente'),
                                        ('quarterly', u'Trimestralmente'),
                                        ('semiannually', u'Semestralmente'),
                                        ('annually', u'Anualmente'), ], u'Pagamento'),
        'cond_pagam_id': fields.many2one('sncp.comum.cond.pagam', u'Condições de Pagamento'),
        'aviso_prev': fields.integer(u'Dias de Aviso Prévio'),
        'aviso_texto': fields.text(u'Texto de Aviso'),
        'novo_notif1_id': fields.many2one('res.users', u'Novo Notifica'),
        'novo_notif2_id': fields.many2one('res.users', u''),
        'novo_notif3_id': fields.many2one('res.users', u''),
        'novo_notif_texto': fields.text(u'Texto de notificação do novo'),
        'caduc_notif1_id': fields.many2one('res.users', u'Caducidade notifica'),
        'caduc_notif2_id': fields.many2one('res.users', u''),
        'caduc_notif3_id': fields.many2one('res.users', u''),
        'caduc_notif_texto': fields.text(u'Texto de notificação de caducidade'),
        'renov_notif1_id': fields.many2one('res.users', u'Renovação notifica'),
        'renov_notif2_id': fields.many2one('res.users', u''),
        'renov_notif3_id': fields.many2one('res.users', u''),
        'renov_notif_texto': fields.text(u'Texto de notificação de renovação'),
        'last_uid': fields.many2one('res.users', u'Utilizador responsável pela última alteração'),
        'last_date': fields.datetime(u'Última data de alteração'),
    }

    _defaults = {

    }

    def create(self, cr, uid, vals, context=None):
        tipo_controlo = ''
        db_sncp_comum_codigos_contab = self.pool.get('sncp.comum.codigos.contab')
        obj_cod_contab = db_sncp_comum_codigos_contab.browse(cr, uid, vals['cod_contab_id'])
        if vals['tipo_controlo'] == '1':
            tipo_controlo = u'Estacionamento de moradores'
        if vals['tipo_controlo'] == '2':
            tipo_controlo = u'Estacionamento privativo'
        if vals['tipo_controlo'] == '3':
            tipo_controlo = u'Ocupação de espaço público'
        if vals['tipo_controlo'] == '4':
            tipo_controlo = u'Publicidade'
        if vals['tipo_controlo'] == '5':
            tipo_controlo = u'Máquinas de diversão'
        if vals['tipo_controlo'] == '6':
            tipo_controlo = u'Venda ambulante'
        if vals['tipo_controlo'] == '7':
            tipo_controlo = u'Arrendamentos'
        vals['last_uid'] = uid
        datahora = unicode(datetime.now())
        if datahora.find('.') != -1:
            datahora = datahora[:datahora.find('.')]
        vals['last_date'] = datahora
        vals['name'] = tipo_controlo + ' (' + unicode(obj_cod_contab.item_id.default_code) + ')'
        return super(sncp_receita_controlo_config, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        vals['last_uid'] = uid
        datahora = unicode(datetime.now())
        if datahora.find('.') != -1:
            datahora = datahora[:datahora.find('.')]
        vals['last_date'] = datahora
        return super(sncp_receita_controlo_config, self).write(cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        db_sncp_receita_controlo = self.pool.get('sncp.receita.controlo')

        for nid in ids:
            cr.execute("""
            SELECT id FROM sncp_receita_controlo
            WHERE sector_id = %d
            """ % nid)

            controlos_ids = cr.fetchall()
            if len(controlos_ids) != 0:
                for controlo_id in controlos_ids:
                    obj_controlo = db_sncp_receita_controlo.browse(cr, uid, controlo_id[0])
                    if obj_controlo.state == 'draft':
                        cr.execute("""
                        DELETE FROM sncp_receita_controlo_guias
                        WHERE controlo_id = %d
                        """ % controlo_id[0])
                        cr.execute("""
                        DELETE FROM sncp_receita_controlo
                        WHERE id = %d
                        """ % controlo_id[0])

            cr.execute("""
            SELECT id FROM sncp_receita_controlo
            WHERE sector_id = %d
            """ % nid)

            resultado = cr.fetchall()
            if len(resultado) == 0:
                cr.execute("""
                DELETE FROM sncp_receita_controlo_config
                WHERE id = %d
                """ % nid)

        return True

    _order = 'name,cod_contab_id'

    def _restrict_renova_limite(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.renova is True:
            if obj.renova_limite >= -1 and obj.renova_limite != 0:
                return True
            else:
                raise osv.except_osv(_(u'Erro de Restrição'),
                                     _(u'Se o Controlo é renovável, o Máximo de renovações '
                                       u'têm que ser positivo.'
                                       u'Caso o Controlo é permanente coloque o -1.'))
        return True

    def _restrict_novo1(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj.novo_notif1_id.id > 0 and obj.novo_notif1_id.partner_id.email is False:
            raise osv.except_osv(_(u'Erro de Restrição de Notificação de Novo'),
                                 _(u'Utilizadores seguintes não podem ser notificados '
                                   u'devido à ausência do endereço de Correio Eletrónico válido: \n' +
                                   obj.novo_notif1_id.partner_id.name))
        return True

    def _restrict_novo2(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj.novo_notif2_id.id > 0 and obj.novo_notif2_id.partner_id.email is False:
            raise osv.except_osv(_(u'Erro de Restrição de Notificação de Novo'),
                                 _(u'Utilizadores seguintes não podem ser notificados '
                                   u'devido à ausência do endereço de Correio Eletrónico válido: \n' +
                                   obj.novo_notif2_id.partner_id.name))
        return True

    def _restrict_novo3(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj.novo_notif3_id.id > 0 and obj.novo_notif3_id.partner_id.email is False:
            raise osv.except_osv(_(u'Erro de Restrição de Notificação de Novo'),
                                 _(u'Utilizadores seguintes não podem ser notificados '
                                   u'devido à ausência do endereço de Correio Eletrónico válido: \n' +
                                   obj.novo_notif3_id.partner_id.name))
        return True

    def _restrict_caduc1(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj.caduc_notif1_id.id > 0 and obj.caduc_notif1_id.partner_id.email is False:
            raise osv.except_osv(_(u'Erro de Restrição de Notificação de Caducidade'),
                                 _(u'Utilizadores seguintes não podem ser notificados '
                                   u'devido à ausência do endereço de Correio Eletrónico válido: \n' +
                                   obj.caduc_notif1_id.partner_id.name))
        return True

    def _restrict_caduc2(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj.caduc_notif2_id.id > 0 and obj.caduc_notif2_id.partner_id.email is False:
            raise osv.except_osv(_(u'Erro de Restrição de Notificação de Caducidade'),
                                 _(u'Utilizadores seguintes não podem ser notificados '
                                   u'devido à ausência do endereço de Correio Eletrónico válido: \n' +
                                   obj.caduc_notif2_id.partner_id.name))
        return True

    def _restrict_caduc3(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj.caduc_notif3_id.id > 0 and obj.caduc_notif3_id.partner_id.email is False:
            raise osv.except_osv(_(u'Erro de Restrição de Notificação de Caducidade'),
                                 _(u'Utilizadores seguintes não podem ser notificados '
                                   u'devido à ausência do endereço de Correio Eletrónico válido: \n' +
                                   obj.caduc_notif3_id.partner_id.name))
        return True

    def _restrict_renov1(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj.renov_notif1_id.id > 0 and obj.renov_notif1_id.partner_id.email is False:
            raise osv.except_osv(_(u'Erro de Restrição de Notificação de Renovação'),
                                 _(u'Utilizadores seguintes não podem ser notificados '
                                   u'devido à ausência do endereço de Correio Eletrónico válido: \n' +
                                   obj.renov_notif1_id.partner_id.name))
        return True

    def _restrict_renov2(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj.renov_notif2_id.id > 0 and obj.renov_notif2_id.partner_id.email is False:
            raise osv.except_osv(_(u'Erro de Restrição de Notificação de Renovação'),
                                 _(u'Utilizadores seguintes não podem ser notificados '
                                   u'devido à ausência do endereço de Correio Eletrónico válido: \n' +
                                   obj.renov_notif2_id.partner_id.name))
        return True

    def _restrict_renov3(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj.renov_notif3_id.id > 0 and obj.renov_notif3_id.partner_id.email is False:
            raise osv.except_osv(_(u'Erro de Restrição de Notificação de Renovação'),
                                 _(u'Utilizadores seguintes não podem ser notificados '
                                   u'devido à ausência do endereço de Correio Eletrónico válido: \n' +
                                   obj.renov_notif3_id.partner_id.name))
        return True

    def _restrict_aviso_texto(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        message = ''
        if type(obj.aviso_texto) in [str, unicode] and len(obj.aviso_texto) > 0:

            re_renov_ini = re.compile('\{(RENOV_INI)\}')
            re_renov_fim = re.compile('\{(RENOV_FIM)\}')
            if re.search(re_renov_ini, obj.aviso_texto) and not re.search(re_renov_fim, obj.aviso_texto):
                message += u' -- Falta a TAG do fim de Renovação {RENOV_FIM}\n'
            elif not re.search(re_renov_ini, obj.aviso_texto) and re.search(re_renov_fim, obj.aviso_texto):
                message += u' -- Falta a TAG do inicio de Renovação {RENOV_INI}\n'

            re_ass_ini = re.compile('\{(ASSUN_INI)\}')
            re_ass_fim = re.compile('\{(ASSUN_FIM)\}')
            if not re.search(re_ass_ini, obj.aviso_texto) and not re.search(re_ass_fim, obj.aviso_texto):
                message += u' -- Falta o bloco de Assunto {ASSUN_INI} Texto do Assunto {ASSUN_FIM}\n'
            elif re.search(re_ass_ini, obj.aviso_texto) and not re.search(re_ass_fim, obj.aviso_texto):
                message += u' -- Falta a TAG do fim de Assunto {ASSUN_FIM}\n'
            elif not re.search(re_ass_ini, obj.aviso_texto) and re.search(re_ass_fim, obj.aviso_texto):
                message += u' -- Falta a TAG do inicio de Assunto {ASSUN_INI}\n'

            re_ender_ini = re.compile('\{(ENDER_INI)\}')
            re_ender_fim = re.compile('\{(ENDER_FIM)\}')
            if not re.search(re_ender_ini, obj.aviso_texto) and not re.search(re_ender_fim, obj.aviso_texto):
                message += u' -- Falta o bloco de Endereço {ENDER_INI} Texto do Endereço {ENDER_FIM}\n'
            elif re.search(re_ender_ini, obj.aviso_texto) and not re.search(re_ender_fim, obj.aviso_texto):
                message += u' -- Falta a TAG do fim de Endereço {ENDER_FIM}\n'
            elif not re.search(re_ender_ini, obj.aviso_texto) and re.search(re_ender_fim, obj.aviso_texto):
                message += u' -- Falta a TAG do inicio de Endereço {ENDER_INI}\n'

        if len(message) > 0:
            raise osv.except_osv(_(u'Erro de  preenchimento de Texto de aviso.\n'),
                                 _(message))
        return True

    _constraints = [
        (_restrict_renova_limite, u'', ['renova_limite']),
        (_restrict_novo1, u'', ['novo_notif1_id']),
        (_restrict_novo2, u'', ['novo_notif2_id']),
        (_restrict_novo3, u'', ['novo_notif3_id']),
        (_restrict_caduc1, u'', ['caduc_notif1_id']),
        (_restrict_caduc2, u'', ['caduc_notif2_id']),
        (_restrict_caduc3, u'', ['caduc_notif3_id']),
        (_restrict_renov1, u'', ['renov_notif1_id']),
        (_restrict_renov2, u'', ['renov_notif2_id']),
        (_restrict_renov3, u'', ['renov_notif3_id']),
        (_restrict_aviso_texto, u'', ['aviso_texto']),
    ]

    _sql_constraints = [
        ('name_item_unique', 'unique (name,cod_contab_id)', u'Este ítem já têm controlo registado')
    ]


sncp_receita_controlo_config()

# _____________________________________________ Controlo (cabeçalho)___________________________________________________


class sncp_receita_controlo(osv.Model):
    _name = 'sncp.receita.controlo'
    _description = u"Controlo de Receita"

    def on_change_sector_id(self, cr, uid, ids, sector_id):
        db_sncp_receita_controlo_config = self.pool.get('sncp.receita.controlo.config')
        obj_sector = db_sncp_receita_controlo_config.browse(cr, uid, sector_id)
        return {'value': {'despacho_user_id': obj_sector.renova_aprov_id.id}}

    def on_change_freguesia_id(self, cr, uid, ids, freguesia_id):
        if freguesia_id is False:
            return {'value': {'arruamento_id': 0,
                              'bairro_id': 0}}
        # Bloco de filtro Arruamentos
        cr.execute("""SELECT id FROM sncp_comum_arruamentos WHERE freguesia1_id = %d OR freguesia2_id = %d
        """ % (freguesia_id, freguesia_id))
        result_a = cr.fetchall()
        lista_arruamentos = []
        for res in result_a:
            lista_arruamentos.append(res[0])

        # Bloco de filtro Bairros
        cr.execute("""SELECT id FROM sncp_comum_bairros WHERE freguesia_id = %d""" % freguesia_id)
        result_b = cr.fetchall()
        lista_bairros = []
        for res in result_b:
            lista_bairros.append(res[0])

        lista_arruamentos = list(set(lista_arruamentos))
        lista_bairros = list(set(lista_bairros))

        return {'domain': {'arruamento_id': [('id', 'in', lista_arruamentos)],
                           'bairro_id': [('id', 'in', lista_bairros)]},
                'value': {'arruamento_id': 0, 'bairro_id': 0}}

    def on_change_medidas(self, cr, uid, ids, comprimento, largura, altura, area, volume):
        if comprimento != 0 and largura != 0:
            area = comprimento * largura
        if comprimento != 0 and largura != 0 and altura != 0:
            volume = comprimento * largura * altura
        self.write(cr, uid, ids, {'area': area, 'volume': volume})
        return {'value': {'area': area, 'volume': volume}}

    def on_change_partner_id(self, cr, uid, ids, partner_id):
        db_res_partner = self.pool.get('res.partner')
        obj_partner = db_res_partner.browse(cr, uid, partner_id)
        if not obj_partner.email:
            if not obj_partner.city or \
                    not obj_partner.zip or \
                    not obj_partner.country_id.id or \
                    not obj_partner.street:
                return {'warning': {'title': 'Aviso',
                                    'message': u'Este parceiro de Negócios não têm nem endereço de correio eletrónico,'
                                               u' nem a morada definidos.'}}
            else:
                return {'warning': {'title': 'Aviso',
                                    'message': u'Este parceiro de Negócios não têm nem endereço de correio eletrónico'
                                               u' definido.'}}
        else:
            if not obj_partner.city or \
                    not obj_partner.zip or \
                    not obj_partner.country_id.id or \
                    not obj_partner.street:
                return {'warning': {'title': 'Aviso',
                                    'message': u'Este parceiro de Negócios não têm a morada definida.'}}
            else:
                return {}

    # METODOS INTERNOS
    def activar(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        vals = {
            'partner_id': obj.partner_id.id,
            'cod_contab_id': obj.sector_id.cod_contab_id.id,
            'action': 'activar'}
        return self.pool.get('formulario.sncp.receita.select.guia').wizard(cr, uid, ids, vals)

    def activar_termo(self, cr, uid, ids, context, vals):
        db_sncp_receita_controlo_guias = self.pool.get('sncp.receita.controlo.guias')
        db_sncp_receita_guia_rec = self.pool.get('sncp.receita.guia.rec')
        obj = self.browse(cr, uid, ids[0])
        obj_guia = db_sncp_receita_guia_rec.browse(cr, uid, vals['guia_id'])
        data_fim = None
        data_inicio = datetime.strptime(obj.inicio, "%Y-%m-%d %H:%M:%S")
        if obj.duracao_tipo == 'days':
            data_fim = data_inicio + relativedelta(days=obj.duracao_num) - relativedelta(days=1)
        if obj.duracao_tipo == 'wdays':
            data_fim = rrule(DAILY, byweekday=(MO, TU, WE, TH, FR),
                             dtstart=data_inicio)[obj.duracao_num] - relativedelta(days=1)
        if obj.duracao_tipo == 'weeks':
            data_fim = data_inicio + relativedelta(weeks=obj.duracao_num) - relativedelta(days=1)
        if obj.duracao_tipo == 'months':
            data_fim = data_inicio + relativedelta(months=obj.duracao_num) - relativedelta(days=1)
        if obj.duracao_tipo == 'years':
            data_fim = data_inicio + relativedelta(years=obj.duracao_num) - relativedelta(days=1)

        db_sncp_receita_controlo_guias.create(cr, uid, {
            'name': obj_guia.name,
            'controlo_id': ids[0],
            'guia_id': vals['guia_id'],
            'data_ini': unicode(data_inicio),
            'data_fim': data_fim,
        })
        self.write(cr, uid, ids, {'state': 'running', 'fim': data_fim})
        return True

    def renovar(self, cr, uid, ids, context):
        obj = self.browse(cr, uid, ids[0])
        vals = {
            'partner_id': obj.partner_id.id,
            'cod_contab_id': obj.sector_id.cod_contab_id.id,
            'action': 'renovar'}
        return self.pool.get('formulario.sncp.receita.select.guia').wizard(cr, uid, ids, vals)

    def renovar_termo(self, cr, uid, ids, context, vals):
        db_sncp_receita_controlo_guias = self.pool.get('sncp.receita.controlo.guias')
        db_sncp_receita_guia_rec = self.pool.get('sncp.receita.guia.rec')
        obj = self.browse(cr, uid, ids[0])
        obj_guia = db_sncp_receita_guia_rec.browse(cr, uid, vals['guia_id'])
        data_fim = None
        data_reinicio = datetime.strptime(vals['data_reinicio'], "%Y-%m-%d %H:%M:%S")
        if obj.duracao_tipo == 'days':
            data_fim = data_reinicio + relativedelta(days=(obj.duracao_num - 1))
        if obj.duracao_tipo == 'wdays':
            data_fim = rrule(DAILY, byweekday=(MO, TU, WE, TH, FR),
                             dtstart=data_reinicio)[obj.duracao_num] - relativedelta(days=1)
        if obj.duracao_tipo == 'weeks':
            data_fim = data_reinicio + relativedelta(weeks=obj.duracao_num) - relativedelta(days=1)
        if obj.duracao_tipo == 'months':
            data_fim = data_reinicio + relativedelta(months=obj.duracao_num) - relativedelta(days=1)
        if obj.duracao_tipo == 'years':
            data_fim = data_reinicio + relativedelta(years=obj.duracao_num) - relativedelta(days=1)

        db_sncp_receita_controlo_guias.create(cr, uid, {
            'name': obj_guia.name,
            'controlo_id': ids[0],
            'guia_id': vals['guia_id'],
            'data_ini': vals['data_reinicio'],
            'data_fim': data_fim,
        })
        self.write(cr, uid, ids, {'state': 'running', 'fim': data_fim,
                                  'despacho_data': vals['data_despacho'],
                                  'avisado': False, 'caduc_notific': False,
                                  'renovacoes': obj.renovacoes + 1})
        return True

    # Teste de metodos externos
    # def trata_info(self, cr, uid, ids, context):
    #     return trata_info(self, cr, uid, ids, context)

    # def avisa(self, cr, uid, ids, context=None):
    #     db_sncp_receita_print_report = self.pool.get('sncp.receita.print.report')
    #     return db_sncp_receita_print_report.avisa(cr, uid, context=context)

    _columns = {
        'sector_id': fields.many2one('sncp.receita.controlo.config', u'Sector'),
        'item_descr': fields.related('sector_id', 'cod_contab_id', 'name', type="text", store=True, string=u"Item"),
        'renova_req': fields.related('sector_id', 'renova_req', type="boolean", store=False,
                                     string="Renovação a Requerimento"),
        'partner_id': fields.many2one('res.partner', u'Parceiro de Negócios',
                                      domain=[('customer', '=', True)]),
        'sequencia': fields.integer(u'Sequência'),
        'freguesia_id': fields.many2one('sncp.comum.freguesias', u'Freguesia'),
        'bairro_id': fields.many2one('sncp.comum.bairros', u'Bairro'),
        'arruamento_id': fields.many2one('sncp.comum.arruamentos', u'Arruamento'),
        'numero': fields.char(u'Número de polícia', size=6),
        'andar': fields.char(u'Andar, etc', size=16),
        'zona_id': fields.many2one('sncp.receita.zonas.venda.amb', u'Zona'),
        'mercado_id': fields.many2one('sncp.receita.mercados.feiras', u'Mercado ou Feira'),
        'finalidade_id': fields.many2one('sncp.receita.oep.finalidades', u'Finalidade'),
        'comprimento': fields.float(u'Comprimento', digits=(12, 3)),
        'largura': fields.float(u'Largura', digits=(12, 3)),
        'area': fields.float(u'Área', digits=(12, 3)),
        'altura': fields.float(u'Altura', digits=(12, 3)),
        'volume': fields.float(u'Volume', digits=(12, 3)),
        'num_itens': fields.integer(u'Número de lugares'),
        'name': fields.char(u'Número de Série', size=32),
        'notas': fields.text(u'Notas'),
        'duracao_num': fields.integer(u'Duração do período'),
        'duracao_tipo': fields.selection([('hours', u'Horas'),
                                          ('days', u'Dias'),
                                          ('wdays', u'Dias Úteis'),
                                          ('weeks', u'Semanas'),
                                          ('months', u'Meses'),
                                          ('years', u'Anos'),
                                          ('perpetual', u'Perpetua'),
                                          ('indfly', u'Indeterminada'), ], u'Unidade'),
        'inicio': fields.datetime(u'Desde'),
        'fim': fields.datetime(u'Até'),
        'renovacoes': fields.integer(u'Renovações'),
        'despacho_user_id': fields.many2one('res.users', u'Despacho de'),
        'despacho_data': fields.datetime(u'em'),
        'avisado': fields.boolean(u'Avisado'),
        'caduc_notific': fields.boolean(u'Caducidade Notificada'),
        'state': fields.selection([('draft', u'Rascunho'),
                                   ('running', u'Activo'),
                                   ('done', u'Completo')], u'Estado'),
        'controlo_guias_ids': fields.one2many('sncp.receita.controlo.guias', 'controlo_id', u'Guias'),
    }

    _defaults = {
        'state': 'draft',
        'renovacoes': 0,
    }

    def create(self, cr, uid, vals, context=None):
        test_partner_id(self, cr, uid, vals['partner_id'])
        vals['sequencia'] = guia.get_sequence(self, cr, uid, context, 'controlo_SecPart',
                                              unicode(vals['sector_id']) + '_' + unicode(vals['partner_id']))
        if vals['comprimento'] != 0 and vals['largura'] != 0:
            vals['area'] = vals['comprimento'] * vals['largura']
        if vals['comprimento'] != 0 and vals['largura'] != 0 and vals['altura'] != 0:
            vals['volume'] = vals['comprimento'] * vals['altura'] * vals['largura']
        return super(sncp_receita_controlo, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'zona_id' in vals:
            vals['mercado_id'] = False
        elif 'mercado_id' in vals:
            vals['zona_id'] = False

        return super(sncp_receita_controlo, self).write(cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)
            if obj.state == 'draft':
                cr.execute("""
                DELETE FROM sncp_receita_controlo_guias WHERE controlo_id = %d
                """ % nid)
                cr.execute("""
                DELETE FROM sncp_receita_controlo
                WHERE id = %d
                """ % nid)

        return True

    _order = 'sector_id,partner_id,sequencia'

    def _restrict_num_itens(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.sector_id.tipo_controlo in ['1', '2'] and obj.num_itens <= 0:
            raise osv.except_osv(_(u'Erro de Restrição'),
                                 _(u'Número de lugares têm que ser superior a 0.'))
        return True

    def _restrict_duracao_num(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.duracao_tipo not in ['perpetual', 'indfly'] and obj.duracao_num <= 0:
            raise osv.except_osv(_(u'Erro de Restrição'),
                                 _(u'Duração têm que ser superior a 0.'))
        return True

    def _restrict_numero(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.sector_id.tipo_controlo in ['2', '3', '5', '7'] and obj.numero <= 0:
            raise osv.except_osv(_(u'Erro de Restrição'),
                                 _(u'Número de polícia têm que ser positivo.'))
        return True

    def _restrict_partner_id(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if not obj.partner_id.email:
            if not obj.partner_id.city or \
                    not obj.partner_id.zip or not obj.partner_id.country_id.id or \
                    not obj.partner_id.street:
                raise osv.except_osv(_(u'Erro de Restrição'),
                                     _(u'O Parceiro de Negócio tem que ter obrigatoriamente definido ou endereço'
                                       u' de correio eletrónico ou a morada.'))
        return True

    _constraints = [
        (_restrict_num_itens, u'', ['num_itens']),
        (_restrict_duracao_num, u'', ['duracao_num']),
        (_restrict_numero, u'', ['numero']),
        (_restrict_partner_id, u'', ['partner_id']),
    ]

    _sql_constraints = [
        ('controlo_receita_unique', 'unique (sector_id,partner_id,sequencia)', u'O registo já existe')
    ]


sncp_receita_controlo()

# ________________________________________________ Controlo de Guias (linhas)_______________________________


class sncp_receita_controlo_guias(osv.Model):
    _name = 'sncp.receita.controlo.guias'
    _description = u'Controlo de Guias'

    _columns = {
        'name': fields.char(u'Guia de Receita', size=12),
        'controlo_id': fields.many2one('sncp.receita.controlo', u'Controlo'),
        'guia_id': fields.many2one('sncp.receita.guia.rec', u'Guia de Receita'),
        'data_emissao': fields.related('guia_id', 'data_emissao', type="char",
                                       store=True, string=u"Data de emissão"),
        'montante': fields.related('guia_id', 'montante', type="char", store=True, string="Montante"),
        'parceiro_ref': fields.related('guia_id', 'partner_id', 'name', type="char",
                                       store=True, string=u"Parceiro de Negócio"),
        'data_ini': fields.datetime(u'Início do período'),
        'data_fim': fields.datetime(u'Fim do período'),
    }

    _sql_constraints = [
        ('controlo_guia_unique', 'unique (controlo_id,guia_id)', u'Esta guia já foi utilizada')
    ]


sncp_receita_controlo_guias()

# ________________________________________________ Venda Ambulante _____________________________________


class sncp_receita_zonas_venda_amb(osv.Model):
    _name = 'sncp.receita.zonas.venda.amb'
    _description = u"Zonas de Venda Ambulante"

    def open_map(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj = self.browse(cr, uid, ids, context=context)[0]
        url = "http://maps.google.com/maps?oi=map&q="
        if obj.coord_p1:
            url += '+' + obj.coord_p1.replace(' ', '+')
        elif obj.coord_p2:
            url += '+' + obj.coord_p2.replace(' ', '+')
        elif obj.coord_p3:
            url += '+' + obj.coord_p3.replace(' ', '+')
        elif obj.coord_p4:
            url += '+' + obj.coord_p4.replace(' ', '+')

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new'
        }

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_receita_controlo
            WHERE zona_id = %d
            """ % obj.id)

            res_controlo = cr.fetchall()

            if len(res_controlo) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se a zona de venda ambulante '
                                                    + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Receita\Controlo de Receitas Renováveis.'))

        return super(sncp_receita_zonas_venda_amb, self).unlink(cr, uid, ids, context=context)

    _columns = {
        'name': fields.char(u'Designação da Zona', size=64),
        'notas': fields.text(u'Detalhes'),
        'coord_p1': fields.char(u'Coordenadas ponto 1', size=30),
        'coord_p2': fields.char(u'Coordenadas ponto 2', size=30),
        'coord_p3': fields.char(u'Coordenadas ponto 3', size=30),
        'coord_p4': fields.char(u'Coordenadas ponto 4', size=30),
    }

    _order = 'name'

    _sql_constraints = [
        ('zona_amb_unique', 'unique (name)', u'Esta Zona de Venda Ambulante já está registada')
    ]


sncp_receita_zonas_venda_amb()

# ________________________________________________ Mercados e Feiras _____________________________


class sncp_receita_mercados_feiras(osv.Model):
    _name = 'sncp.receita.mercados.feiras'
    _description = u"Mercados e Feiras"

    def open_map(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj = self.browse(cr, uid, ids, context=context)[0]
        url = "http://maps.google.com/maps?oi=map&q="
        if obj.coord_centro:
            url += '+' + obj.coord_centro.replace(' ', '+')
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new'
        }

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_receita_controlo
            WHERE mercado_id = %d
            """ % obj.id)

            res_controlo = cr.fetchall()

            if len(res_controlo) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se o mercado ou feira '
                                                    + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Receita\Controlo de Receitas Renováveis.'))

        return super(sncp_receita_mercados_feiras, self).unlink(cr, uid, ids, context=context)

    _columns = {
        'name': fields.char(u'Designação'),
        'tipo': fields.selection([('mercado', u'Mercado'),
                                  ('feira', u'Feira'), ], u'Tipologia'),
        'realizacao': fields.selection([('dayly', u'Diária'),
                                        ('dayly-1', u'Segunda a Sábado'),
                                        ('wdayly', u'Segunda a Sexta'),
                                        ('weekly', u'Semanal'),
                                        ('monthly', u'Mensal'), ], u'Realização'),
        'dia': fields.integer(u'Dia'),
        'coord_centro': fields.char(u'Coordenadas do Centro', size=30),
        'area': fields.float(u'Área total', digits=(12, 3)),
        'area_coberta': fields.float(u'Área coberta', digits=(12, 3)),
        'notas': fields.text(u'Notas'),
    }

    def write(self, cr, uid, ids, vals, context=None):
        if 'realizacao' in vals:
            if vals['realizacao'] not in ['weekly', 'monthly']:
                vals['dia'] = 0

        return super(sncp_receita_mercados_feiras, self).write(cr, uid, ids, vals, context=None)

    def restrict_dia(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        if obj.realizacao in ['weekly', 'monthly']:
            if obj.dia not in range(1, 32):
                raise osv.except_osv(_(u'Aviso'), _(u' O dia deve estar entre 1 e 31.'))

        return True

    _order = 'name'

    _constraints = [(restrict_dia, u'', ['dia'])]

    _sql_constraints = [
        ('mercados_feiras_unique', 'unique (name)', u'Este mercado/feira já está registado')
    ]


sncp_receita_mercados_feiras()

# ________________________________________________ Ocupação Espaço Público _____________________________


class sncp_receita_oep_finalidades(osv.Model):
    _name = 'sncp.receita.oep.finalidades'
    _description = u"Ocupação Espaço Público"

    def unlink(self, cr, uid, ids, context=None):
        for nid in ids:
            obj = self.browse(cr, uid, nid)

            cr.execute("""
            SELECT id
            FROM sncp_receita_controlo
            WHERE mercado_id = %d
            """ % obj.id)

            res_controlo = cr.fetchall()

            if len(res_controlo) != 0:
                raise osv.except_osv(_(u'Aviso'), _(u'Verifique se a ocupação do espaço público '
                                                    + obj.name
                                                    + u' têm associação em:\n'
                                                    u'1. Receita\Controlo de Receitas Renováveis.'))

        return super(sncp_receita_oep_finalidades, self).unlink(cr, uid, ids, context=context)

    _columns = {
        'name': fields.char(u'Finalidade', size=64),
        'natureza': fields.selection([('perm', u'Permanente'),
                                      ('sazo', u'Sazonal'),
                                      ('ocas', u'Ocasional'), ], u'Natureza'),
        'solo': fields.boolean(u'Ocupação do solo'),
        'subsolo': fields.boolean(u'Ocupação do subsolo'),
        'aereo': fields.boolean(u'Ocupação do espaço aéreo'),
    }

    _order = 'name'

    _sql_constraints = [
        ('oep_unique', 'unique (name)', u'Este Espaço Público já está registado')
    ]


sncp_receita_oep_finalidades()