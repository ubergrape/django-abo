# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name='django-abo',
    version='0.1.3',
    description='Recurring payment / subscription handling for Django, supporting different payment gateways',
    url='https://github.com/ubergrape/django-abo',
    author='Stefan Kröner',
    author_email='sk@ubergrape.com',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    zip_safe=False,
    platforms=["any"],
    install_requires=[
        'django >= 1.6',
        'pymill',
        'requests'
    ],
    tests_require=[
        'factory-boy >= 2.3.0',
        'requests'
    ]
)
