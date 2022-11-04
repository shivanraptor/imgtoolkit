from setuptools import setup, find_packages

VERSION = '0.0.6'
DESCRIPTION = 'Image tools for checking photos for blur and duplicates'
LONG_DESCRIPTION = 'An image tool Python package for checking photos for blur and duplicates'

setup(
        name='imgtoolkit',
        version=VERSION,
        author="Raptor K",
        author_email='findme' '@' 'raptor.hk',
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        url='https://github.com/shivanraptor/imgtoolkit',
        packages=find_packages(),
        install_requires=['dhash', 'alive-progress', 'Pillow', 'opencv-python', 'about-time', 'grapheme'],

        keywords=['image', 'find duplicate', 'find blur'],
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Programming Language :: Python :: 3",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
            "License :: OSI Approved :: MIT License",
        ]
)
