# pylint: disable=C0114
# -*- coding: utf-8 -*-pack
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    # App information
    'name': 'Amazon Odoo Connector',
    'version': '14.0.2.30',
    'category': 'Sales',
    'license': 'OPL-1',
    'summary': 'Amazon Odoo Connector helps you integrate & manage your Amazon Seller Account '
               'operations from Odoo. '
               'Save time, efforts and avoid errors due to manual data entry to boost your Amazon '
               'sales with this '
               'connector.',
    'description': """
       Ticket 2894
    """,
    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com/',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',
    # Dependencies
    'depends': ['iap', 'common_connector_library', 'rating'],
    # Views
    'data': [
        'data/ir_cron.xml',
        'data/ir_sequence.xml',
        'security/res_groups.xml',
        'view/vat_config_ept.xml',
        'view/res_config_view.xml',
        'view/amazon_seller.xml',
        'view/product_view.xml',
        'wizard_views/shipment_report_configure_fulfillment_center_ept.xml',
        'view/shipping_report.xml',
        'wizard_views/amazon_outbound_order_wizard_view.xml',
        'view/sale_view.xml',
        'wizard_views/amazon_process_import_export.xml',
        'view/invoice_view.xml',
        'view/instance_view.xml',
        'view/fbm_sale_order_report_ept.xml',
        'view/stock_warehouse.xml',
        'view/delivery.xml',

        'view/product_ul.xml',

        'wizard_views/amazon_product_mapping.xml',
        'wizard_views/export_product_wizard_view.xml',
        'wizard_views/import_product_removal_order_wizard.xml',
        'wizard_views/queue_process_wizard_view.xml',

        'wizard_views/import_product_inbound_shipment.xml',
        'wizard_views/import_inbound_shipment_report_wizard.xml',
        'wizard_views/inbound_shipment_labels_wizard.xml',

        'wizard_views/fbm_cron_configuration.xml',
        'wizard_views/fba_cron_configuration.xml',
        'wizard_views/global_cron_configuration.xml',

        'data/import_product_attachment.xml',
        'data/res_partner_data.xml',
        'view/stock_adjustment_view.xml',
        'view/amazon_stock_adjustment_config.xml',
        'view/amazon_stock_adjustment_group.xml',
        'view/adjustment_reason.xml',
        'view/stock_view.xml',
        'view/stock_move_view.xml',
        'view/removal_order_config.xml',
        'view/stock_location_route.xml',
        'view/sale_order_return_report.xml',
        'wizard_views/settlement_report_configure_fees_ept.xml',
        'view/settlement_report.xml',
        'view/removal_order_view.xml',
        'view/amazon_removal_order_report.xml',
        'view/sale_order_return_report.xml',
        'view/amazon_fba_live_stock_report_view.xml',
        'view/stock_inventory.xml',
        'view/fulfillment_center_config_view.xml',
        'view/account_bank_statement.xml',

        # inbound view
        'view/inbound_shipment_plan.xml',
        'view/inbound_shipment_ept.xml',
        'view/shipment_picking.xml',
        'wizard_views/inbound_shipment_details_wizard.xml',

        # 'view/stock_picking_view.xml',
        # data
        'data/amazon.developer.details.ept.csv',
        'view/cancel_order_wizard_view.xml',
        'view/active_product_listing.xml',
        'view/rating_report_view.xml',
        'view/rating_view.xml',
        'view/vcs_tax_report.xml',
        'view/res_country_view.xml',
        'view/account_fiscal_position.xml',
        'view/common_log_book_view.xml',
        'view/feed_submission_history.xml',
        'view/shipped_order_data_queue_view.xml',
        'view/sale_report.xml',
        'data/product_data.xml',
        'data/import_removal_order_attachment.xml',
        'data/ca_code.xml',
        'data/de_code.xml',
        'data/es_code.xml',
        'data/fr_code.xml',
        'data/it_code.xml',
        'data/pl_code.xml',
        'data/uk_code.xml',
        'data/us_code.xml',
        'data/mx_code.xml',
        'data/email_template.xml',
        'data/amazon.adjustment.reason.group.csv',
        'data/amazon.adjustment.reason.code.csv',
        'data/email_template.xml',
        'data/amazon_transaction_type.xml',
        'data/amazon_return_reason_data.xml',
        'data/res_country_group.xml',
        'data/amazon_upgrade_data.xml',

        # cron
        # security
        'security/ir.model.access.csv',
        # 'report/invoice_paperformat.xml',
        # 'report/invoice_report.xml'
        'view/assets.xml',
    ],

    # cloc settings
    'cloc_exclude': [
        "**/*.xml",
        "wizard/**/*",
    ],

    # Odoo Store Specific
    'images': ['static/description/cover.png'],
    'qweb': ['static/src/xml/dashboard_widget_inherit.xml'],

    # Technical
    'installable': True,
    'auto_install': False,
    'live_test_url': 'https://www.emiprotechnologies.com/free-trial?app=amazon-ept&version=14'
                     '&edition=enterprise',
    'application': True,
    'price': 479.00,
    'currency': 'EUR',
}
