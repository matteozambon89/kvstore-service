from server.core import app
from flask import request

@app.route("/echo", methods=["GET", "POST"])
def echo_view():
    print("called echo")
    return str(request.headers.items())
