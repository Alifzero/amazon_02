# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


"""
Added class and methods to get labels from the wizard
"""
import base64
import os
import time
import zipfile

from odoo import models, fields, _
from odoo.addons.iap.tools import iap_tools
from odoo.exceptions import UserError

from ..endpoint import DEFAULT_ENDPOINT


class AmazonShipmentLabelWizard(models.TransientModel):
    """
    Added class to get labels from the amazon
    """
    _name = "amazon.shipment.label.wizard"
    _description = 'amazon.shipment.label.wizard'

    number_of_box = fields.Integer(string='Number of Boxes', default=1)
    number_of_package = fields.Integer(related="number_of_box", string='Number of Labels')
    page_type = fields.Selection([('PackageLabel_Letter_2', 'PackageLabel_Letter_2'),
                                  ('PackageLabel_Letter_4', 'PackageLabel_Letter_4'),
                                  ('PackageLabel_Letter_6', 'PackageLabel_Letter_6'),
                                  ('PackageLabel_A4_2', 'PackageLabel_A4_2'),
                                  ('PackageLabel_A4_4', 'PackageLabel_A4_4'),
                                  ('PackageLabel_Plain_Paper', 'PackageLabel_Plain_Paper')],
                                 required=True,
                                 string='Package Type',
                                 help="""
    * PackageLabel_Letter_2 : Two labels per US Letter label sheet. Supported in Canada and the US. 
                            Note that this is the only valid value for Amazon-partnered shipments in 
                            the US that use UPS as the carrier.\n
    * PackageLabel_Letter_4 : Four labels per US Letter label sheet. Supported in Canada and the US.\n
    * PackageLabel_Letter_6 : Six labels per US Letter label sheet. Supported in Canada and the US. 
                            Note that this is the only valid value for non-Amazon-partnered 
                            shipments in the US.\n
    * PackageLabel_A4_2 : Two labels per A4 label sheet. Supported in France, Germany, Italy, Spain, 
                        and the UK.\n
    * PackageLabel_A4_4 : Four labels per A4 label sheet. Supported in France, Germany, Italy, Spain, 
                        and the UK.\n
    * PackageLabel_Plain_Paper: One label per sheet of US Letter paper. Supported in all marketplaces.\n""")

    def get_instance(self, shipment):
        """
        This method is used to get the instance
        """
        if shipment.instance_id_ept:
            return shipment.instance_id_ept
        return shipment.shipment_plan_id.instance_id

    def get_labels_from_amazon(self, instance, label_type, shipment_rec, number_of_pallet,
                               number_of_package):
        """
        This method is used request for get labels from the amazon and return the response
        """

        account = self.env['iap.account'].search([('service_name', '=', 'amazon_ept')])
        dbuuid = self.env['ir.config_parameter'].sudo().get_param('database.uuid')

        kwargs = {'merchant_id': instance.merchant_id and str(instance.merchant_id) or False,
                  'auth_token': instance.auth_token and str(instance.auth_token) or False,
                  'app_name': 'amazon_ept',
                  'account_token': account.account_token,
                  'emipro_api': 'get_labels_from_amazon_v13',
                  'dbuuid': dbuuid,
                  'amazon_marketplace_code': instance.country_id.amazon_marketplace_code or
                                             instance.country_id.code,
                  'shipment_id': shipment_rec.shipment_id,
                  'page_type': self.page_type,
                  'number_of_pallet': number_of_pallet,
                  'number_of_package': number_of_package,
                  'label_type': label_type,
                  }
        response = iap_tools.iap_jsonrpc(DEFAULT_ENDPOINT + '/iap_request', params=kwargs, timeout=1000)
        return response

    def get_unique_labels_from_amazon(self, shipment_rec):
        """
        This method is used to get unique labels from the amazon.
        """
        parcels = shipment_rec.partnered_small_parcel_ids \
            if shipment_rec.partnered_small_parcel_ids else shipment_rec.partnered_ltl_ids

        list_box_no = parcels.mapped('box_no')

        if not list_box_no:
            raise UserError(_("No Box information found for unique labels"))
        return list_box_no

    def get_labels(self):
        """
        This method is used to get label from the amazon
        """
        self.ensure_one()
        ctx = self._context.copy() or {}
        shipment_id = ctx.get('active_id', False)
        model = ctx.get('active_model', False)
        account = self.env['iap.account'].search([('service_name', '=', 'amazon_ept')])
        dbuuid = self.env['ir.config_parameter'].sudo().get_param('database.uuid')

        if not shipment_id or model != 'amazon.inbound.shipment.ept':
            return True
        shipment_rec = self.env['amazon.inbound.shipment.ept'].browse(shipment_id)
        instance = self.get_instance(shipment_rec)
        country_code = instance.marketplace_id.country_id.code if \
            instance.marketplace_id.country_id else ''
        country = instance.marketplace_id.country_id.name if \
            instance.marketplace_id.country_id else ''
        page_type = self.page_type
        label_type = ctx.get('label_type', '')
        number_of_package = 1
        number_of_pallet = 1
        if label_type == 'delivery':
            number_of_pallet = self.number_of_package
        else:
            number_of_package = self.number_of_package
        flag = False
        if page_type in ['PackageLabel_Letter_2', 'PackageLabel_Letter_4',
                         'PackageLabel_Letter_6'] and country_code not in ['CA', 'US']:
            flag = True
        if page_type in ['PackageLabel_A4_2', 'PackageLabel_A4_4'] and country_code not in ['FR',
                                                                                            'DE',
                                                                                            'IT',
                                                                                            'ES',
                                                                                            'GB']:
            flag = True
        if page_type == 'PackageLabel_Letter_2' and country_code == 'US' and not shipment_rec.is_partnered:
            flag = True
        if page_type == 'PackageLabel_Letter_6' and country_code == 'US' and shipment_rec.is_partnered:
            flag = True
        if flag:
            raise UserError(_( \
                'Please select correct Page Type, Page type %s not supported for country %s.' % ( \
                    page_type, country)))

        if shipment_rec.is_partnered:
            list_box_no = self.get_unique_labels_from_amazon(shipment_rec)
            kwargs = {'merchant_id': instance.merchant_id and str(instance.merchant_id) or False,
                      'auth_token': instance.auth_token and str(instance.auth_token) or False,
                      'app_name': 'amazon_ept',
                      'account_token': account.account_token,
                      'emipro_api': 'get_labels_v13',
                      'dbuuid': dbuuid,
                      'amazon_marketplace_code': instance.country_id.amazon_marketplace_code or
                                                 instance.country_id.code,
                      'shipment_id': shipment_rec.shipment_id,
                      'page_type': self.page_type,
                      'list_box_no': list_box_no,
                      }
            response = iap_tools.iap_jsonrpc(DEFAULT_ENDPOINT + '/iap_request', params=kwargs, timeout=1000)

        else:
            response = self.get_labels_from_amazon(instance, label_type, shipment_rec,
                                                   number_of_pallet, number_of_package)

        if not shipment_rec.is_partnered:
            shipment_rec.update_non_partnered_carrier()
            response = self.get_labels_from_amazon(instance, label_type, shipment_rec,
                                                   number_of_pallet, number_of_package)
        elif response.get('reason', False):
            raise UserError(_(response.get('reason', {})))

        result = response.get('result', {})
        label_doc = result.get('TransportDocument', {}).get('PdfDocument', {}).get('value', '')

        attachment_obj = self.env['ir.attachment']
        shipment_rec.write({'box_count': self.number_of_box})
        if label_doc:
            label_doc = base64.b64decode(label_doc)
            filename = 'package_label_%s.zip' % (time.strftime('%Y%m%d_%H%M%S'))
            label_zip = open('/tmp/%s' % filename, 'wb')
            label_zip.write(label_doc)
            label_zip.close()
            zip_file = open('/tmp/%s' % filename, 'rb')
            z = zipfile.ZipFile(zip_file)
            for name in z.namelist():
                path = z.extract(name, '/tmp/')
                fh = open(path, 'rb')
                datas = base64.b64encode(fh.read())
                fh.close()
                if label_type == 'delivery':
                    fname = 'Delivery_' + name
                else:
                    fname = 'Shipment_' + name
                attachments = attachment_obj.search([('name', '=', fname),
                                                     ('res_model', '=',
                                                      'amazon.inbound.shipment.ept'),
                                                     ('res_id', '=', shipment_rec.id)
                                                     ])
                if attachments:
                    attachments.unlink()
                attachment = attachment_obj.create({
                    'name': fname,
                    'datas': datas,
                    'res_model': 'mail.compose.message',
                    'type': 'binary'
                })
                shipment_rec.message_post(body=_("<b>Amazon Labels Downloaded</b>"),
                                          attachment_ids=attachment.ids)
                try:
                    os.remove(path)
                except Exception as e:
                    pass
            zip_file.close()
            try:
                os.remove('/tmp/%s' % filename)
            except Exception as e:
                pass
        return True
