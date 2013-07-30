import sys
from setuptools import setup, find_packages

setup(
    name = "expressions",
    version = "0.1",

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
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
        'Topic :: Utilities'
    ],

    # metadata for upload to PyPI
    author = "Stefan Urbanek",
    author_email = "stefan.urbanek@gmail.com",
    description = "Simple abstract parser for arithmetic expressions with slightly customizable syntax. Provides mechanisms for custom execution or compilation into custom structures.",
    license = "MIT license",
    keywords = "arithmetic expression",
    url = "http://databrewery.org"

)
