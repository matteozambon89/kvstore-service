import uuid
import unittest
from pyserver.core import *

class CacheTestFixture(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        self.app_cache = app.config['_CACHE']
        self.app.debug = True

    @app.route("/cache_test", methods=["GET", "POST"])
    @cache_my_response(vary_by=['vary_key', 'vary_key2'])
    def random_stuff():
        return str(uuid.uuid4())
    @app.route("/nv_cache_test", methods=["GET"])
    @cache_my_response()
    def nv_random_stuff():
        return str(uuid.uuid4())

    def test_cached_view_returns_cached_response(self):
        first_response = self.app.get("/nv_cache_test")
        self.assertEquals(200, first_response.status_code)
        second_response = self.app.get("/nv_cache_test")
        self.assertEquals(200, second_response.status_code)
        self.assertEquals(first_response.data, second_response.data)

    def test_cached_view_response_sets_header(self):
        response = self.app.get("/nv_cache_test")
        response = self.app.get("/nv_cache_test")
        self.assertTrue('Expires' in response.headers)

    def test_uncached_view_response_has_no_header(self):
        response = self.app.get("/nv_cache_test?_reload_cache=1")
        self.assertTrue(not 'Expires' in response.headers)

    def test_cached_view_returns_uncached_with_no_vary_and_force(self):
        first_response = self.app.get("/nv_cache_test?_reload_cache=1")
        self.assertEquals(200, first_response.status_code)
        second_response = self.app.get("/nv_cache_test?_reload_cache=1")
        self.assertEquals(200, second_response.status_code)
        self.assertNotEquals(first_response.data, second_response.data)

    def test_cached_view_returns_uncached_response_by_vary(self):
        first_response = self.app.get("/cache_test?vary_key=1")
        self.assertEquals(200, first_response.status_code)
        second_response = self.app.get("/cache_test?vary_key=2")
        self.assertEquals(200, second_response.status_code)
        self.assertNotEquals(first_response.data, second_response.data)

    def test_cached_view_returns_uncached_response_by_either_vary(self):
        first_response = self.app.get("/cache_test?vary_key=1")
        self.assertEquals(200, first_response.status_code)
        second_response = self.app.post("/cache_test?vary_key2=1")
        self.assertEquals(200, second_response.status_code)
        self.assertNotEquals(first_response.data, second_response.data)

    def test_cached_view_returns_cached_with_same_vary(self):
        first_response = self.app.get("/cache_test?vary_key=1")
        self.assertEquals(200, first_response.status_code)
        second_response = self.app.get("/cache_test?vary_key=1")
        self.assertEquals(200, second_response.status_code)
        self.assertEquals(first_response.data, second_response.data)

    def test_cached_view_returns_uncached_with_force(self):
        first_response = self.app.get("/cache_test?vary_key=1")
        self.assertEquals(200, first_response.status_code)
        second_response = self.app.get("/cache_test?vary_key=1&_reload_cache=1")
        self.assertEquals(200, second_response.status_code)
        self.assertNotEquals(first_response.data, second_response.data)

    def test_cached_response_handles_non_string_response(self):
        @app.route("/ns_cache_test")
        @cache_my_response()
        def ns_return():
            return "<xml></xml>", 200, {'Content-Balls': 'text/xml'}
        first_response = self.app.get("/ns_cache_test")
        second_response = self.app.get("/ns_cache_test")
        self.assertEquals(200, second_response.status_code)
        self.assertEquals("<xml></xml>", second_response.data)
        self.assertEquals("text/xml", second_response.headers['Content-Balls'])
        self.assertTrue('Expires' in second_response.headers)
