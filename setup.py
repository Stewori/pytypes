from setuptools import setup

setup(
    name='pytypes',
    version='1.0b1',
    description='Typing toolbox for Python 3 _and_ 2.',
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
    }
)
