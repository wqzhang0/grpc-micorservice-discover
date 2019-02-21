from distutils.core import setup

from setuptools import find_packages

setup(name='grpc-micorservice-discover',
      version='0.0.3',
      description='Service registration discovery by etcd3',
      long_description=open('README.md').read(),
      author='wqzhang',
      author_email='wqzhang0@163.com',
      url='https://github.com/wqzhang0',
      packages=find_packages(),
      install_requires=[
          'etcd3==0.8.1',
          'grpcio==1.18.0',
          'grpcio-tools==1.18.0',
          'simplejson==3.16.0',
      ],
      classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
      ],
      )
