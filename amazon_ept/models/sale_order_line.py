from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    amz_instance_id = fields.Many2one('amazon.instance.ept', string='Amazon Instance',
                                      help="Amazon Instance")
    amz_return_reason = fields.Selection([('NoInventory', 'NoInventory'),
                                          ('ShippingAddressUndeliverable',
                                           'ShippingAddressUndeliverable'),
                                          ('CustomerExchange', 'CustomerExchange'),
                                          ('BuyerCanceled', 'BuyerCanceled'),
                                          ('GeneralAdjustment', 'GeneralAdjustment'),
                                          ('CarrierCreditDecision', 'CarrierCreditDecision'),
                                          ('RiskAssessmentInformationNotValid',
                                           'RiskAssessmentInformationNotValid'),
                                          ('CarrierCoverageFailure', 'CarrierCoverageFailure'),
                                          ('CustomerReturn', 'CustomerReturn'),
                                          ('MerchandiseNotReceived', 'MerchandiseNotReceived')
                                          ], string="Return Reason", default="NoInventory")

    amz_order_line_ref = fields.Char('Amazon Order Line Reference',
                                     help="Amazon Sale order line reference")
    amazon_order_item_id = fields.Char(help="Amazon Sale order line reference")
    amazon_product_id = fields.Many2one("amazon.product.ept", "Amazon Product",
                                        help="Amazon Product Id")
    amazon_order_qty = fields.Float("Amazon Order Quantity", help="Amazon Ordered Quantity")
    amazon_shipment_item_id = fields.Char(help="Amazon shipment item id for FBA")
    line_tax_amount = fields.Float("Line Tax", default=0.0, digits="Product Price",
                                   help="Order line tax amount")
    amz_shipping_charge_ept = fields.Float("Amazon Shipping Charge", default=0.0,
                                           digits="Product Price",
                                           help="Amazon FBA Shipping Charge")
    amz_shipping_discount_ept = fields.Float("Shipping Discount", default=0.0,
                                             digits="Product Price",
                                             help="Amazon FBA Shipping discount")
    amz_gift_wrapper_charge = fields.Float("Gift Wrapper Charge", default=0.0,
                                           digits="Product Price",
                                           help="Amazon FBA Gift Wrapper Charge")
    amz_promotion_discount = fields.Float("Promotion Discount", default=0.0, digits="Product Price",
                                          help="Amazon FBA Promotion Discount")
    amz_shipping_charge_tax = fields.Float("Amazon Shipping Tax", default=0.0,
                                           digits="Product Price",
                                           help="Amazon FBA Shipping Charges")
    amz_order_line_tax = fields.Float("Order Line Tax", default=0.0, digits="Product Price",
                                      help="Amazon order line taxes")
    amz_gift_wrapper_tax = fields.Float("Tax of Shipping Charge", default=0.0,
                                        digits="Product Price",
                                        help="Amazon FBA Gift Wrapper Tax")

    def create_amazon_sale_order_line(self, amazon_order, line_data, product_details):
        seller_sku = line_data.get('sku', '')
        instance = amazon_order.amz_instance_id
        odoo_product = product_details.get((seller_sku, instance.id), False)
        if odoo_product:
            if line_data.get('shipment-item-id', ''):
                sale_line = self.search(\
                    [('amazon_shipment_item_id', '=', line_data.get('shipment-item-id', ''))])
                if not sale_line:
                    available_line = self.search([('amz_instance_id', '=', instance.id), (
                        'amazon_order_item_id', '=', line_data.get('amazon-order-item-id', ''))])
                    if available_line:
                        unit_price = self.get_item_price(line_data, amazon_order)
                        unit_price = unit_price / float(line_data.get('quantity-shipped', 1.0))
                        if available_line.price_unit == unit_price:
                            updated_qty = float(
                                line_data.get('quantity-shipped', 0.0)) + available_line.product_uom_qty
                            available_line.write({'product_uom_qty': updated_qty})
                    else:
                        order_line_vals = self.create_sale_order_line_vals_amazon(line_data,
                                                                                  odoo_product,
                                                                                  amazon_order)
                        if line_data.get('quantity-shipped', 0.0):
                            order_line_vals.update(
                                {'product_uom_qty': float(line_data.get('quantity-shipped', 0.0))})
                        sale_line = self.create(order_line_vals)
                        self.create_amazon_order_charges_line(sale_line, line_data)
                return sale_line
            available_line = self.search([('amz_instance_id', '=', instance.id), (\
                'amazon_order_item_id', '=', line_data.get('amazon-order-item-id', ''))])
            if not available_line:
                order_line_vals = self.create_sale_order_line_vals_amazon(line_data,
                                                                          odoo_product,
                                                                          amazon_order)
                sale_line = self.create(order_line_vals)
                return sale_line
        return True

    def create_sale_order_line_vals_amazon(self, order_line, odoo_product, amazon_order):
        """
        Create Sale order line values for amazon order
        :param order_line:
        :param odoo_product:
        :param amazon_order:
        :return: {}
        """

        so_line_obj = self.env['sale.order.line']
        taxargs = {}
        unit_price = self.get_item_price(order_line, amazon_order)
        item_tax = self.get_item_tax_amount(order_line)
        quantity = float(order_line.get('product_uom_qty', 0.0) or order_line.get('quantity-shipped', 0.0))
        if quantity > 0.0:
            unit_price = unit_price / quantity
        vals = ({
            'order_id': amazon_order.id,
            'product_id': odoo_product and odoo_product.id or False,
            'company_id': amazon_order.company_id.id,
            'warehouse_id': order_line.get('warehouse', False),
            'description': order_line.get('name', '') or order_line.get('product-name', ''),
            'order_qty': quantity,
            'price_unit': unit_price,
            'discount': 0.0,
            'product_uom': odoo_product and odoo_product.product_tmpl_id.uom_id.id
        })
        order_vals = so_line_obj.create_sale_order_line_ept(vals)
        if amazon_order.amz_instance_id.is_use_percent_tax:
            unit_tax = item_tax / quantity if quantity > 0.0 else item_tax
            item_tax_percent = (unit_tax * 100) / unit_price if unit_price > 0 else 0.00
            amz_tax_id = amazon_order.amz_instance_id.amz_tax_id
            taxargs = {'line_tax_amount_percent': item_tax_percent,
                       'tax_id': [(6, 0, [amz_tax_id.id])]}

        order_vals.update({
            'amazon_order_qty': order_line.get('amazon_order_qty', 0.0) or order_line.get(\
                'quantity-shipped', 0.0),
            'invoice_status': False,
            'line_tax_amount': item_tax,
            'amazon_order_item_id': order_line.get('amazon_order_item_id', '') or order_line.get(
                'amazon-order-item-id', ''),
            'amazon_shipment_item_id': order_line.get('amazon_shipment_item_id', '') or order_line.get(
                'shipment-item-id', ''),
            **taxargs
        })
        return order_vals

    def create_amazon_order_charges_line(self, amazon_order_line, line_data):
        amazon_order = amazon_order_line.order_id
        instance = amazon_order.amz_instance_id
        """Shipment Charge Line"""
        shipping_price = self.get_shipping_price(line_data, amazon_order)
        if shipping_price > 0:
            shipment_product = amazon_order.carrier_id and \
                               amazon_order.carrier_id.product_id or \
                               instance.seller_id and instance.seller_id.shipment_charge_product_id
            if shipment_product:
                order_line_vals = self.create_sale_order_line_vals_amazon(line_data,
                                                                          shipment_product,
                                                                          amazon_order)
                shipping_tax = self.get_shipping_tax_amount(line_data)
                shipargs = {}
                if instance.is_use_percent_tax:
                    item_tax_percent = (shipping_tax * 100) / shipping_price
                    amz_tax_id = amazon_order.amz_instance_id.amz_tax_id
                    shipargs = {'line_tax_amount_percent': item_tax_percent,
                                'tax_id': [(6, 0, [amz_tax_id.id])]}

                order_line_vals.update(
                    {'name': "Shipping and Handling",
                     'price_unit': shipping_price,
                     'amazon_order_qty': 1, 'product_uom_qty': 1,
                     'amazon_order_item_id': line_data.get('amazon-order-item-id', '') + '_ship',
                     **shipargs})
                amazon_order_line and amazon_order_line.write(
                    {'amz_shipping_charge_ept': shipping_price,
                     'amz_shipping_charge_tax': shipping_tax})
                self.create(order_line_vals)

        """Gift Wrapper Line"""
        git_wrapper_price = self.get_gift_wrapper_price(line_data, amazon_order)
        if git_wrapper_price > 0:
            gift_wrapper_product = instance.seller_id and instance.seller_id.gift_wrapper_product_id
            if gift_wrapper_product:
                giftargs = {}
                order_line_vals = self.create_sale_order_line_vals_amazon(line_data,
                                                                          gift_wrapper_product,
                                                                          amazon_order)
                gift_wrapper_tax = self.get_gift_wrapper_tax_amount(line_data)
                if instance.is_use_percent_tax:
                    gift_tax_percent = (gift_wrapper_tax * 100) / git_wrapper_price
                    amz_tax_id = amazon_order.amz_instance_id.amz_tax_id
                    giftargs = {'line_tax_amount_percent': gift_tax_percent,
                                'tax_id': [(6, 0, [amz_tax_id.id])]}
                order_line_vals.update(
                    {'name': "Gift Wrapping", 'price_unit': git_wrapper_price,
                     'amazon_order_qty': 1, 'product_uom_qty': 1,
                     'amazon_order_item_id': line_data.get('amazon-order-item-id', '') + '_gift_wrap',
                     **giftargs})
                amazon_order_line and amazon_order_line.write(
                    {'amz_gift_wrapper_charge': git_wrapper_price,
                     'amz_gift_wrapper_tax': gift_wrapper_tax})
                self.create(order_line_vals)

        """Shipment Promotion Discount Line"""
        if line_data.get('ship-promotion-discount') and float(line_data.get('ship-promotion-discount')) < 0:
            shipment_discount_product = instance.seller_id and instance.seller_id.ship_discount_product_id
            if shipment_discount_product:
                discargs = {}
                order_line_vals = self.create_sale_order_line_vals_amazon(line_data,
                                                                          shipment_discount_product,
                                                                          amazon_order)
                ship_tax = self.get_shipping_tax_amount(line_data)
                discount_price = float(line_data.get('ship-promotion-discount', 0.0)) - ship_tax
                if instance.is_use_percent_tax:
                    discount_price = float(line_data.get('ship-promotion-discount', 1.0))
                    gift_tax_percent = (ship_tax * 100) / discount_price
                    amz_tax_id = amazon_order.amz_instance_id.amz_tax_id
                    discargs = {'line_tax_amount_percent': abs(gift_tax_percent),
                                'tax_id': [(6, 0, [amz_tax_id.id])]}
                order_line_vals.update(
                    {'name': "Shipping Discount", 'price_unit': discount_price,
                     'amazon_order_qty': 1, 'product_uom_qty': 1,
                     'amazon_order_item_id': line_data.get(\
                         'amazon-order-item-id', '') + '_ship_discount',
                     **discargs})
                amazon_order_line and amazon_order_line.write(\
                    {'amz_shipping_discount_ept': discount_price})
                self.create(order_line_vals)

        """Promotion Discount"""
        if line_data.get('item-promotion-discount', 0.0) and float(\
                line_data.get('item-promotion-discount', 0.0)) < 0.0:
            promotion_discount_product = instance.seller_id and instance.seller_id.promotion_discount_product_id
            if promotion_discount_product:
                order_line_vals = self.create_sale_order_line_vals_amazon(line_data,
                                                                          promotion_discount_product,
                                                                          amazon_order)
                order_line_vals.update({'name': "Promotion Discount", 'amazon_order_qty': 1,
                                        'product_uom_qty': 1,
                                        'price_unit': float(\
                                            line_data.get('item-promotion-discount', 0.0)),
                                        'amazon_order_item_id': line_data.get(
                                            'amazon-order-item-id', False) + '_promo_discount'})
                if instance.is_use_percent_tax:
                    order_line_vals.update({'line_tax_amount_percent': 0.00, 'line_tax_amount': 0.00})
                amazon_order_line and amazon_order_line.write(
                    {'amz_promotion_discount': float(
                        line_data.get('item-promotion-discount', 0.0))})
                self.create(order_line_vals)
        return True

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        lines = self.filtered(lambda l: l.order_id.amz_fulfillment_by != 'FBA')
        return super(SaleOrderLine, lines)._action_launch_stock_rule(
            previous_product_uom_qty=previous_product_uom_qty)

    def get_item_price(self, order_line, order):
        item_price = float(order_line.get('item-price', 0.0)) or float(
                order_line.get('item_price', 0.0))
        if order.amz_instance_id.amz_tax_id and not order.amz_instance_id.amz_tax_id.price_include:
            return item_price
        tax_amount = float(order_line.get('item-tax', 0.0)) or float(
                order_line.get('tax_amount', 0.0))
        return tax_amount + item_price

    def get_item_tax_amount(self, order_line):
        tax_amount = float(order_line.get('item-tax', 0.0)) or float(
            order_line.get('tax_amount', 0.0))
        return tax_amount

    def get_shipping_tax_amount(self, order_line):
        tax_amount = float(order_line.get('shipping-tax', 0.0))
        return tax_amount

    def get_shipping_price(self, order_line, order):
        ship_price = float(order_line.get('shipping-price', 0.0))
        if order.amz_instance_id.amz_tax_id and not order.amz_instance_id.amz_tax_id.price_include:
            return  ship_price
        ship_tax = float(order_line.get('shipping-tax', 0.0))
        return ship_tax + ship_price

    def get_gift_wrapper_price(self, order_line, order):
        gift_price = float(order_line.get('gift-wrap-price', 0.0))
        if order.amz_instance_id.amz_tax_id and not order.amz_instance_id.amz_tax_id.price_include:
            return gift_price
        gift_tax = float(order_line.get('gift-wrap-tax', 0.0))
        return gift_price + gift_tax

    def get_gift_wrapper_tax_amount(self, order_line):
        gift_tax = float(order_line.get('gift-wrap-tax', 0.0))
        return gift_tax

    def _prepare_invoice_line(self, **optional_values):
        """
        Preparing Invoice Lines for FBA Orders only
        Reason: While Update invoice in Amazon need invoices as per Shipment id.
        @author: Keyur Kanani
        :return: _prepare_invoice_line or False
        """
        self.ensure_one()
        if self._context.get('shipment_item_ids', False):
            if self.order_id.amz_fulfillment_by == 'FBA' and \
                    self.amazon_shipment_item_id not in self._context.get('shipment_item_ids', False):
                return {'display_type': False}
        return super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
