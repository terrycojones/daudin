#!/usr/bin/env python

from setuptools import setup


# Modified from http://stackoverflow.com/questions/2058802/
# how-can-i-get-the-version-defined-in-setup-py-setuptools-in-my-package and
# https://stackoverflow.com/questions/6786555/
# automatic-version-number-both-in-setup-py-setuptools-and-source-code#7502821

def version():
    import os
    import re

    init = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'daudinlib', '__init__.py')
    with open(init) as fp:
        initData = fp.read()
    match = re.search(r"^__version__ = ['\"]([^'\"]+)['\"]",
                      initData, re.M)
    if match:
        return match.group(1)
    else:
        raise RuntimeError('Unable to find version string in %r.' % init)


setup(name='daudin',
      version=version(),
      packages=['daudinlib'],
      include_package_data=False,
      url='https://github.com/terrycojones/daudin',
      download_url='https://github.com/terrycojones/daudin',
      author='Terry Jones',
      author_email='terry@jon.es',
      keywords=['python shell'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Programming Language :: Python :: 3 :: Only',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: POSIX :: Linux',
          'Operating System :: Unix',
          'Topic :: System :: Shells'
      ],
      license='MIT',
      scripts=['daudin'],
      description='A UNIX command-line shell based on Python',
      extras_require={
        'dev': [
            'flake8',
            'pytest',
        ]
      })
