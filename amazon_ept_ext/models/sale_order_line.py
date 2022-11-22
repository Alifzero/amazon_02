# -*- coding: utf-8 -*-

from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def get_item_price(self, order_line, order):
        item_price = float(order_line.get('item-price', 0.0)) or float(
                order_line.get('item_price', 0.0))
        if order.amz_instance_id.amz_tax_id and not order.amz_instance_id.amz_tax_id.price_include:
            return item_price
        tax_amount = float(order_line.get('item-tax', 0.0)) or float(
                order_line.get('tax_amount', 0.0))
        # return tax_amount + item_price
        return item_price

    def get_shipping_price(self, order_line, order):
        ship_price = float(order_line.get('shipping-price', 0.0))
        if order.amz_instance_id.amz_tax_id and not order.amz_instance_id.amz_tax_id.price_include:
            return ship_price
        ship_tax = float(order_line.get('shipping-tax', 0.0))
        # return ship_tax + ship_price
        return ship_price