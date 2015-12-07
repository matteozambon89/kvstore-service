from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='kvstore-service',
    version='0.1.0',
    description='A HTTP based key/value storage service backed by Dynamo DB',
    long_description=long_description,
    url='https://github.com/igroff/kvstore-service',
    author='Ian Groff',
    author_email='',
    license='MIT',
    classifiers=[
        'Development Status :: 5',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7'
    ],
    keywords='http document storage key',
    install_requires=[
        'Werkzeug==0.8.3',
        'Flask==0.9',
        'gunicorn==0.17.2',
        'boto==2.36.0'
    ],
    entry_points={
        'console_scripts': ['kvstore-service=server:main']
    }
)


