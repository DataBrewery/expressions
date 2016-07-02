import sys
from setuptools import setup, find_packages

requirements = ['grako>=3.9.3']

setup(
    name = "expressions",
    version = "0.2.3",

    packages = find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst'],
    },

    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering',
        'Topic :: Utilities'
    ],

    install_requires = requirements,

    test_suite = "tests",

    # metadata for upload to PyPI
    author = "Stefan Urbanek",
    author_email = "stefan.urbanek@gmail.com",
    description = "Extensible arithmetic expression parser and compiler",
    license = "MIT license",
    keywords = "arithmetic expression",
    url = "http://databrewery.org"

)
