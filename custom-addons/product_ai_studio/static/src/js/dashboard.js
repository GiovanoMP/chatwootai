odoo.define('product_ai_studio.dashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var session = require('web.session');

    var ProductAIStudioDashboard = AbstractAction.extend({
        template: 'ProductAIStudioDashboard',
        events: {
            'click .o_product_ai_studio_dashboard_action': '_onDashboardActionClicked',
            'click .o_product_ai_studio_dashboard_item': '_onDashboardItemClicked',
        },

        /**
         * @override
         */
        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.dashboardData = {};
            this.actionsEnabled = true;
        },

        /**
         * @override
         */
        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return self._fetchDashboardData();
            });
        },

        /**
         * @override
         */
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._renderDashboard();
            });
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Fetch the dashboard data from the server
         *
         * @private
         * @returns {Promise}
         */
        _fetchDashboardData: function () {
            var self = this;
            return rpc.query({
                model: 'product.enrichment',
                method: 'get_dashboard_data',
                args: [],
            }).then(function (result) {
                self.dashboardData = result;
            });
        },

        /**
         * Render the dashboard content
         *
         * @private
         */
        _renderDashboard: function () {
            this.$('.o_product_ai_studio_dashboard_content').html(
                QWeb.render('ProductAIStudioDashboardContent', {
                    widget: this,
                    data: this.dashboardData,
                })
            );
        },

        /**
         * Refresh the dashboard
         *
         * @private
         * @returns {Promise}
         */
        _refreshDashboard: function () {
            var self = this;
            return this._fetchDashboardData().then(function () {
                self._renderDashboard();
            });
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * Handle click on dashboard action buttons
         *
         * @private
         * @param {MouseEvent} ev
         */
        _onDashboardActionClicked: function (ev) {
            ev.preventDefault();
            if (!this.actionsEnabled) {
                return;
            }

            var $target = $(ev.currentTarget);
            var actionName = $target.attr('name');
            var actionParams = $target.data('params') || {};

            if (actionName) {
                this.actionsEnabled = false;
                this.trigger_up('do_action', {
                    action: actionName,
                    options: {
                        additional_context: actionParams,
                        on_close: this._refreshDashboard.bind(this),
                    },
                    on_success: this._enableActions.bind(this),
                    on_fail: this._enableActions.bind(this),
                });
            }
        },

        /**
         * Handle click on dashboard items
         *
         * @private
         * @param {MouseEvent} ev
         */
        _onDashboardItemClicked: function (ev) {
            ev.preventDefault();
            if (!this.actionsEnabled) {
                return;
            }

            var $target = $(ev.currentTarget);
            var actionName = $target.attr('name');
            var actionParams = $target.data('params') || {};

            if (actionName) {
                this.actionsEnabled = false;
                this.trigger_up('do_action', {
                    action: actionName,
                    options: {
                        additional_context: actionParams,
                        on_close: this._refreshDashboard.bind(this),
                    },
                    on_success: this._enableActions.bind(this),
                    on_fail: this._enableActions.bind(this),
                });
            }
        },

        /**
         * Re-enable dashboard actions
         *
         * @private
         */
        _enableActions: function () {
            this.actionsEnabled = true;
        },
    });

    core.action_registry.add('product_ai_studio_dashboard', ProductAIStudioDashboard);

    return ProductAIStudioDashboard;
});
