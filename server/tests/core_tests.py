import uuid
import unittest
from server.core import *

class TestFixture(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_response_header_has_hostname(self):
        response = self.app.get("/diagnostic")
        self.assertTrue('X-HOSTNAME' in response.headers)
        self.assertTrue(response.headers['X-HOSTNAME']) 

    def test_echo(self):
        response = self.app.get("/echo?something=k")
        self.assertEqual(200, response.status_code)

    def test_fail_json_formatted_response(self):
        previous_prop = app.config['PROPAGATE_EXCEPTIONS']
        app.config['PROPAGATE_EXCEPTIONS'] = False
        response = self.app.get("/diagnostic/fail", content_type='json')
        app.config['PROPAGATE_EXCEPTIONS'] = previous_prop
        self.assertEqual(500, response.status_code)
        self.assertTrue(json.loads(response.data))
        self.assertTrue("eid" in json.loads(response.data))
        self.assertEqual("application/json", response.content_type)
        
    def test_fail_html_formatted_response(self):
        previous_prop = app.config['PROPAGATE_EXCEPTIONS']
        app.config['PROPAGATE_EXCEPTIONS'] = False
        response = self.app.get("/diagnostic/fail")
        app.config['PROPAGATE_EXCEPTIONS'] = previous_prop
        self.assertEqual(500, response.status_code)
        # we only explicily set application/json so we'll be expecting
        # flask to chose the right one
        self.assertTrue("text/html" in  response.content_type)

    def test_head_root_health_check(self):
        response = self.app.get("/")
        self.assertTrue(200, response.status_code)

    def test_callback(self):
        response = self.app.get("/diagnostic/echo?callback=run_me&bare=true")
        self.assertEqual('run_me({"bare": "true"});', response.data)
        self.assertEqual('application/javascript', response.content_type)
    
    def test_callback_alone(self):
        response = self.app.get("/diagnostic/echo?callback=run_me")
        self.assertEqual('run_me({});', response.data);

    def test_no_callback(self):
        response = self.app.get("/diagnostic/echo?bare=true")
        self.assertEqual('{"bare": "true"}', response.data);

    @app.route("/test_me", methods=["GET"])
    def im_here_for_documentation():
        """ this is my documentation for this endpoint

            :statuscode 200: returned if everything is ok
            :statuscode 500: returned if nothing is ok
        """

        return "this is a test response"

    def test_can_find_view_from_handler_file(self):
        response = self.app.get("/test_me")
        self.assertEqual("this is a test response", response.data)

    def test_view_returning_none_gets_handled_in_json_response(self):
        @app.route("/return_null", methods=["GET"])
        @make_my_response_json
        def null_view():
            return None

        response = self.app.get("/return_null")
        self.assertEqual(200, response.status_code)
        jr = json.loads(response.data)
        self.assertEqual({}, jr)

    def test_view_returning_dict_with_callback_in_request(self):
        @app.route("/bad_callback", methods=["GET"])
        @make_my_response_json
        def null_view():
            return dict(pants="blue")

        response = self.app.get("/bad_callback?callback=run_me")
        self.assertEqual(200, response.status_code)
        self.assertEqual('run_me({"pants": "blue"});', response.data)

    def test_static_works_at_all(self):
        if not os.path.exists("./static/"):
            os.makedirs("./static/")
        with open("./static/core_test_index.html", "w+") as sf:
            sf.write("I'm static!")
        response = self.app.get("/static/core_test_index.html")
        self.assertEqual(200, response.status_code)
        self.assertEqual("I'm static!", response.data.strip())
        if os.path.exists("./static/core_test_index.html"):
            os.unlink("./static/core_test_index.html")

    def test_convert_dictionary_simple(self):
        converted = convert_types_in_dictionary(dict(myint="1", myfloat="1.3"))
        self.assertEqual(1, converted['myint'])
        self.assertEqual(1.3, converted['myfloat'])
    
    @app.route("/convert", methods=["GET", "POST"])
    @make_my_response_json
    def convert():
        d = request.values.to_dict(flat=False)
        ret_val = convert_types_in_dictionary(remove_single_element_lists(d))
        return ret_val

    def test_convert_dictionary_request(self):
        response = self.app.get("/convert?myint=1&myfloat=1.3")
        self.assertEqual(200, response.status_code)
        converted = json.loads(response.data)
        self.assertEqual(1, converted['myint'])
        self.assertEqual(1.3, converted['myfloat'])

    def test_convert_dictionary_request_multiple(self):
        response = self.app.post("/convert?myint=2&myint=4")
        self.assertEqual(200, response.status_code)
        converted = json.loads(response.data)
        self.assertEqual([2,4], converted['myint'])

    def test_convert_dictionary_nested(self):   
        converted = convert_types_in_dictionary(
            dict(myint="1", myfloat="1.3", child=dict(childint="3"))
        )
        self.assertEqual(1, converted['myint'])
        self.assertEqual(1.3, converted['myfloat'])
        self.assertEqual(3, converted['child']['childint'])

    def test_convert_dictionary_nested_list(self):   
        converted = convert_types_in_dictionary(
            dict(myzero="0", myint="1", myfloat="1.3", child=dict(childint="3"), childlist=["1", 2])
        )
        self.assertEqual(0, convert_into_number("0"))
        self.assertEqual(0, converted['myzero'])
        self.assertEqual(1, converted['myint'])
        self.assertEqual(1.3, converted['myfloat'])
        self.assertEqual(3, converted['child']['childint'])
        self.assertEqual([1,2], converted['childlist'])


    @app.route("/return_list", methods=["GET", "POST"])
    @make_my_response_json
    def return_list():
        return [1,2,3]

    def test_return_list_json(self):
        response = self.app.get("/return_list")
        self.assertEqual(200, response.status_code)
        jr = json.loads(response.data)
        self.assertEqual([1,2,3], jr)

    @app.route("/can_return_status", methods=["GET", "POST"])
    @make_my_response_json
    def return_int():
        return 503 

    def test_can_return_statuscode(self):
        response = self.app.get("/can_return_status")
        self.assertEqual(503, response.status_code)

    @app.route("/can_return_raw_json_string", methods=["GET", "POST"])
    @make_my_response_json
    def return_raw_json_string():
        return '{"one": 1}'

    def test_raw_json_string_returns(self):
        response = self.app.get("/can_return_raw_json_string")
        self.assertEqual(200, response.status_code)
        print(("!%s!" % (response.data)))
        jr = json.loads(response.data)
        self.assertTrue(jr)
        self.assertEqual(1, jr['one'])

    @app.route("/no_json_404")
    @make_my_response_json
    def return_404():
        return dict(message="pants", status_code=404)

    def test_404_for_json_response(self):
        response = self.app.get("/no_json_404")
        self.assertEqual(404, response.status_code)
        self.assertEqual(dict(message="pants"), json.loads(response.data))

    def test_no_404_for_JSONP_response(self):
        response = self.app.get("/no_json_404?callback=mo")
        self.assertEqual(200, response.status_code)

    @app.route("/json_endpoint_with_string_response")
    @make_my_response_json
    def string_response():
        return "this is a string";

    def test_return_string_from_json_view_using_jsonp(self):
        response = self.app.get("/json_endpoint_with_string_response?callback=pants")
        self.assertEqual(200, response.status_code)
        self.assertEqual('pants("this is a string");', response.data)
        self.assertEqual('application/javascript', response.content_type)

    def test_return_string_from_json_view(self):
        response = self.app.get("/json_endpoint_with_string_response")
        self.assertEqual(200, response.status_code)
        self.assertEqual('this is a string', response.data)
        self.assertEqual('application/json', response.content_type)
