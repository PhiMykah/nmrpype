from setuptools import setup,find_packages

setup(name='nmrPype',
    version='0.8.1',
    packages=find_packages(), 
    install_requires=[
        'numpy',
        'scipy'
    ],
    entry_points={
        'console_scripts': [
            'nmrPype = nmrPype.pype:main',
        ]
    },
    author='Micah Smith',
    author_email='mykahsmith21@gmail.com',
    description='Python implementation of Nuclear Magnetic \
                Resonance (NMR) signal analysis program \'nmrPipe\''
)
