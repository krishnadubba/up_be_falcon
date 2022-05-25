# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


def read_file(filename):
    with open(filename, 'r') as infile:
        return infile.read()

requires = [
    "falcon==0.3.0",
    "Cython==0.22",
    "colander==1.0",
    "pymongo==2.8",
    "mongoengine==0.8.7",
    "gunicorn==18.0",
    "PyJWT==2.4.0",
]

extras_require = {
    "test": [
        "nose",
        "coverage",
        "flake8",
        "mock"
    ]
}

setup(name='uggipuggi',
      version='0.1.0',
      description='backend server for UggiPuggi',
      long_description=read_file('README.md'),
      author='dksr',
      author_email='dksreddy@gmail.com',
      keywords='web wsgi falcon restful japan',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='uggipuggi',
      install_requires=requires,
      extras_require=extras_require)
