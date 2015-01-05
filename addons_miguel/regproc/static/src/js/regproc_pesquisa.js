/* Declarações a fazer

*/
openerp.regproc = function (instance) {
    openerp.regproc.filter_manager(instance);
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.regproc = instance.web.regproc || {};


    // Remove Attachments
    instance.web.Sidebar.include({
        init: function () {
            this._super.apply(this, arguments);
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

    instance.web.views.add('tree_pesquisa', 'instance.web.regproc.PesquisaListView');
    instance.web.regproc.PesquisaListView = instance.web.ListView.extend({
        init:function(){
            this._super.apply(this, arguments);
            this.objecto_lista = [];
            this.current_objecto_id = null;
            this.aquis_alien_lista = [];
            this.current_aquis_alien_id = null;
            this.id_lista = [];
            this.current_input_desc = '';
            this.outrg_lista = [];
            this.current_outrg_id = null;
            this.data_from = '';
            this.data_to = '';

        },
        start:function(){
            var tmp = this._super.apply(this, arguments);
            var self = this;
            var defs = [];
            this.$el.parent().prepend(QWeb.render("Pesquisa", {widget: this}));

            // Carregar as variaveis locais com os valores seleccionados
            this.$el.parent().find('.oe_regproc_select_objecto').change(function() {
                self.current_objecto_id = this.value ==='' ? null : parseInt(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_regproc_select_aquis_alien').change(function() {
                self.current_aquis_alien_id = this.value ==='' ? null : parseInt(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_regproc_select_outrg').change(function() {
                self.current_outrg_id = this.value ==='' ? null : String(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_regproc_input_desc').change(function() {
                self.current_input_desc = this.value ==='' ? null : this.value;
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });


            this.$el.parent().find('.oe_regproc_input_date_from').change(function() {
                self.data_from = this.value ==='' ? null : String(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_regproc_input_date_to').change(function() {
                self.data_to = this.value ==='' ? null : String(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });


            //Tratamento dos atributos
            this.on('edit:after', this, function () {
                self.$el.parent().find('.oe_regproc_select_objecto').attr('disabled', 'disabled');
                self.$el.parent().find('.oe_regproc_select_aquis_alien').attr('disabled', 'disabled');
                self.$el.parent().find('.oe_regproc_select_outrg').attr('disabled', 'disabled');
            });
            this.on('save:after cancel:after', this, function () {
                self.$el.parent().find('.oe_regproc_select_objecto').removeAttr('disabled');
                self.$el.parent().find('.oe_regproc_select_aquis_alien').removeAttr('disabled');
                self.$el.parent().find('.oe_regproc_select_outrg').removeAttr('disabled');
            });

            //Chamada a função Python
            var mod_notario = new instance.web.Model("sncp.regproc.notario.objecto", self.dataset.context, self.dataset.domain);
            defs.push(mod_notario.call("get_objecto_list_js", []).then(function(result) {
                    self.objecto_lista = result;
            }));
            var mod_aquis_alien = new instance.web.Model("sncp.regproc.aquis.alien", self.dataset.context, self.dataset.domain);
            defs.push(mod_aquis_alien.call("get_aquis_alien_list_js", []).then(function(result) {
                    self.aquis_alien_lista = result;
            }));
            var mod_outrg = new instance.web.Model("sncp.regproc.notario.actos.outrg", self.dataset.context, self.dataset.domain);
            defs.push(mod_outrg.call("get_outrg_list_js", []).then(function(result) {
                    self.outrg_lista = result;
                console.log("result ", result);
            }));
            var mod_notario_actos = new instance.web.Model("sncp.regproc.notario.actos", self.dataset.context, self.dataset.domain);
            defs.push(mod_notario_actos.call("get_id_list_js", [self.current_input_desc]).then(function(result) {
                    self.id_lista = result;
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

            // Bloco de construção da lista dos objetos
            self.$el.parent().find('.oe_regproc_select_objecto').children().remove().end();
            self.$el.parent().find('.oe_regproc_select_objecto').append(new Option('', ''));
            for (var i = 0; i < self.objecto_lista.length; i++) {
                o = new Option(self.objecto_lista[i][1], self.objecto_lista[i][0]);
                self.$el.parent().find('.oe_regproc_select_objecto').append(o);
            }
            self.$el.parent().find('.oe_regproc_select_objecto').val(self.current_objecto_id).attr('selected',true);

            // Bloco de construção da lista de Aquisições/Alienações
            self.$el.parent().find('.oe_regproc_select_aquis_alien').children().remove().end();
            self.$el.parent().find('.oe_regproc_select_aquis_alien').append(new Option('', ''));
            for (var i = 0; i < self.aquis_alien_lista.length; i++) {
                o = new Option(self.aquis_alien_lista[i][1], self.aquis_alien_lista[i][0]);
                self.$el.parent().find('.oe_regproc_select_aquis_alien').append(o);
            }
            self.$el.parent().find('.oe_regproc_select_aquis_alien').val(self.current_aquis_alien_id).attr('selected',true);

            // Bloco de construção da lista dos Outorgantes
            self.$el.parent().find('.oe_regproc_select_outrg').children().remove().end();
            self.$el.parent().find('.oe_regproc_select_outrg').append(new Option('', ''));
            for (var i = 0; i < self.outrg_lista.length; i++) {
                o = new Option(self.outrg_lista[i][2], [self.outrg_lista[i][0], self.outrg_lista[i][1]]);
                self.$el.parent().find('.oe_regproc_select_outrg').append(o);
                console.log("options", o);
            }

            self.$el.parent().find('.oe_regproc_select_outrg').val(self.current_outrg_id).attr('selected',true);


            // Bloco de pesquisa por texto
            this.$el.parent().find('.oe_regproc_input_desc').change(function() {
                self.current_input_desc = this.value === null ? '' : this.value;
              });
            if (self.current_input_desc === null) self.current_input_desc ='';

            var mod_notario_actos = new instance.web.Model("sncp.regproc.notario.actos", self.dataset.context, self.dataset.domain);
            defs.push(mod_notario_actos.call("get_id_list_js", [self.current_input_desc]).then(function(result) {
                self.id_lista = result;
                self.search();
               }));

            // Bloco das datas
            self.$el.parent().find('.oe_regproc_input_date_from').change(function() {
                self.data_from = this.value === '' ? null : this.value;
                self.search();
              });

            if (self.data_from === '') self.data_from = null;
            self.$el.parent().find('.oe_regproc_input_date_to').change(function() {
                self.data_to = this.value === '' ? null : this.value;
                console.log("1");
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
            if (self.current_objecto_id !== null) domain.push(["objecto_id","=", self.current_objecto_id]);
            if (self.current_aquis_alien_id !== null) domain.push(["aquis_alien_ids","=", self.current_aquis_alien_id]);
            if (self.current_outrg_id !== null) {
                var mod_outrg = new instance.web.Model("sncp.regproc.notario.actos.outrg", self.dataset.context, self.dataset.domain);
                defs.push(mod_outrg.call("get_acto_list_js", [self.current_outrg_id]).then(function(result) {
                        domain.push(["id","in", result]);
                }));


            }
            if (self.current_input_desc !== null) domain.push(["id","in", self.id_lista]);
            if (self.data_from !== null) domain.push(["datahora",">", self.data_from]);
            if (self.data_to !== null) domain.push(["datahora","<", self.data_to]);


            self.last_context["objecto_id"] = self.current_objecto_id === null ? false : self.current_objecto_id;
            if (self.current_aquis_alien_id === null) delete self.last_context["aquis_alien_ids"];
            else self.last_context["aquis_alien_ids"] =  self.current_aquis_alien_id;
            if (self.current_outrg_id === null) delete self.last_context["outrg_ids"];
            else self.last_context["outrg_ids"] =  self.current_outrg_id;
            if (self.data_from === null) delete self.last_context["datahora"];
            else self.last_context["datahora"] =  self.data_from;
            delete self.last_context["id"];
            self.last_context["id"] =  self.id_lista;

            var compound_domain = new instance.web.CompoundDomain(self.last_domain, domain);
            self.dataset.domain = compound_domain.eval();
            return self.old_search(compound_domain, self.last_context, self.last_group_by);
        }
    });
};