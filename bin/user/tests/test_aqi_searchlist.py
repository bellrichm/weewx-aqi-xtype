# pylint: disable=missing-docstring

import unittest

import user.aqitype

class AQISearchListTests(unittest.TestCase):
    def test_get_aqi_color_epa(self):
        searchlist = user.aqitype.AQISearchList({})
        self.assertEqual(searchlist.get_aqi_color(0.0, 'EPAAQI'), '00e400')
        self.assertEqual(searchlist.get_aqi_color(25.0, 'EPAAQI'), '00e400')
        self.assertEqual(searchlist.get_aqi_color(75.0, 'EPAAQI'), 'ffff00')
        self.assertEqual(searchlist.get_aqi_color(125.0, 'EPAAQI'), 'ff7e00')
        self.assertEqual(searchlist.get_aqi_color(175.0, 'EPAAQI'), 'ff0000')
        self.assertEqual(searchlist.get_aqi_color(250.0, 'EPAAQI'), '8f3f97')
        self.assertEqual(searchlist.get_aqi_color(350.0, 'EPAAQI'), '7e0023')
        self.assertEqual(searchlist.get_aqi_color(450.0, 'EPAAQI'), '7e0023')
        self.assertEqual(searchlist.get_aqi_color(6050.0, 'EPAAQI'), '7e0023')


    def test_get_aqi_label_epa(self):
        searchlist = user.aqitype.AQISearchList({})
        self.assertEqual(searchlist.get_aqi_label(0.0, 'EPAAQI'), 'aqi_EPAAQI_label1')
        self.assertEqual(searchlist.get_aqi_label(25.0, 'EPAAQI'), 'aqi_EPAAQI_label1')
        self.assertEqual(searchlist.get_aqi_label(75.0, 'EPAAQI'), 'aqi_EPAAQI_label2')
        self.assertEqual(searchlist.get_aqi_label(125.0, 'EPAAQI'), 'aqi_EPAAQI_label3')
        self.assertEqual(searchlist.get_aqi_label(175.0, 'EPAAQI'), 'aqi_EPAAQI_label4')
        self.assertEqual(searchlist.get_aqi_label(250.0, 'EPAAQI'), 'aqi_EPAAQI_label5')
        self.assertEqual(searchlist.get_aqi_label(350.0, 'EPAAQI'), 'aqi_EPAAQI_label6')
        self.assertEqual(searchlist.get_aqi_label(450.0, 'EPAAQI'), 'aqi_EPAAQI_label7')
        self.assertEqual(searchlist.get_aqi_label(6050.0, 'EPAAQI'), 'aqi_EPAAQI_label7')

if __name__ == '__main__':
    unittest.main(exit=False)
