/* Declarações a fazer

*/
openerp.despesa.autorizacoes_pesquisa = function (instance) {

    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.despesa = instance.web.despesa || {};



    instance.web.views.add('tree_autorizacoes_pesquisa', 'instance.web.despesa.AutorizacoesPesquisaListView');
    instance.web.despesa.AutorizacoesPesquisaListView = instance.web.ListView.extend({
        init:function(){
            this._super.apply(this, arguments);
            this.current_tipo_documento = null;
            this.user_lista = [];
            this.current_user_id = null;

            this.data_from = '';
            this.data_to = '';
        },
        start:function(){
            var tmp = this._super.apply(this, arguments);
            var self = this;
            var defs = [];
            this.$el.parent().prepend(QWeb.render("AutorizacoesPesquisa", {widget: this}));

            // Carregar as variaveis locais com os valores seleccionados

            this.$el.parent().find('.oe_despesa_select_tipo_documento').change(function() {
                self.current_tipo_documento = this.value ==='' ? null : String(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_despesa_select_user').change(function() {
                self.current_user_id = this.value ==='' ? null : parseInt(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });

            this.$el.parent().find('.oe_despesa_autorizacao_data_from').change(function() {
                self.data_from = this.value ==='' ? null : String(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_despesa_autorizacao_data_to').change(function() {
                self.data_to = this.value ==='' ? null : String(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });



            //Tratamento dos atributos
            this.on('edit:after', this, function () {
                self.$el.parent().find('.oe_despesa_select_tipo_documento').attr('disabled', 'disabled');
                self.$el.parent().find('.oe_despesa_select_user').attr('disabled', 'disabled');
                });
            this.on('save:after cancel:after', this, function () {
                self.$el.parent().find('.oe_despesa_select_tipo_documento').removeAttr('disabled');
                self.$el.parent().find('.oe_despesa_select_user').removeAttr('disabled');
                });


            //Chamada a função Python
            var mod_autorizacoes = new instance.web.Model("sncp.despesa.autorizacoes", self.dataset.context, self.dataset.domain);
            defs.push(mod_autorizacoes.call("get_user_list_js", []).then(function(result) {
                    self.user_lista = result;
            }));

            return $.when(tmp, defs);
        },
        do_search: function(domain, context, group_by) {
            var self = this;
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);
            var defs = [];
            var o;

            // Bloco de construção da lista dos tipos de documentos
            self.$el.parent().find('.oe_despesa_select_tipo_documento').children().remove().end();
            self.$el.parent().find('.oe_despesa_select_tipo_documento').append(new Option('', ''));

            o1 = new Option("Requisição Interna", "reqi");
                self.$el.parent().find('.oe_despesa_select_tipo_documento').append(o1);
            o2 = new Option("Cabimento", "cabi");
                self.$el.parent().find('.oe_despesa_select_tipo_documento').append(o2);
            o3 = new Option("Compromisso", "comp");
                self.$el.parent().find('.oe_despesa_select_tipo_documento').append(o3);
            o4 = new Option("Ordem de Compra", "ocmp");
                self.$el.parent().find('.oe_despesa_select_tipo_documento').append(o4);
            o5 = new Option("Fatura de Compra", "fact");
                self.$el.parent().find('.oe_despesa_select_tipo_documento').append(o5);
            o6 = new Option("Proposta de Pagamento", "ppag");
                self.$el.parent().find('.oe_despesa_select_tipo_documento').append(o6);
            o7 = new Option("Ordem de Pagamento", "opag");
                self.$el.parent().find('.oe_despesa_select_tipo_documento').append(o7);

            self.$el.parent().find('.oe_despesa_select_tipo_documento').val(self.current_tipo_documento).attr('selected',true);


            // Bloco de construção da lista dos utilizadores
            self.$el.parent().find('.oe_despesa_select_user').children().remove().end();
            self.$el.parent().find('.oe_despesa_select_user').append(new Option('', ''));
            for (var i = 0; i < self.user_lista.length; i++) {
                o = new Option(self.user_lista[i][1], self.user_lista[i][0]);
                self.$el.parent().find('.oe_despesa_select_user').append(o);
            }
            self.$el.parent().find('.oe_despesa_select_user').val(self.current_user_id).attr('selected',true);


            // Bloco das datas
            self.$el.parent().find('.oe_despesa_autorizacao_date_from').change(function() {
                self.data_from = this.value === '' ? null : this.value;
                self.search();
              });

            if (self.data_from === '') self.data_from = null;
            self.$el.parent().find('.oe_despesa_autorizacao_date_to').change(function() {
                self.data_to = this.value === '' ? null : this.value;
                self.search();
              });
            if (self.data_to === '') self.data_to = null;

            return self.search();
        },
        search: function(){
            var self = this;
            var domain = [];
            var defs = [];

            // Atribuição de valor ao domain
            if (self.current_tipo_documento !== null) domain.push(["tipo_doc","=", self.current_tipo_documento]);
            if (self.current_user_id !== null) domain.push(["user_id","=", self.current_user_id]);
            if (self.data_from !== null) domain.push(["datahora",">", self.data_from]);
            if (self.data_to !== null) domain.push(["datahora","<", self.data_to]);


            if (self.current_tipo_documento === null) delete self.last_context["tipo_doc"];
            else self.last_context["tipo_doc"] =  self.current_tipo_documento;
            if (self.current_user_id === null) delete self.last_context["user_id"];
            else self.last_context["user_id"] =  self.current_user_id;
            if (self.data_from === null) delete self.last_context["datahora"];
            else self.last_context["datahora"] =  self.data_from;
            delete self.last_context["id"];
            self.last_context["id"] =  self.id_lista;

            var compound_domain = new instance.web.CompoundDomain(self.last_domain, domain);
            self.dataset.domain = compound_domain.eval();
            return self.old_search(compound_domain, self.last_context, self.last_group_by);
        },
    });
};
