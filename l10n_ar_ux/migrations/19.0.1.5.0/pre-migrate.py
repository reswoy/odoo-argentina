"""
Pre-migration: remove orphan inherited views left behind by the Odoo 18→19
platform upgrade.

Several fields, buttons, and elements were removed from core views in Odoo 19
but the platform upgrade does not always clean up inherited views that reference
them, causing ParseError during view validation of custom modules.

This script runs before l10n_ar_ux XMLs are loaded (module ~232/266), which is
early enough to clean orphan views that would break later modules too.
"""
import logging

_logger = logging.getLogger(__name__)

# Elements removed in Odoo 19 that may still be referenced by orphan views.
# Each entry: (model, pattern to match in arch_db::text)
ORPHAN_PATTERNS = [
    ('res.config.settings', 'l10n_ar_afip_activity_id'),
    ('account.payment', 'action_post_and_new'),
]


def migrate(cr, version):
    total_deleted = 0
    for model, pattern in ORPHAN_PATTERNS:
        # arch_db is JSONB in Odoo 19 (translatable field), cast to text
        cr.execute("""
            DELETE FROM ir_ui_view
            WHERE model = %s
            AND arch_db::text LIKE %s
        """, (model, f'%{pattern}%'))
        if cr.rowcount:
            _logger.info(
                "Deleted %s orphan view(s) referencing '%s' in model '%s'",
                cr.rowcount, pattern, model,
            )
            total_deleted += cr.rowcount

    if total_deleted:
        # Clean up orphan ir.model.data references
        cr.execute("""
            DELETE FROM ir_model_data
            WHERE model = 'ir.ui.view'
            AND res_id NOT IN (SELECT id FROM ir_ui_view)
        """)
