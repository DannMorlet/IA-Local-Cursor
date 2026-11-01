"""Tests for conservative CI evidence reporting."""
import unittest
from functional_matrix import CHECKS, evaluate, markdown


class FunctionalMatrixTests(unittest.TestCase):
    def test_missing_evidence_is_not_success(self):
        report = evaluate({})
        self.assertEqual(report['puntos_verificados'], 0)
        self.assertEqual(report['puntos_sin_probar'], 100)
        self.assertTrue(all(c['estado'] == 'SIN PROBAR' for c in report['checks']))

    def test_ci_can_never_claim_full_app_works(self):
        evidence = {v: 'success' for _, _, _, v, _ in CHECKS if v}
        report = evaluate(evidence)
        self.assertEqual(report['puntos_verificados'], 80)
        self.assertEqual(report['puntos_sin_probar'], 20)
        self.assertIn('NO equivale', markdown(report))

    def test_failure_is_not_untested_or_passed(self):
        report = evaluate({'MATICK_TEST_CHAT': 'failure',
                           'MATICK_TEST_API': 'success',
                           'MATICK_TEST_DX12': 'skipped'})
        self.assertEqual(report['puntos_verificados'], 15)
        self.assertEqual(report['puntos_fallidos'], 10)
        self.assertEqual(report['puntos_sin_probar'], 75)
        self.assertEqual(report['cobertura_de_pruebas'], 25)
        self.assertEqual(sum(c['peso'] for c in report['checks']), 100)


if __name__ == '__main__':
    unittest.main()
