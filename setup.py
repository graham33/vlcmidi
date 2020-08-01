from setuptools import setup

setup(
    name='vlcmidi',
    version='0.1',
    py_modules=['vlcmidi'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        vlcmidi=vlcmidi:vlcmidi
    ''',
)
