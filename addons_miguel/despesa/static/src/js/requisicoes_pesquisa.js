/* Declarações a fazer

*/
openerp.despesa.requisicoes_pesquisa = function (instance) {

    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.despesa = instance.web.despesa || {};



    instance.web.views.add('tree_requisicoes_pesquisa', 'instance.web.despesa.RequisicoesPesquisaListView');
    instance.web.despesa.RequisicoesPesquisaListView = instance.web.ListView.extend({
        init:function(){
            this._super.apply(this, arguments);
            this.requisicao_lista = [];
            this.current_requisicao_id = null;
            this.current_accao = null;
            this.user_lista = [];
            this.current_user_id = null;

            this.data_from = '';
            this.data_to = '';
        },
        start:function(){
            var tmp = this._super.apply(this, arguments);
            var self = this;
            var defs = [];
            this.$el.parent().prepend(QWeb.render("RequisicoesPesquisa", {widget: this}));

            // Carregar as variaveis locais com os valores seleccionados
            this.$el.parent().find('.oe_despesa_select_requisicao').change(function() {
                self.current_requisicao_id = this.value ==='' ? null : parseInt(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_despesa_select_accao').change(function() {
                self.current_accao = this.value ==='' ? null : String(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_despesa_select_user').change(function() {
                self.current_user_id = this.value ==='' ? null : parseInt(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });

            this.$el.parent().find('.oe_despesa_select_data_from').change(function() {
                self.data_from = this.value ==='' ? null : String(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_despesa_select_data_to').change(function() {
                self.data_to = this.value ==='' ? null : String(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });



            //Tratamento dos atributos
            this.on('edit:after', this, function () {
                self.$el.parent().find('.oe_despesa_select_requisicao').attr('disabled', 'disabled');
                self.$el.parent().find('.oe_despesa_select_accao').attr('disabled', 'disabled');
                self.$el.parent().find('.oe_despesa_select_user').attr('disabled', 'disabled');
                });
            this.on('save:after cancel:after', this, function () {
                self.$el.parent().find('.oe_despesa_select_requisicao').removeAttr('disabled');
                self.$el.parent().find('.oe_despesa_select_accao').removeAttr('disabled');
                self.$el.parent().find('.oe_despesa_select_user').removeAttr('disabled');
                });


            //Chamada a função Python
            var mod_requisicoes = new instance.web.Model("sncp.despesa.requisicoes", self.dataset.context, self.dataset.domain);
            defs.push(mod_requisicoes.call("get_requisicao_pesquisa_list_js", []).then(function(result) {
                    self.requisicao_lista = result;
            }));
            var mod_user = new instance.web.Model("sncp.despesa.requisicoes", self.dataset.context, self.dataset.domain);
            defs.push(mod_user.call("get_user_list_js", []).then(function(result) {
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

            // Bloco de construção da lista das requisiçções
            self.$el.parent().find('.oe_despesa_select_requisicao').children().remove().end();
            self.$el.parent().find('.oe_despesa_select_requisicao').append(new Option('', ''));
            for (var i = 0; i < self.requisicao_lista.length; i++) {
                o = new Option(self.requisicao_lista[i][1], self.requisicao_lista[i][0]);
                self.$el.parent().find('.oe_despesa_select_requisicao').append(o);
            }
            self.$el.parent().find('.oe_despesa_select_requisicao').val(self.current_requisicao_id).attr('selected',true);


            // Bloco de construção da lista das acçõs
            self.$el.parent().find('.oe_despesa_select_accao').children().remove().end();
            self.$el.parent().find('.oe_despesa_select_accao').append(new Option('', ''));

            o1 = new Option("Abertura", "draft");
                self.$el.parent().find('.oe_despesa_select_accao').append(o1);
            o2 = new Option("Remetida", "remetd");
                self.$el.parent().find('.oe_despesa_select_accao').append(o2);
            o3 = new Option("Aprovada", "aprovd");
                self.$el.parent().find('.oe_despesa_select_accao').append(o3);
            o4 = new Option("Rejeitada", "rejeit");
                self.$el.parent().find('.oe_despesa_select_accao').append(o4);
            o5 = new Option("Recuperada", "recupe");
                self.$el.parent().find('.oe_despesa_select_accao').append(o5);
            o6 = new Option("Completa", "complt");
                self.$el.parent().find('.oe_despesa_select_accao').append(o6);

            self.$el.parent().find('.oe_despesa_select_accao').val(self.current_accao).attr('selected',true);


            // Bloco de construção da lista dos utilizadores
            self.$el.parent().find('.oe_despesa_select_user').children().remove().end();
            self.$el.parent().find('.oe_despesa_select_user').append(new Option('', ''));
            for (var i = 0; i < self.user_lista.length; i++) {
                o = new Option(self.user_lista[i][1], self.user_lista[i][0]);
                self.$el.parent().find('.oe_despesa_select_user').append(o);
            }
            self.$el.parent().find('.oe_despesa_select_user').val(self.current_user_id).attr('selected',true);


            // Bloco das datas
            self.$el.parent().find('.oe_despesa_input_date_from').change(function() {
                self.data_from = this.value === '' ? null : this.value;
                self.search();
              });

            if (self.data_from === '') self.data_from = null;
            self.$el.parent().find('.oe_despesa_input_date_to').change(function() {
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
            if (self.current_requisicao_id !== null) domain.push(["req_id","=", self.current_requisicao_id]);
            if (self.current_accao !== null) domain.push(["accao","=", self.current_accao]);
            if (self.current_user_id !== null) domain.push(["user_id","=", self.current_user_id]);
            if (self.data_from !== null) domain.push(["name",">", self.data_from]);
            if (self.data_to !== null) domain.push(["name","<", self.data_to]);


            self.last_context["req_id"] = self.current_requisicao_id === null ? false : self.current_requisicao_id;
            if (self.current_accao === null) delete self.last_context["accao"];
            else self.last_context["accao"] =  self.current_accao;
            if (self.current_user_id === null) delete self.last_context["user_id"];
            else self.last_context["user_id"] =  self.current_user_id;
            if (self.data_from === null) delete self.last_context["name"];
            else self.last_context["name"] =  self.data_from;
            delete self.last_context["id"];
            self.last_context["id"] =  self.id_lista;

            var compound_domain = new instance.web.CompoundDomain(self.last_domain, domain);
            self.dataset.domain = compound_domain.eval();
            return self.old_search(compound_domain, self.last_context, self.last_group_by);
        },
    });
};
