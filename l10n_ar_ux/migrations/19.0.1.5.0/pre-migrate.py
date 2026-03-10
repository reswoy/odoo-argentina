"""
Pre-migration: remove orphan inherited views referencing l10n_ar_afip_activity_id.

In Odoo 19, the field l10n_ar_afip_activity_id and the model l10n_ar.afip.activity
were removed from l10n_ar core. The platform upgrade does not clean up inherited
views that reference this field, causing a ParseError during view validation.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # arch_db is stored as JSONB in Odoo 19 (translatable field),
    # so we cast to text for LIKE to work
    cr.execute("""
        DELETE FROM ir_ui_view
        WHERE model = 'res.config.settings'
        AND arch_db::text LIKE '%%l10n_ar_afip_activity_id%%'
    """)
    if cr.rowcount:
        _logger.info("Deleted %s orphan view(s) referencing l10n_ar_afip_activity_id", cr.rowcount)
        cr.execute("""
            DELETE FROM ir_model_data
            WHERE model = 'ir.ui.view'
            AND res_id NOT IN (SELECT id FROM ir_ui_view)
        """)
