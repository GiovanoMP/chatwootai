odoo.define('product_ai_studio.preview_editor', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var Dialog = require('web.Dialog');

    var PreviewEditor = Widget.extend({
        template: 'ProductAIStudioPreviewEditor',
        events: {
            'input .o_preview_editor_content': '_onContentChange',
            'click .o_preview_editor_apply': '_onApplyClicked',
            'click .o_preview_editor_refresh': '_onRefreshClicked',
            'click .o_preview_editor_marketplace_tab': '_onMarketplaceTabClicked',
        },

        /**
         * @override
         */
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.options = options || {};
            this.recordId = options.recordId;
            this.model = options.model || 'product.enrichment';
            this.previewData = {};
            this.activeMarketplace = null;
            this.marketplaces = [];
            this.isEditing = false;
        },

        /**
         * @override
         */
        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return self._fetchPreviewData();
            });
        },

        /**
         * @override
         */
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._renderPreview();
                if (self.marketplaces.length > 0) {
                    self.activeMarketplace = self.marketplaces[0].id;
                    self._updateActiveTab();
                }
            });
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Fetch the preview data from the server
         *
         * @private
         * @returns {Promise}
         */
        _fetchPreviewData: function () {
            var self = this;
            return rpc.query({
                model: this.model,
                method: 'get_preview_data',
                args: [this.recordId],
            }).then(function (result) {
                self.previewData = result.preview_data || {};
                self.marketplaces = result.marketplaces || [];
            });
        },

        /**
         * Render the preview content
         *
         * @private
         */
        _renderPreview: function () {
            this.$('.o_preview_editor_preview_container').html(
                QWeb.render('ProductAIStudioPreviewContent', {
                    widget: this,
                    data: this.previewData,
                    activeMarketplace: this.activeMarketplace,
                    marketplaces: this.marketplaces,
                })
            );
        },

        /**
         * Update the active marketplace tab
         *
         * @private
         */
        _updateActiveTab: function () {
            this.$('.o_preview_editor_marketplace_tab').removeClass('active');
            this.$('.o_preview_editor_marketplace_tab[data-marketplace-id="' + this.activeMarketplace + '"]').addClass('active');
            this._renderPreview();
        },

        /**
         * Save the edited content
         *
         * @private
         * @returns {Promise}
         */
        _saveContent: function () {
            var self = this;
            var content = this.$('.o_preview_editor_content').val();
            
            return rpc.query({
                model: this.model,
                method: 'save_preview_content',
                args: [this.recordId, content, this.activeMarketplace],
            }).then(function (result) {
                if (result.success) {
                    self.previewData = result.preview_data || self.previewData;
                    self._renderPreview();
                    self.isEditing = false;
                    return true;
                } else {
                    Dialog.alert(self, {
                        title: _t("Error"),
                        message: result.error || _t("An error occurred while saving the content."),
                    });
                    return false;
                }
            });
        },

        /**
         * Refresh the preview from the server
         *
         * @private
         * @returns {Promise}
         */
        _refreshPreview: function () {
            var self = this;
            return this._fetchPreviewData().then(function () {
                self._renderPreview();
                return true;
            });
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * Handle content changes
         *
         * @private
         */
        _onContentChange: function () {
            this.isEditing = true;
        },

        /**
         * Handle apply button click
         *
         * @private
         * @param {MouseEvent} ev
         */
        _onApplyClicked: function (ev) {
            ev.preventDefault();
            if (this.isEditing) {
                this._saveContent();
            }
        },

        /**
         * Handle refresh button click
         *
         * @private
         * @param {MouseEvent} ev
         */
        _onRefreshClicked: function (ev) {
            ev.preventDefault();
            if (this.isEditing) {
                Dialog.confirm(this, _t("You have unsaved changes. Do you want to discard them?"), {
                    confirm_callback: this._refreshPreview.bind(this),
                });
            } else {
                this._refreshPreview();
            }
        },

        /**
         * Handle marketplace tab click
         *
         * @private
         * @param {MouseEvent} ev
         */
        _onMarketplaceTabClicked: function (ev) {
            ev.preventDefault();
            var $target = $(ev.currentTarget);
            var marketplaceId = $target.data('marketplace-id');
            
            if (this.isEditing) {
                var self = this;
                Dialog.confirm(this, _t("You have unsaved changes. Do you want to save them before switching?"), {
                    confirm_callback: function () {
                        self._saveContent().then(function (success) {
                            if (success) {
                                self.activeMarketplace = marketplaceId;
                                self._updateActiveTab();
                            }
                        });
                    },
                    cancel_callback: function () {
                        self.isEditing = false;
                        self.activeMarketplace = marketplaceId;
                        self._updateActiveTab();
                    },
                });
            } else {
                this.activeMarketplace = marketplaceId;
                this._updateActiveTab();
            }
        },
    });

    return PreviewEditor;
});
