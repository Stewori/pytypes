import os.path

from setuptools import setup

here = os.path.dirname(__file__)
readme_path = os.path.join(here, 'README.rst')
readme = open(readme_path).read()

setup(
    name='pytypes',
    version='1.0b1',
    description='Typing toolbox for Python 3 _and_ 2.',
    long_description=readme,
    url='https://github.com/Stewori/pytypes',
    author='Stefan Richthofer',
    author_email='stefan.richthofer@jyni.org',
    license='Apache-2.0',
    packages=['pytypes'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    extras_require={
        ':python_version == "2.7"': 'typing'
    },
    entry_points={
        'console_scripts': [
            'typestubs = pytypes.stubfile_2_converter:main'
        ]
    }
)
