import sys

from setuptools import find_packages
from setuptools import setup

version = "1.0.5"

setup(
    name='passerelle-imio-ia-tech',
    version=version,
    author='iA.Téléservices',
    author_email='support-ts@imio.be',
    url='https://github.com/IMIO/passerelle-imio-ia_tech',
    packages=find_packages(),
    classifiers=[
        "Environment :: Web Environment",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
    ],
    install_requires=[
        "django>=2.2",
    ],
    zip_safe=False,
)
