import unittest
from coc_advisor.prediction import predict, validate_model


class PredictionTests(unittest.TestCase):
    def model(self):
        return dict(schema_version=1,model_id='m',feature_names=['x'],mean=[1],scale=[2],
                    weights=[10],intercept=50,domains=['2:barbarians'])
    def test_unknown_model_or_domain_abstains(self):
        self.assertIsNone(predict({'x':3,'domain':'2:barbarians'},None)['expected_destruction'])
        self.assertIsNone(predict({'x':3,'domain':'13:dragons'},self.model())['expected_destruction'])
    def test_numeric_export_serves_scaled_prediction(self):
        self.assertEqual(predict({'x':3,'domain':'2:barbarians'},self.model())['expected_destruction'],60)
        self.assertEqual(predict({'x':300,'domain':'2:barbarians'},self.model())['expected_destruction'],100)
    def test_invalid_or_missing_features_never_become_zero(self):
        for x in [float('nan'),True,None]:
            self.assertIsNone(predict({'x':x,'domain':'2:barbarians'},self.model())['expected_destruction'])
        m=self.model(); m['scale']=[0]
        with self.assertRaises(ValueError): validate_model(m)
