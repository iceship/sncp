/**
 * Created by jose on 13-11-2014.
 */
openerp.orcamento.acumulados = function (instance) {

    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.orcamento = instance.web.orcamento || {};


    // Remove Button
    instance.web.Sidebar.include({
        init: function () {
            this._super.apply(this, arguments);
            console.log("Parent", this.getParent());
            if (this.getParent().view_type == "form"){
                //console.log("sections", this.sections);
                for (var i = 0; i < this.sections.length; i++) {
                    if (this.sections[i].name == "files") {
                        this.sections.splice(i, 1);
                    }
                }
            }
        }
    });

    instance.web.views.add('tree_orcamento_acumulados_pesquisa', 'instance.web.orcamento.OrcamentoAcumuladosPesquisaListView');
    instance.web.orcamento.OrcamentoAcumuladosPesquisaListView = instance.web.ListView.extend({
        init:function(){
            this._super.apply(this, arguments);
            this.ano_lista = [];
            this.current_ano = null;
            this.current_categoria = null;
            this.organica_lista = [];
            this.current_organica_id = null;
            this.economica_lista = [];
            this.current_economica_id = null;
            this.funcional_lista = [];
            this.current_funcional_id = null;

            },
        start:function(){
            var tmp = this._super.apply(this, arguments);
            var self = this;
            var defs = [];
            this.$el.parent().prepend(QWeb.render("OrcamentoAcumuladosPesquisa", {widget: this}));

            // Carregar as variaveis locais com os valores seleccionados
            this.$el.parent().find('.oe_orcamento_acumulados_select_ano').change(function() {
                self.current_ano = this.value ==='' ? null : parseInt(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_orcamento_acumulados_select_categoria').change(function() {
                self.current_categoria = this.value ==='' ? null : String(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_orcamento_acumulados_select_organica').change(function() {
                self.current_organica_id = this.value ==='' ? null : parseInt(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_orcamento_acumulados_select_economica').change(function() {
                self.current_economica_id = this.value ==='' ? null : parseInt(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });this.$el.parent().find('.oe_orcamento_acumulados_select_funcional').change(function() {
                self.current_funcional_id = this.value ==='' ? null : parseInt(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });

            this.$el.parent().find('.realtxt').change(function() {
                self.searchSel();
                });



            //Tratamento dos atributos
            this.on('edit:after', this, function () {
                self.$el.parent().find('.oe_orcamento_acumulados_select_ano').attr('disabled', 'disabled');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').attr('disabled', 'disabled');
                self.$el.parent().find('.oe_orcamento_acumulados_select_organica').attr('disabled', 'disabled');
                self.$el.parent().find('.oe_orcamento_acumulados_select_economica').attr('disabled', 'disabled');
                self.$el.parent().find('.oe_orcamento_acumulados_select_funcional').attr('disabled', 'disabled');
            });
            this.on('save:after cancel:after', this, function () {
                self.$el.parent().find('.oe_orcamento_acumulados_select_ano').removeAttr('disabled');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').removeAttr('disabled');
                self.$el.parent().find('.oe_orcamento_acumulados_select_organica').removeAttr('disabled');
                self.$el.parent().find('.oe_orcamento_acumulados_select_economica').removeAttr('disabled');
                self.$el.parent().find('.oe_orcamento_acumulados_select_funcional').removeAttr('disabled');
            });


            //Chamada a função Python
            var mod_orcamento_acumulados = new instance.web.Model("sncp.orcamento.acumulados", self.dataset.context, self.dataset.domain);
            defs.push(mod_orcamento_acumulados.call("get_ano_pesquisa_list_js", []).then(function(result) {
                    self.ano_lista = result;
                    console.log("lista anos", self.ano_lista);
            }));
            defs.push(mod_orcamento_acumulados.call("get_dimensao_list_js", ['organica']).then(function(result) {
                    self.organica_lista = result;
            }));
            defs.push(mod_orcamento_acumulados.call("get_dimensao_list_js", ['economica']).then(function(result) {
                    self.economica_lista = result;
            }));
            defs.push(mod_orcamento_acumulados.call("get_dimensao_list_js", ['funcional']).then(function(result) {
                    self.funcional_lista = result;
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
            self.$el.parent().find('.oe_orcamento_acumulados_select_ano').children().remove().end();
            self.$el.parent().find('.oe_orcamento_acumulados_select_ano').append(new Option('', ''));
            for (var i = 0; i < self.ano_lista.length; i++) {
                o = new Option(self.ano_lista[i], self.ano_lista[i]);
                self.$el.parent().find('.oe_orcamento_acumulados_select_ano').append(o);
            }
            self.$el.parent().find('.oe_orcamento_acumulados_select_ano').val(self.current_ano).attr('selected',true);


            // Bloco de construção da lista das categorias
            self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').children().remove().end();
            self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(new Option('', ''));
            o1 = new Option('Dotação Inicial','01ddota');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o1);
            o2 = new Option('Reforço (D)','02drefo');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o2);
            o3 = new Option('Abate (D)','03dabat');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o3);
            o4 = new Option('Cabimento','04cabim');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o4);
            o5 = new Option('Compromisso','05compr');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o5);
            o6 = new Option('Compromisso Futuro','06futur');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o6);
            o7 = new Option('Fatura de Compras','07dfact');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o7);
            o8 = new Option('Liquidação (D)','08dliqd');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o8);
            o9 = new Option('Pagamento','09pagam');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o9);
            o10 = new Option('Reposição Abatida a Pagamento','10repos');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o10);
            o11 = new Option('Previsão Inicial','51rdota');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o11);
            o12 = new Option('Reforço (R)','52rrefo');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o12);
            o13 = new Option('Abate (R)','53rabat');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o13);
            o14 = new Option('Receita p/cobrar Início do Ano','54rinia');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o14);
            o15 = new Option('Fatura de Vendas','55rfact');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o15);
            o16 = new Option('Nota de Crédito de Vendas','56rncrd');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o16);
            o17 = new Option('Liquidação (R)','57rliqd');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o17);
            o18 = new Option('58cobra','Cobrança');
                self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').append(o17);
            self.$el.parent().find('.oe_orcamento_acumulados_select_categoria').val(self.current_categoria).attr('selected',true);


            // Bloco de construção da lista dos dimensoes
            self.$el.parent().find('.oe_orcamento_acumulados_select_organica').children().remove().end();
            self.$el.parent().find('.oe_orcamento_acumulados_select_organica').append(new Option('', ''));
            for (var i = 0; i < self.organica_lista.length; i++) {
                o = new Option(self.organica_lista[i][1], self.organica_lista[i][0]);
                self.$el.parent().find('.oe_orcamento_acumulados_select_organica').append(o);
            }
            self.$el.parent().find('.oe_orcamento_acumulados_select_organica').val(self.current_organica_id).attr('selected',true);

            self.$el.parent().find('.oe_orcamento_acumulados_select_economica').children().remove().end();
            self.$el.parent().find('.oe_orcamento_acumulados_select_economica').append(new Option('', ''));
            for (var i = 0; i < self.economica_lista.length; i++) {
                o = new Option(self.economica_lista[i][1], self.economica_lista[i][0]);
                self.$el.parent().find('.oe_orcamento_acumulados_select_economica').append(o);
            }
            self.$el.parent().find('.oe_orcamento_acumulados_select_economica').val(self.current_economica_id).attr('selected',true);

            self.$el.parent().find('.oe_orcamento_acumulados_select_funcional').children().remove().end();
            self.$el.parent().find('.oe_orcamento_acumulados_select_funcional').append(new Option('', ''));
            for (var i = 0; i < self.funcional_lista.length; i++) {
                o = new Option(self.funcional_lista[i][1], self.funcional_lista[i][0]);
                self.$el.parent().find('.oe_orcamento_acumulados_select_funcional').append(o);
            }
            self.$el.parent().find('.oe_orcamento_acumulados_select_funcional').val(self.current_funcional_id).attr('selected',true);

            return self.search();
        },
        search: function(){
            var self = this;
            var domain = [];
            var defs = [];

            // Atribuição de valor ao domain
            if (self.current_ano !== null) domain.push(["name","=", self.current_ano]);
            if (self.current_categoria !== null) domain.push(["categoria","=", self.current_categoria]);
            if (self.current_organica_id !== null) domain.push(["organica_id","=", self.current_organica_id]);
            if (self.current_economica_id !== null) domain.push(["economica_id","=", self.current_economica_id]);
            if (self.current_funcional_id !== null) domain.push(["funcional_id","=", self.current_funcional_id]);


            self.last_context["name"] = self.current_ano === null ? false : self.current_ano;
            if (self.current_categoria === null) delete self.last_context["categoria"];
            else self.last_context["categoria"] =  self.current_categoria;
            if (self.current_organica_id === null) delete self.last_context["organica_id"];
            else self.last_context["organica_id"] =  self.current_organica_id;
            if (self.current_economica_id === null) delete self.last_context["economica_id"];
            else self.last_context["economica_id"] =  self.current_economica_id;
            if (self.current_funcional_id === null) delete self.last_context["funcional_id"];
            else self.last_context["funcional_id"] =  self.current_funcional_id;
            delete self.last_context["id"];
            self.last_context["id"] =  self.id_lista;

            var compound_domain = new instance.web.CompoundDomain(self.last_domain, domain);
            self.dataset.domain = compound_domain.eval();
            return self.old_search(compound_domain, self.last_context, self.last_group_by);
        },
        searchSel: function() {

            var input = document.getElementById('realtxt').value.toLowerCase();
            var output = document.getElementById('oe_orcamento_acumulados_select_economica').options;
            for(var i  =0; i <output.length;i++) {
                if(output[i].text.indexOf(input)!=-1){
                    output[i].selected=true;
                    output[i].hidden = false
                }else{
                    output[i].hidden = true
                }
                if(document.getElementById('realtxt').value==''){
                    output[0].selected=true;
                }
            }
        }
    });



};