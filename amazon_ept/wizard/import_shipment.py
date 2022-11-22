# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
"""
Added class  and methods to request for inbound shipment and process inbound shipment response.
"""

from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.addons.iap.tools import iap_tools
from ..endpoint import DEFAULT_ENDPOINT


class AmazonInboundImportShipmentWizard(models.TransientModel):
    """
    Added to import inbound shipment.
    """
    _name = "amazon.inbound.import.shipment.ept"
    _description = 'amazon.inbound.import.shipment.ept'

    shipment_id = fields.Char(required=True)
    instance_id = fields.Many2one('amazon.instance.ept', string='Instance', required=True)
    from_warehouse_id = fields.Many2one("stock.warehouse", string="From Warehouse", required=True)
    sync_product = fields.Boolean(default=True,
                                  help="Set to True to if you want before import shipment "
                                       "automatically sync the amazon product.")

    def create_amazon_inbound_shipment_line(self, items, inbound_shipment_id, instance_id):
        """
        :param items: dict of shipment details
        :param inbound_shipment_id: inbound shipment record
        :param instance_id: instance record
        :return:
        """
        amazon_inbound_shipment_plan_line_obj = self.env['inbound.shipment.plan.line']
        amazon_product_obj = self.env['amazon.product.ept']

        for item in items:
            seller_sku = item.get('SellerSKU', {}).get('value', '')
            fn_sku = item.get('FulfillmentNetworkSKU', {}).get('value')
            received_qty = float(item.get('QuantityShipped', {}).get('value', 0.0))
            quantity_in_case = float(item.get('QuantityInCase', {}).get('value', 0.0))

            amazon_product = amazon_product_obj.search_amazon_product(\
                instance_id.id, seller_sku, 'FBA')
            if not amazon_product:
                amazon_product = amazon_product_obj.search( \
                    [('product_asin', '=', fn_sku), ('instance_id', '=', instance_id.id)], limit=1)
            if not amazon_product:
                raise UserError(_("Amazon Product is not found in ERP || Seller SKU %s || "
                                  "Instance %s" % ( \
                                      seller_sku, instance_id.name)))
            amazon_inbound_shipment_plan_line_obj. \
                create({'amazon_product_id': amazon_product.id,
                        'seller_sku': seller_sku,
                        'quantity': received_qty,
                        'fn_sku': fn_sku,
                        'odoo_shipment_id': inbound_shipment_id,
                        'quantity_in_case': quantity_in_case
                        })
        return True

    def get_list_inbound_shipment_items(self, shipment_id, instance, inbound_shipment_id):
        """
        Get list of shipment items from amazon to odoo
        :param shipment_id: str
        :param instance: amazon.instance.ept
        :param inbound_shipment_id: amazon.inbound.shipment.ept()
        :return:
        """

        kwargs = self.amz_prepare_inbound_kwargs_vals(instance)
        kwargs.update(
            {'emipro_api': 'check_amazon_shipment_status_v13', 'amazon_shipment_id': shipment_id})
        response = iap_tools.iap_jsonrpc(DEFAULT_ENDPOINT + '/iap_request', params=kwargs, timeout=1000)
        if response.get('reason', False):
            raise UserError(_(response.get('reason', {})))
        items = response.get('items', {})
        return self.create_amazon_inbound_shipment_line(items, inbound_shipment_id, instance)

    def create_amazon_inbound_shipment(self, results, instance_id, from_warehouse_id):
        """
        Method for Create Inbound Shipment which is already created in Amazon.
        :param results: [{},{}]
        :param instance_id: amazon instance id
        :param from_warehouse_id: from warehouse id
        :return: amazon.inbound.shipment.ept() or False
        """
        inbound_shipment = False
        amazon_inbound_shipment_obj = self.env['amazon.inbound.shipment.ept']
        for result in results:
            shipment_name = result.get('ShipmentName', {}).get('value', False)
            shipment_id = result.get('ShipmentId', {}).get('value', False)
            fulfillment_center_id = result.get('DestinationFulfillmentCenterId', {}).get('value',
                                                                                         False)
            label_prep_type = result.get('LabelPrepType', {}).get('value', False)
            are_cases_required = True if result.get('AreCasesRequired', {}).get('value',
                                                                                'false').lower() == 'true' else False
            inbound_shipment = amazon_inbound_shipment_obj.create( \
                {'name': shipment_name, 'fulfill_center_id': fulfillment_center_id,
                 'shipment_id': shipment_id, 'from_warehouse_id': from_warehouse_id,
                 'is_manually_created': True, 'instance_id_ept': instance_id,
                 'label_prep_type': label_prep_type, 'are_cases_required': are_cases_required})
        return inbound_shipment

    def get_inbound_import_shipment(self, instance, warehouse_id, ship_ids):
        """
        Import already created Inbound Shipment from shipment id and
        it will be created for given warehouse id.
        :param instance: amazon.instance.ept()
        :param warehouse_id: stock.warehouse()
        :param ship_ids: []
        :return:
        @author: Keyur Kanani
        """
        amz_inbound_shipment_obj = self.env['amazon.inbound.shipment.ept']
        shipment_ids = ship_ids.split(',')
        # No Need to Import Duplicate Inbound Shipment
        inbound_shipment = amz_inbound_shipment_obj.search([('shipment_id', 'in', shipment_ids)])
        if inbound_shipment:
            shipments = ", ".join(str(shipment.shipment_id) for shipment in inbound_shipment)
            raise UserError(_("Shipments %s already exists" % shipments))
        for shipment_id in shipment_ids:
            kwargs = self.amz_prepare_inbound_kwargs_vals(instance)
            kwargs.update({'emipro_api': 'check_status_v13', 'shipment_ids': [shipment_id]})
            response = iap_tools.iap_jsonrpc(DEFAULT_ENDPOINT + '/iap_request', params=kwargs, timeout=1000)
            if response.get('reason', False):
                raise UserError(_(response.get('reason', {})))
            amazon_shipments = response.get('amazon_shipments', {})
            inbound_shipment = self.create_amazon_inbound_shipment(amazon_shipments, instance.id,
                                                                   warehouse_id.id)
            self.get_list_inbound_shipment_items(shipment_id, instance, inbound_shipment.id)
            inbound_shipment.create_shipment_picking()

    def amz_prepare_inbound_kwargs_vals(self, instance):
        """
        Prepare General kwargs for  inbound shipment
        :param instance: amazon.instance.ept()
        :return: dict {}
        @author: Keyur Kanani
        """
        account = self.env['iap.account'].search([('service_name', '=', 'amazon_ept')])
        dbuuid = self.env['ir.config_parameter'].sudo().get_param('database.uuid')
        kwargs = {'merchant_id': instance.merchant_id and str(instance.merchant_id) or False,
                  'auth_token': instance.auth_token and str(instance.auth_token) or False,
                  'app_name': 'amazon_ept',
                  'account_token': account.account_token,
                  'dbuuid': dbuuid,
                  'amazon_marketplace_code': instance.country_id.amazon_marketplace_code or
                                             instance.country_id.code}
        return kwargs
