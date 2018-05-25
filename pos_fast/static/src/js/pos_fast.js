odoo.define('pos_fast', function (require) {
    var models = require('point_of_sale.models');
    var Model = require('web.DataModel');
    var core = require('web.core');
    var _t = core._t;
    var screens = require('point_of_sale.screens');
    var db = require('point_of_sale.DB');

    db.include({
        is_product_in_category: function (category_ids, product_id) {
            try {
                return this._super(options);
            } catch (ex) {
                return false
            }
        }
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        load_server_data: function () {
            var self = this;
            self.model_blocked_loading = [
                'product.product',
                'res.partner'
            ];
            for (var i in self.model_blocked_loading) {
                if (self.model_blocked_loading[i] == 'res.partner') {
                    var partner_index = _.findIndex(self.models, function (model) {
                        return model.model == self.model_blocked_loading[i];
                    });
                    self.partner_model = this.models[partner_index];
                    if (partner_index !== -1) {
                        self.models.splice(partner_index, 1);
                    }
                } else {
                    var model_index = _.findIndex(self.models, function (model) {
                        return model.model == self.model_blocked_loading[i];
                    });
                    if (model_index !== -1) {
                        self.models.splice(model_index, 1);
                    }
                }
            }
            return _super_posmodel.load_server_data.apply(this, arguments).then(function () {
                self.chrome.loading_message(_t('Please waiting some minutes for loading cache datas'), 0);
                return new Model('pos.auto.cache').call('get_data', []).then(function (json_data) {
                    var products_json = json_data['product.product'];
                    var partners_json = json_data['res.partner'];
                    self.db.add_products(products_json);
                    self.partners = partners_json;
                    self.db.add_partners(partners_json);
                    self.models.push(self.partner_model);
                });
            })
        },
    });
});
