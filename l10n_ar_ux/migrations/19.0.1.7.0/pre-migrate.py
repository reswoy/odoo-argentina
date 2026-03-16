"""Pre-migration: clean remaining orphan models missed in 19.0.1.6.0.

Models from card_installment and l10n_ar_import_bill that were still
generating "declared but cannot be loaded" INFO messages.
"""
import logging

_logger = logging.getLogger(__name__)

ORPHAN_MODELS = [
    'account.card',
    'account.card.installment',
    'afip.import.wizard',
    'afip.import.wizard.line',
]


def migrate(cr, version):
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
    _logger.info("Cleaned %s remaining orphan model definitions", len(ORPHAN_MODELS))
