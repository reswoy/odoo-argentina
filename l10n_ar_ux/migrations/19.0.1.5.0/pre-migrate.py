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

# XML IDs of account.account.tag records removed in v19 that may still be
# referenced by tax repartition lines. We unlink the m2m relation first so
# Odoo can safely delete the tag during _process_end.
ORPHAN_TAG_XMLIDS = [
    'l10n_ar_ux.tag_ret_perc_sicore_aplicada',
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
    for xmlid in ORPHAN_TAG_XMLIDS:
        module, name = xmlid.split('.')
        cr.execute("""
            SELECT res_id FROM ir_model_data
            WHERE module = %s AND name = %s AND model = 'account.account.tag'
        """, (module, name))
        row = cr.fetchone()
        if row:
            tag_id = row[0]
            # Remove m2m references so the tag can be safely deleted by Odoo
            cr.execute("""
                DELETE FROM account_account_tag_account_tax_repartition_line_rel
                WHERE account_account_tag_id = %s
            """, (tag_id,))
            _logger.info(
                "Unlinked tag '%s' (id=%s) from %s tax repartition line(s)",
                xmlid, tag_id, cr.rowcount,
            )
