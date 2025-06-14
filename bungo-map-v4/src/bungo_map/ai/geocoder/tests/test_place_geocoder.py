import unittest
from unittest.mock import MagicMock, patch
from bungo_map.ai.geocoder.place_geocoder import PlaceGeocoder, GeocoderConfig

class TestPlaceGeocoder(unittest.TestCase):
    def setUp(self):
        self.config = GeocoderConfig(
            api_key="test_key",
            region="jp",
            language="ja",
            batch_size=10,
            retry_count=3,
            retry_delay=1
        )
        self.test_places = [
            {
                "name": "東京",
                "type": "city",
                "context": "東京都"
            },
            {
                "name": "大阪",
                "type": "city",
                "context": "大阪府",
                "latitude": 34.6937,
                "longitude": 135.5023
            },
            {
                "name": "名古屋",
                "type": "city",
                "context": "愛知県"
            }
        ]

    @patch('googlemaps.Client')
    def test_basic_geocoding(self, mock_client):
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        mock_instance.geocode.side_effect = [
            [{
                'geometry': {
                    'location': {
                        'lat': 35.6895,
                        'lng': 139.6917
                    }
                }
            }],
            [{
                'geometry': {
                    'location': {
                        'lat': 35.1815,
                        'lng': 136.9066
                    }
                }
            }]
        ]

        geocoder = PlaceGeocoder(self.config)
        geocoded = geocoder.geocode_places(self.test_places)

        self.assertEqual(len(geocoded), 3)

        tokyo = next(p for p in geocoded if p["name"] == "東京")
        self.assertEqual(tokyo["latitude"], 35.6895)
        self.assertEqual(tokyo["longitude"], 139.6917)
        self.assertEqual(tokyo["geocoding_confidence"], 0.9)
        self.assertEqual(tokyo["geocoding_source"], "google_maps")

        osaka = next(p for p in geocoded if p["name"] == "大阪")
        self.assertEqual(osaka["latitude"], 34.6937)
        self.assertEqual(osaka["longitude"], 135.5023)

        nagoya = next(p for p in geocoded if p["name"] == "名古屋")
        self.assertEqual(nagoya["latitude"], 35.1815)
        self.assertEqual(nagoya["longitude"], 136.9066)
        self.assertEqual(nagoya["geocoding_confidence"], 0.9)
        self.assertEqual(nagoya["geocoding_source"], "google_maps")

    @patch('googlemaps.Client')
    def test_coordinate_validation(self, mock_client):
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        mock_instance.geocode.return_value = [{
            'geometry': {
                'location': {
                    'lat': 200.0,
                    'lng': 139.6917
                }
            }
        }]

        geocoder = PlaceGeocoder(self.config)
        geocoded = geocoder.geocode_places([self.test_places[0]])

        self.assertEqual(len(geocoded), 0)

    @patch('googlemaps.Client')
    def test_api_error_handling(self, mock_client):
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        mock_instance.geocode.side_effect = Exception("API Error")

        geocoder = PlaceGeocoder(self.config)
        # 例外がraiseされず、失敗カウントが増えることを確認
        result = geocoder.geocode_places([self.test_places[0]])
        self.assertEqual(len(result), 0)
        self.assertEqual(geocoder.stats['failed_geocoding'], 1)

    @patch('googlemaps.Client')
    def test_stats_display(self, mock_client):
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        geocoder = PlaceGeocoder(self.config)
        geocoder.stats = {
            'total_places': 10,
            'successful_geocoding': 8,
            'failed_geocoding': 2,
            'api_calls': 10,
            'retries': 1
        }
        with patch('rich.console.Console.print') as mock_print:
            geocoder.display_stats()
            mock_print.assert_called_once()
