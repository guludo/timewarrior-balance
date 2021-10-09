import pathlib

import setuptools


setuptools.setup(
    name='timewarrior-balance',
    version='0.1.0',
    url='https://github.com/guludo/timewarrior-balance',
    description='Get a balance of your timewarrior hours',
    long_description=(pathlib.Path(__file__).parent / 'README.rst').read_text(),
    long_description_content_type='text/x-rst',
    packages=['timewarrior_balance'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
    keywords='timewarrior',
)
