#    Copyright (c) 2023-2025 Rich Bell <bellrichm@gmail.com>
#    See the file LICENSE.txt for your full rights.

# pylint: disable=missing-docstring

import unittest

import user.aqitype

class TestAQISearchList(unittest.TestCase):
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


    def test_get_aqi_description_epa(self):
        searchlist = user.aqitype.AQISearchList({})
        self.assertEqual(searchlist.get_aqi_description(0.0, 'EPAAQI'), 'aqi_EPAAQI_description1')
        self.assertEqual(searchlist.get_aqi_description(25.0, 'EPAAQI'), 'aqi_EPAAQI_description1')
        self.assertEqual(searchlist.get_aqi_description(75.0, 'EPAAQI'), 'aqi_EPAAQI_description2')
        self.assertEqual(searchlist.get_aqi_description(125.0, 'EPAAQI'), 'aqi_EPAAQI_description3')
        self.assertEqual(searchlist.get_aqi_description(175.0, 'EPAAQI'), 'aqi_EPAAQI_description4')
        self.assertEqual(searchlist.get_aqi_description(250.0, 'EPAAQI'), 'aqi_EPAAQI_description5')
        self.assertEqual(searchlist.get_aqi_description(350.0, 'EPAAQI'), 'aqi_EPAAQI_description6')
        self.assertEqual(searchlist.get_aqi_description(450.0, 'EPAAQI'), 'aqi_EPAAQI_description6')
        self.assertEqual(searchlist.get_aqi_description(6050.0, 'EPAAQI'), 'aqi_EPAAQI_description6')

if __name__ == '__main__':
    unittest.main(exit=False)
