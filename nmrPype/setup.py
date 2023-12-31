from setuptools import setup,find_packages

setup(name='nmrPype',
    version='0.2.0',
    packages=find_packages(), 
    install_requires=[
        'nmrglue',
        'numpy',
        'scipy'
    ],
    entry_points={
        'console_scripts': [
            'nmrPype = pypeMain:main',
        ]
    },
    author='Micah Smith',
    author_email='mykahsmith21@gmail.com',
    description='Python implementation of Nuclear Magnetic \
                Resonance (NMR) signal analysis program \'nmrPipe\''
)