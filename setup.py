#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools.command.install_lib import install_lib as _install_lib
from setuptools import setup, find_packages

class install_lib(_install_lib):
    def run(self):
        _install_lib.run(self)

setup(
    name='passerelle-imio-ia-tech',
    author='Christophe Boulanger',
    author_email='christophe.boulanger@imio.be',
    url='https://github.com/IMIO/passerelle-imio-ia_tech',
    packages=find_packages(),
    install_requires=['passerelle',],
    cmdclass={
        'install_lib': install_lib,
    }
)
