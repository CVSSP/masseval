from setuptools import setup, find_packages

with open('README.rst') as file:
    long_description = file.read()

setup(
    name='mass_eval',
    version='0.1',
    description='Evaluation of musical audio source separation techniques.',
    author='Dominic Ward, Hagen Wierstorf',
    author_email='dw0031@surrey.ac.uk',
    url='',
    packages=find_packages(),
    long_description=long_description,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        'Development Status :: 5 - Production/Stable',
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
    ],
    keywords='audio music bss mushra',
    license='MIT',
    install_requires=[
        'pandas',
        'numpy',
        'untwist >= 0.1.dev0',
        'lxml'
    ],
    extras_require={
        'display': ['matplotlib>=1.5.0',
                    'seaborn']
    }
)
