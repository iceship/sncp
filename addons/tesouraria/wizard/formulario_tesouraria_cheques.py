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
from openerp.tools.translate import _


class formulario_tesouraria_cheques(osv.Model):
    _name = 'formulario.tesouraria.cheques'
    _description = u"Formulário Cheques"

    send = {}

    def menor_sequencia(self, cr, uid, num_ini, num_fim):
        men_seq_ini = ""
        men_seq_fim = ""

        for i in range(len(num_ini)-1, -1, -1):
            if '0' <= num_ini[i] <= '9':
                men_seq_ini += num_ini[i]
            else:
                break

        men_seq_ini = men_seq_ini[::-1]

        for i in range(len(num_fim)-1, -1, -1):
            if '0' <= num_fim[i] <= '9':
                men_seq_fim += num_fim[i]
            else:
                break

        men_seq_fim = men_seq_fim[::-1]

        if len(men_seq_fim) < len(men_seq_ini):
            dif_comp = len(men_seq_ini)-len(men_seq_fim)
            aux_str_ini = men_seq_ini[dif_comp:]
            if int(aux_str_ini) <= int(men_seq_fim):
                return num_ini, dif_comp, aux_str_ini, men_seq_fim
            else:
                raise osv.except_osv(_(u'Aviso'),
                                     _(u'Comparando o mesmo número\nde carateres numéricos\n'
                                       u'da direita para a esquerda, o valor correspondente '
                                       u' do número final têm de ser maior que o valor do número inicial.'))
        elif len(men_seq_fim) > len(men_seq_ini):
            dif_comp = len(men_seq_fim)-len(men_seq_ini)
            aux_str_fim = men_seq_fim[dif_comp:]
            if int(aux_str_fim) <= int(men_seq_ini):
                return num_fim, dif_comp, aux_str_fim, men_seq_ini
            else:
                raise osv.except_osv(_(u'Aviso'),
                                     _(u'Comparando o mesmo número\nde carateres numéricos\n'
                                       u'da direita para a esquerda, o valor correspondente '
                                       u' do número inicial têm de ser maior que o valor do número final.'))
        else:
            if int(men_seq_fim) >= int(men_seq_ini):
                return num_ini, 0, men_seq_ini, men_seq_fim
            else:
                return num_fim, 0, men_seq_fim, men_seq_ini

    def wizard(self, cr, uid, ids, context=None):
        self.send['series_id'] = ids
        return {
            'name': u'<div style="width:500px;">Parâmetros de criação de cheques</div>',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'formulario.tesouraria.cheques',
            'nodestroy': True,
            'target': 'new', }

    def criar_cheques(self, cr, uid, ids, context):
        db_sncp_tesouraria_cheques = self.pool.get('sncp.tesouraria.cheques')
        record = self.browse(cr, uid, ids[0])

        ts = self.menor_sequencia(cr, uid, record.numero_inicial, record.numero_final)

        lim_inf = int(ts[2])
        lim_sup = int(ts[3])
        numero = ""
        for i in range(lim_inf, lim_sup+1):
            if ts[0] == record.numero_inicial:
                if len(unicode(i)) > len(unicode(lim_inf)):
                    if ts[2][ts[1]] == '0':
                        numero = record.numero_inicial[:len(record.numero_inicial)-len(unicode(i))]
                    else:
                        numero = record.numero_inicial[:len(ts[2])-ts[1]]
                    numero += unicode(i)
                else:
                    numero = record.numero_inicial[:len(record.numero_inicial)-len(unicode(i))]
                    numero += unicode(i)

            elif ts[0] == record.numero_final:
                if len(unicode(i)) > len(unicode(lim_inf)):
                    if ts[2][ts[1]] == '0':
                        numero = record.numero_final[:len(record.numero_final)-len(unicode(i))]
                    else:
                        numero = record.numero_final[:len(ts[2])-ts[1]]
                    numero += unicode(i)
                else:
                    numero = record.numero_final[:len(record.numero_final)-len(unicode(i))]
                    numero += unicode(i)

            cheques_id = db_sncp_tesouraria_cheques.search(cr, uid, [('serie_id', '=', self.send['series_id'][0]),
                                                                     ('numero', '=', numero)])

            if len(cheques_id) != 0:
                raise osv.except_osv(_(u'Aviso'),
                                     _(u'A sequência que está a criar contêm elementos que já estão na '
                                       u' lista de cheques.'))

            db_sncp_tesouraria_cheques.create(cr, uid, {'numero': numero, 'serie_id': self.send['series_id'][0], })
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return True

    def numeros_bem_definidos(self, cr, uid, ids):
        record = self.browse(cr, uid, ids[0])

        tam_ini = len(record.numero_inicial)-1
        tam_fim = len(record.numero_final)-1

        x = range(ord('A'), ord('Z')+1)
        maiusculas = map(chr, x)

        x = range(ord('a'), ord('z')+1)
        minusculas = map(chr, x)

        if record.numero_inicial.isalnum() is False:
            raise osv.except_osv(_(u'Aviso'), _(u'O número inicial contêm carateres não alfanuméricos.'))

        if record.numero_final.isalnum() is False:
            raise osv.except_osv(_(u'Aviso'), _(u'O número final contêm carateres não alfanuméricos.'))

        if record.numero_inicial[tam_ini] in maiusculas or record.numero_inicial[tam_ini] in minusculas:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'O carater mais à direita\ndo número inicial têm de ser um número.'))

        if record.numero_final[tam_fim] in maiusculas or record.numero_final[tam_fim] in minusculas:
            raise osv.except_osv(_(u'Aviso'),
                                 _(u'O carater mais à direita\ndo número final têm de ser um número.'))

        self.menor_sequencia(cr, uid, record.numero_inicial, record.numero_final)

        return True

    def descartar(self, cr, uid, ids, context):
        # Apagar formulários
        self.unlink(cr, uid, ids)
        #
        return True

    _columns = {
        'numero_inicial': fields.char(u'Número inicial da sequência de cheques', size=15),
        'numero_final': fields.char(u'Número final da sequência de cheques', size=15),

    }

    _constraints = [(numeros_bem_definidos, u'', ['numero_inicial', 'numero_final'])]

formulario_tesouraria_cheques()