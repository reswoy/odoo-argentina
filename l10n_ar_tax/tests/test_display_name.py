from odoo.tests.common import TransactionCase


class TestJurisdictionPadronDisplayName(TransactionCase):
    def test_display_name_uses_company_and_jurisdiction(self):
        state = self.env["res.country.state"].search([], limit=1)
        padron = self.env["res.company.jurisdiction.padron"].new(
            {
                "company_id": self.env.company.id,
                "state_id": state.id,
            }
        )

        self.assertEqual(
            padron.display_name,
            "%s: %s" % (self.env.company.name, state.name),
        )
