import unittest
from coc_advisor.strategy import compare_strategies


class StrategyTests(unittest.TestCase):
    def test_unchosen_strategy_does_not_receive_reward(self):
        rows=[{'chosen':'east','actual_destruction':100,'predictions':{'west':100},'verified':True,'domain':'2:basic'}]
        report=compare_strategies(rows)
        self.assertEqual(report['east']['count'],1); self.assertNotIn('west',report)
    def test_guesses_and_unverified_results_do_not_count(self):
        self.assertEqual(compare_strategies([{'chosen':'east','prediction':100,'verified':False,'domain':'2:basic'}]),{})
