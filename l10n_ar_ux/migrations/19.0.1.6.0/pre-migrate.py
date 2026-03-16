"""Pre-migration: consolidate v18->v19 cleanup for ELOG.

Extends the 19.0.1.5.0 pre-migrate (Reswoy base) with additional
cleanup for shadow modules, helper modules, and orphan models that
were created during ELOG's migration.
"""
import logging

_logger = logging.getLogger(__name__)

# Views referencing fields/actions removed in v19
ORPHAN_VIEW_PATTERNS = [
    # From Reswoy base pre-migrate
    'l10n_ar_afip_activity_id',
    'action_post_and_new',
    # ELOG additions (aeroo fields)
    'stylesheet_id', 'tml_source', 'in_format', 'out_format',
    'parser_model', 'report_wizard', 'aeroo_report',
]

# Modules with no v19 port -- superset of Reswoy base + ELOG
NOT_INSTALLABLE_MODULES = [
    'account_balance_import',
    'account_tax_settlement',
    'card_installment',
    'elog_v19_cleanup',
    'l10n_ar_account_tax_settlement',
    'l10n_ar_import_bill',
    'l10n_ar_payment_bundle',
    'l10n_ar_purchase_stock',
    'l10n_ar_stock_adhoc',
    'l10n_ar_tax_ratio',
    'l10n_ar_tax_settlement_backward_comp',
    'l10n_ar_txt_tucuman',
    'payment_pay_way',
    'product_catalog_aeroo_report',
    'product_catalog_aeroo_report_public_categ',
    'purchase_order_line_number',
    'purchase_stock_picking_invoice_link',
    'report_aeroo',
    'stock_account_ux',
    'stock_voucher',
]

# Models from v18 modules no longer loadable
ORPHAN_MODELS = [
    'stock.book', 'stock.picking.voucher', 'stock.print_stock_voucher',
    'account.tax.settlement.wizard',
    'res.download_files_wizard', 'res.download_files_wizard_line',
    'report.product_catalog_parser',
    'product.product_catalog.wizard', 'product.product_catalog_report',
    'docs_config.installer',
    'report.mimetypes', 'report.product_template_printer',
    'report.report_aeroo.abstract', 'report.sample_report',
    'report.stylesheets',
]


def migrate(cr, version):
    _cleanup_orphan_views(cr)
    _cleanup_orphan_tags(cr)
    _cleanup_not_installable_modules(cr)
    _cleanup_orphan_models(cr)


def _cleanup_orphan_views(cr):
    """Delete inherited views referencing removed fields/actions."""
    total = 0
    for pattern in ORPHAN_VIEW_PATTERNS:
        cr.execute(
            "DELETE FROM ir_ui_view WHERE arch_db::text LIKE %s",
            [f'%{pattern}%'],
        )
        if cr.rowcount:
            _logger.info("Deleted %s orphan view(s) referencing '%s'",
                         cr.rowcount, pattern)
            total += cr.rowcount
    if total:
        cr.execute("""
            DELETE FROM ir_model_data
            WHERE model = 'ir.ui.view'
              AND res_id NOT IN (SELECT id FROM ir_ui_view)
        """)


def _cleanup_orphan_tags(cr):
    """Unlink account tags before module tries to delete them."""
    cr.execute("""
        DELETE FROM account_account_tag_account_tax_repartition_line_rel
        WHERE account_account_tag_id IN (
            SELECT res_id FROM ir_model_data
            WHERE module = 'l10n_ar_ux' AND model = 'account.account.tag'
        )
    """)
    if cr.rowcount:
        _logger.info("Unlinked %s tax repartition refs for l10n_ar_ux tags",
                      cr.rowcount)


def _cleanup_not_installable_modules(cr):
    """Mark removed/disabled modules as uninstalled."""
    cr.execute("""
        UPDATE ir_module_module SET state = 'uninstalled'
        WHERE name IN %s AND state NOT IN ('uninstalled', 'uninstallable')
    """, (tuple(NOT_INSTALLABLE_MODULES),))
    if cr.rowcount:
        _logger.info("Marked %s module(s) as uninstalled", cr.rowcount)


def _cleanup_orphan_models(cr):
    """Remove ir_model records for models no longer in code."""
    for model in ORPHAN_MODELS:
        cr.execute("DELETE FROM ir_rule WHERE model_id IN "
                   "(SELECT id FROM ir_model WHERE model = %s)", (model,))
        cr.execute("DELETE FROM ir_model_constraint WHERE model IN "
                   "(SELECT id FROM ir_model WHERE model = %s)", (model,))
        cr.execute("DELETE FROM ir_model_relation WHERE model IN "
                   "(SELECT id FROM ir_model WHERE model = %s)", (model,))
        cr.execute("DELETE FROM ir_model_access WHERE model_id IN "
                   "(SELECT id FROM ir_model WHERE model = %s)", (model,))
        cr.execute("DELETE FROM ir_model_fields WHERE model = %s", (model,))
        cr.execute("DELETE FROM ir_model_fields WHERE relation = %s", (model,))
        cr.execute("DELETE FROM ir_model_data WHERE model = 'ir.model' "
                   "AND res_id IN (SELECT id FROM ir_model WHERE model = %s)",
                   (model,))
        cr.execute("DELETE FROM ir_model WHERE model = %s", (model,))
    _logger.info("Cleaned %s orphan model definitions", len(ORPHAN_MODELS))
