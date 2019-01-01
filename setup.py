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
        'b2',
        'PyYAML',
        'rauth',
        'requests',
        'requests_oauthlib'
    ],
    entry_points = {
        'console_scripts': [
            'smugmug-to-b2=smugmug_to_b2.command_line:main',
        ],
    },
)
