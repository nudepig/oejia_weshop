# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Category(models.Model):

    _name = 'wxapp.product.category'
    _description = u'商品分类'
    _order = 'level,sort'

    name = fields.Char(string='名称', required=True)
    category_type = fields.Char(string='类型')
    pid = fields.Many2one('wxapp.product.category', string='上级分类', ondelete='cascade')
    child_ids = fields.One2many('wxapp.product.category', 'pid', string='子分类')
    key = fields.Char(string='编号')
    icon = fields.Binary(string='图标/图片')
    icon_site= fields.Selection([('left', '左边'), ('right', '右边')], required=True, default='left', string='图片位置')
    icon_title = fields.Binary(string='标题图标')
    level = fields.Integer(string='分类级别', compute='_compute_level', store=True)
    is_use = fields.Boolean(string='是否启用', default=True, required=True)
    sort = fields.Integer(string='排序')
    product_template_ids = fields.One2many('product.template', 'wxpp_category_id', string='商品')
    product_recommend = fields.One2many('product.template', 'wxpp_recommend_id', string='推荐商品')

    @api.one
    @api.depends('pid')
    def _compute_level(self):
        level = 0
        pid = self.pid
        while True:
            if not pid:
                break

            pid = pid.pid

            level += 1

        self.level = level
        for child in self.child_ids:
            child._compute_level()

    def get_icon_image(self):
        base_url=self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return '%s/web/image/wxapp.product.category/%s/icon/'%(base_url, self.id)

    def get_icon_title_image(self):
        base_url=self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return '%s/web/image/wxapp.product.category/%s/icon_title/'%(base_url, self.id)
