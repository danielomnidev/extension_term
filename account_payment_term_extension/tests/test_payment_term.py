# Copyright 2015-2016 Akretion
# (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestAccountPaymentTerm(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.account_payment_term = cls.env["account.payment.term"]
        cls.sixty_days_end_of_month = cls.env.ref(
            "account_payment_term_extension.sixty_days_end_of_month"
        )
        cls.account_payment_term_holiday = cls.env["account.payment.term.holiday"]

    def test_00_compute(self):
        res = self.sixty_days_end_of_month.compute(10, date_ref="2015-01-30")
        self.assertEqual(
            res[0][0],
            "2015-03-31",
            "Error in the compute of payment terms with months",
        )

    def test_01_compute(self):
        two_week_payterm = self.account_payment_term.create(
            {
                "name": "2 weeks",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 0,
                            "weeks": 2,
                            "option": "day_after_invoice_date",
                        },
                    )
                ],
            }
        )
        res = two_week_payterm.compute(10, date_ref="2015-03-02")
        self.assertEqual(
            res[0][0],
            "2015-03-16",
            "Error in the compute of payment terms with weeks",
        )

    def test_02_compute(self):
        # test for bug caused by bad use of precision_digits/precision_rounding
        res = self.env.ref("account.account_payment_term_15days").compute(
            0.2, date_ref="2015-03-01", currency=self.env.ref("base.EUR")
        )
        self.assertEqual(
            res[0][0],
            "2015-03-16",
            "Error in the compute of payment terms 15 days",
        )

    def test_03_compute(self):
        two_month_payterm_after_invoice_month = self.account_payment_term.create(
            {
                "name": "2 months ",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 0,
                            "weeks": 0,
                            "months": 2,
                            "option": "after_invoice_month",
                        },
                    )
                ],
            }
        )
        res = two_month_payterm_after_invoice_month.compute(10, date_ref="2015-03-02")
        self.assertEqual(
            res[0][0],
            "2015-05-31",
            "Error in the compute of payment terms with months after invoice month",
        )

    def test_postpone_holiday(self):
        str_date_invoice = "2015-03-02"
        str_date_holiday = "2015-03-16"
        str_date_postponed = "2015-03-17"
        two_week_payterm = self.account_payment_term.create(
            {
                "name": "2 weeks",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 0,
                            "weeks": 2,
                            "option": "day_after_invoice_date",
                        },
                    )
                ],
                "holiday_ids": [
                    (
                        0,
                        0,
                        {
                            "holiday": str_date_holiday,
                            "date_postponed": str_date_postponed,
                        },
                    )
                ],
            }
        )
        res = two_week_payterm.compute(10, date_ref=str_date_invoice)
        self.assertEqual(
            res[0][0],
            str_date_postponed,
            "Error in the compute of payment terms with weeks",
        )

    def test_no_postpone_holiday(self):
        str_date_invoice = "2015-03-02"
        str_date_holiday = "2015-03-17"
        str_date_postponed = "2015-03-18"
        two_week_payterm = self.account_payment_term.create(
            {
                "name": "2 weeks",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 0,
                            "weeks": 2,
                            "option": "day_after_invoice_date",
                        },
                    )
                ],
                "holiday_ids": [
                    (
                        0,
                        0,
                        {
                            "holiday": str_date_holiday,
                            "date_postponed": str_date_postponed,
                        },
                    )
                ],
            }
        )
        res = two_week_payterm.compute(10, date_ref=str_date_invoice)
        self.assertNotEqual(
            res[0][0],
            str_date_postponed,
            "Error in the compute of payment terms with weeks",
        )

    def test_check_holiday(self):
        with self.assertRaises(ValidationError):
            self.account_payment_term_holiday.create(
                {"holiday": "2015-06-01", "date_postponed": "2015-06-01"}
            )

        with self.assertRaises(ValidationError):
            self.account_payment_term_holiday.create(
                {"holiday": "2015-06-02", "date_postponed": "2015-06-01"}
            )

        with self.assertRaises(ValidationError):
            self.account_payment_term_holiday.create(
                {"holiday": "2015-06-03", "date_postponed": "2015-06-04"}
            )
            self.account_payment_term_holiday.create(
                {"holiday": "2015-06-03", "date_postponed": "2015-06-05"}
            )

        with self.assertRaises(ValidationError):
            self.account_payment_term_holiday.create(
                {"holiday": "2015-06-06", "date_postponed": "2015-06-07"}
            )
            self.account_payment_term_holiday.create(
                {"holiday": "2015-06-07", "date_postponed": "2015-06-08"}
            )
