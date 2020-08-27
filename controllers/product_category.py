# -*- coding: utf-8 -*-

import json

from odoo import http
from odoo.http import request

from .. import defs
from .base import BaseController


import logging

_logger = logging.getLogger(__name__)


class WxappCategory(http.Controller, BaseController):

    @http.route('/<string:sub_domain>/shop/goods/category/all', auth='public', methods=['GET'])
    def all(self, sub_domain):
        ret, entry = self._check_domain(sub_domain)
        if ret:return ret

        try:
            all_category = request.env['wxapp.product.category'].sudo().search([
                ('is_use', '=', True)
            ])
            if not all_category:
                return self.res_err(404)

            data = [
                {
                    "dateAdd": each_category.create_date,
                    "dateUpdate": each_category.write_date,
                    "icon": each_category.get_icon_image() if each_category.icon else '',
                    "icon_site": each_category.icon_site,
                    "icon_title": each_category.get_icon_title_image() if each_category.icon_title else '',
                    "id": each_category.id,
                    "product_recommend": self.get_product_recommend(each_category.product_recommend),
                    "isUse": each_category.is_use,
                    "key": each_category.key,
                    "level": each_category.level,
                    "name": each_category.name,
                    "paixu": each_category.sort or 0,
                    "pid": each_category.pid.id if each_category.pid else 0,
                    "type": each_category.category_type,
                    "userId": each_category.create_uid.id
                } for each_category in all_category
            ]
            return self.res_ok(data)

        except Exception as e:
            _logger.exception(e)
            return self.res_err(-1, str(e))

    def get_product_recommend(self, each_category):
        data={}
        for index,product in enumerate(each_category):
            data[index] = {
                'id' : product.id,
                'name' : product.name,
                'price' : product.original_price,  #产品的销售价格改为小程序的价格
                'icon' : product.get_main_image()

            }
        return data

