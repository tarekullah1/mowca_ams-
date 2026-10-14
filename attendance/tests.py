from django.test import TestCase, Client
from django.db import connection
from django.test.utils import CaptureQueriesContext


class HealthCheckEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check_returns_200_ok(self):
        """GET /health/ must return HTTP 200 with {'status': 'ok'}."""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_health_check_no_authentication_required(self):
        """GET /health/ must be public and not require API key or auth headers."""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)

    def test_health_check_zero_database_queries(self):
        """GET /health/ must be lightweight and execute 0 database queries."""
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(queries), 0, f"Expected 0 queries, got {len(queries)}")

    def test_health_check_disallows_post(self):
        """POST /health/ must return 405 Method Not Allowed."""
        response = self.client.post('/health/')
        self.assertEqual(response.status_code, 405)

    def test_dashboard_renders_health_check_logic(self):
        """Dashboard page must render and contain health check script references."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('/health/', content)
        self.assertIn('90000', content)
        self.assertIn('initiateHealthCheck', content)
