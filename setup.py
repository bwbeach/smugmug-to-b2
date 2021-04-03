#
# File: setup.py
#

from setuptools import setup

setup(
    name='smugmug_to_b2',
    description='Backs up Smugmug photos to Backblaze B2',
    license='MIT',
    url='https://github.com/bwbeach/smugmug-to-b2',
    packages=['smugmug_to_b2'],
    include_package_data=False,
    install_requires=[
        'b2sdk',
        'PyYAML',
        'rauth',
        'requests',
        'requests_oauthlib'
    ],
    tests_require=[
        'pytest'
    ],
    entry_points = {
        'console_scripts': [
            'smugmug-to-b2=smugmug_to_b2.command_line:main',
        ],
    },
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
    ],
)
