from setuptools import setup

import pypandoc

setup(
    name='dbschema',
    version='1.4.3',
    description='Schema migration made easy',
    long_description=pypandoc.convert_file('README.md', 'rst'),
    author='Gabriel Bordeaux',
    author_email='pypi@gab.lc',
    url='https://github.com/gabfl/dbschema',
    license='MIT',
    packages=['dbschema'],
    package_dir={'dbschema': 'src'},
    install_requires=['argparse', 'PyYAML', 'pymysql',
                      'psycopg2-binary'],  # external dependencies
    entry_points={
        'console_scripts': [
            'dbschema = dbschema.schema_change:main',
        ],
    },
    classifiers=[  # see https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Topic :: Database',
        'Topic :: Database :: Database Engines/Servers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Natural Language :: English',
        #  'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        #  'Development Status :: 5 - Production/Stable',
    ],
)
