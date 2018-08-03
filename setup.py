#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup function for the package."""

from setuptools import setup

setup(
  name='gbj_pythonlib_sw',
  version='1.0.0',
  description='Python libraries for software support.',
  long_description='Modules suitable for whatever python console application.',
  classifiers=[
    'Development Status :: 4 - Beta',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 2.7',
    'Topic :: System :: Monitoring',
  ],
  keywords='configuration, mqtt, trigger, timer, statistics, filter',
  url='http://github.com/mrkalePythonLib/gbj_pythonlib_sw',
  author='Libor Gabaj',
  author_email='libor.gabaj@gmail.com',
  license='MIT',
  packages=['gbj_pythonlib_sw'],
  install_requires=['paho-mqtt'],
  include_package_data=True,
  zip_safe=False
)
