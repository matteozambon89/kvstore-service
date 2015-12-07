import os
import logging
from argparse import ArgumentParser
from pyserver.core import app
from pyserver.core import handler_list

""" we should only get here for debugging and testing, as we're gonna
	use gunicorn for serving in production
"""
arg_parser = ArgumentParser(description="")
arg_parser.add_argument("-p", "--port", default=5000, type=int)
arg_parser.add_argument("--host", default="127.0.0.1")
arg_parser.add_argument("action", choices=('start', 'test', 'config'))
args = arg_parser.parse_args()
if args.action == "start":
	app.run(
		host=args.host,
		use_reloader=(app.config['USE_RELOADER'] == 'True'),
		debug=True,
		use_debugger=True,
		port=args.port,
		extra_files=handler_list)
elif args.action == "config":
	for key, value in app.config.items():
		print("%s: %s" % (key, value))
