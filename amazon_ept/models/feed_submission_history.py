# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

"""
Added class to store feed history and auto process to update tracking number feed cron.
"""

import logging
import time

from odoo import models, fields, _
from odoo.addons.iap.tools import iap_tools
from odoo.exceptions import UserError

from .utils import xml2dict
from ..endpoint import DEFAULT_ENDPOINT

_logger = logging.getLogger(__name__)


class FeedSubmissionHistory(models.Model):
    """
    Added class to store feed history
    """
    _name = "feed.submission.history"
    _description = 'feed.submission.history'
    _rec_name = 'feed_result_id'
    _inherit = ['mail.thread']
    _order = 'feed_submit_date desc'

    feed_result_id = fields.Char(size=256, string='Feed Result ID')
    feed_result = fields.Text()
    message = fields.Text()
    feed_submit_date = fields.Datetime()
    feed_result_date = fields.Datetime()
    instance_id = fields.Many2one('amazon.instance.ept', string='Instance', copy=False)
    user_id = fields.Many2one('res.users', string="Requested User")
    seller_id = fields.Many2one('amazon.seller.ept', string="Seller", copy=False)
    invoice_id = fields.Many2one('account.move', copy=False)
    feed_type = fields.Selection([('export_product', 'Export Products'),
                                  ('export_stock', 'Export Stock'),
                                  ('export_price', 'Export Price'),
                                  ('export_image', 'Export Image'),
                                  ('update_tracking_number', 'Update Tracking Number'),
                                  ('update_carton_content', 'Update Carton Content'),
                                  ('cancel_request', 'Cancel Request in Amazon'),
                                  ('upload_invoice', 'Upload Customer Invoice in Amazon')],
                                 string="Feed Submission Type")

    def get_feed_submission_result(self):
        """
        This method get the feed submission result.
        :return:True
        """

        feed_submission_id = self.feed_result_id
        if not self.seller_id or not feed_submission_id:
            if not self._context.get('auto_process'):
                raise UserError(_('You must need to set Seller and feed submission ID.'))
            _logger.info('You must need to set Seller and feed submission ID.')
            return False

        account = self.env['iap.account'].search([('service_name', '=', 'amazon_ept')])
        dbuuid = self.env['ir.config_parameter'].sudo().get_param('database.uuid')
        merchant_id = self.seller_id.merchant_id if self.seller_id else False
        auth_token = self.seller_id.auth_token if self.seller_id else False
        kwargs = {'merchant_id': merchant_id,
                  'auth_token': auth_token,
                  'app_name': 'amazon_ept',
                  'account_token': account.account_token,
                  'emipro_api': 'get_feed_submission_result_V13',
                  'dbuuid': dbuuid,
                  'amazon_marketplace_code': self.seller_id.country_id.amazon_marketplace_code or
                                             self.seller_id.country_id.code,
                  'feed_submission_id': feed_submission_id}

        response = iap_tools.iap_jsonrpc(DEFAULT_ENDPOINT + '/iap_request', params=kwargs, timeout=1000)
        if response.get('reason', False):
            if self._context.get('auto_process', False):
                _logger.info(response.get('reason', {}))
                result = False
            else:
                raise UserError(_(response.get('reason', {})))
        else:
            result = response.get('result', {})
            self.write(
                {'feed_result': str(result),
                 'feed_result_date': time.strftime("%Y-%m-%d %H:%M:%S")})
        return result

    def update_tracking_number_feed_cron(self):
        sale_order_obj = self.env['sale.order']
        stock_picking_obj = self.env['stock.picking']
        feeds = self.search(
            [('feed_type', '=', 'update_tracking_number'), ('feed_result', '=', False)])
        for feed in feeds:
            response = feed.with_context(auto_process=True).get_feed_submission_result()
            if response:
                xml_to_dict_obj = xml2dict()
                result = xml_to_dict_obj.fromstring(response)
                messages_error = result.get('AmazonEnvelope', {}).get('Message', {}).get(
                    'ProcessingReport', {}).get(\
                    'ProcessingSummary', {}).get('MessagesWithError', {}).get('value', '')
                messages_warning = result.get('AmazonEnvelope', {}).get('Message', {}).get(
                    'ProcessingReport', {}).get(\
                    'ProcessingSummary', {}).get('MessagesWithWarning', {}).get('value', '')
                if messages_error and messages_warning == '0':
                    stock_picking_obj.search([('feed_submission_id', '=', feed.id)]).write(\
                        {'updated_in_amazon': True})
                else:
                    marketplaceids = feed.seller_id.instance_ids.mapped(\
                        lambda l: l.marketplace_id.market_place_id)
                    if not marketplaceids:
                        _logger.debug("There is no any instance is configured of seller %s" % (\
                            feed.seller_id.name))
                    #     continue
                    # self.amazon = sale_order_obj.check_already_status_updated_in_amazon(\
                    #     feed.seller_id, marketplaceids, feed.seller_id.instance_ids)
        return True
