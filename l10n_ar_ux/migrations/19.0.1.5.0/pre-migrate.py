"""
Pre-migration: remove orphan inherited views referencing l10n_ar_afip_activity_id.

In Odoo 19, the field l10n_ar_afip_activity_id and the model l10n_ar.afip.activity
were removed from l10n_ar core. The platform upgrade does not clean up inherited
views that reference this field, causing a ParseError during view validation.
"""
from odoo.tools import sql


def migrate(cr, version):
    cr.execute("""
        DELETE FROM ir_ui_view
        WHERE model = 'res.config.settings'
        AND arch_db LIKE '%%l10n_ar_afip_activity_id%%'
    """)
    if cr.rowcount:
        cr.execute("DELETE FROM ir_model_data WHERE model = 'ir.ui.view' AND res_id NOT IN (SELECT id FROM ir_ui_view)")
