"""
Pre-migration for l10n_ar_ux 18.0 → 19.0

Cleans up orphan data left behind by the Odoo platform upgrade that would
cause errors during the -u phase of custom modules:

1. Orphan inherited views referencing removed fields/buttons
2. Account tags that were removed from XML but are still referenced by
   tax repartition lines (foreign key constraint would block deletion)
"""
import logging

_logger = logging.getLogger(__name__)

# Patterns to match in arch_db::text, searched across ALL models.
# These are elements removed in Odoo 19 core that orphan views may still reference.
ORPHAN_VIEW_PATTERNS = [
    'l10n_ar_afip_activity_id',
    'action_post_and_new',
]



def migrate(cr, version):
    _cleanup_orphan_views(cr)
    _cleanup_orphan_tags(cr)


def _cleanup_orphan_views(cr):
    total_deleted = 0
    for pattern in ORPHAN_VIEW_PATTERNS:
        # arch_db is JSONB in Odoo 19 (translatable field), cast to text
        cr.execute("""
            DELETE FROM ir_ui_view
            WHERE arch_db::text LIKE %s
        """, (f'%{pattern}%',))
        if cr.rowcount:
            _logger.info(
                "Deleted %s orphan view(s) referencing '%s'",
                cr.rowcount, pattern,
            )
            total_deleted += cr.rowcount

    if total_deleted:
        # Clean up orphan ir.model.data references
        cr.execute("""
            DELETE FROM ir_model_data
            WHERE model = 'ir.ui.view'
            AND res_id NOT IN (SELECT id FROM ir_ui_view)
        """)


def _cleanup_orphan_tags(cr):
    # Remove ALL m2m references for tags owned by l10n_ar_ux, so Odoo can
    # safely delete them during _process_end without FK violations
    cr.execute("""
        DELETE FROM account_account_tag_account_tax_repartition_line_rel
        WHERE account_account_tag_id IN (
            SELECT res_id FROM ir_model_data
            WHERE module = 'l10n_ar_ux'
            AND model = 'account.account.tag'
        )
    """)
    if cr.rowcount:
        _logger.info(
            "Unlinked %s tax repartition line reference(s) for l10n_ar_ux tags",
            cr.rowcount,
        )
