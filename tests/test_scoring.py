import unittest

from turkmopet_b2b import AccountTier, WholesaleAccount, rank_accounts, score_account


class AccountScoringTests(unittest.TestCase):
    def test_pro_account(self) -> None:
        result = score_account(
            WholesaleAccount(
                monthly_order_value=120_000,
                active_months=18,
                payment_delay_days=0,
                return_rate=0.01,
                has_tax_certificate=True,
            )
        )
        self.assertEqual(result.total, 100)
        self.assertEqual(result.tier, AccountTier.PRO)

    def test_payment_and_return_risk_reduce_score(self) -> None:
        result = score_account(
            WholesaleAccount(
                monthly_order_value=35_000,
                active_months=6,
                payment_delay_days=20,
                return_rate=0.25,
                has_tax_certificate=True,
            )
        )
        self.assertEqual(result.total, 20)
        self.assertEqual(result.tier, AccountTier.STARTER)
        self.assertIn("payment-risk", result.reasons)
        self.assertIn("high-return-rate", result.reasons)

    def test_invalid_return_rate_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            score_account(WholesaleAccount(monthly_order_value=1, active_months=1, return_rate=1.1))

    def test_accounts_are_ranked_descending(self) -> None:
        ranked = rank_accounts(
            [
                WholesaleAccount(monthly_order_value=5_000, active_months=1),
                WholesaleAccount(monthly_order_value=50_000, active_months=12, has_tax_certificate=True),
            ]
        )
        self.assertGreater(ranked[0].total, ranked[1].total)


if __name__ == "__main__":
    unittest.main()
