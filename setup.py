from setuptools import setup, find_packages

VERSION = '0.1.1'
DESCRIPTION = 'Collection of image tools for checking photos for blur and duplicates, and handle fake PNG transparency'
LONG_DESCRIPTION = 'A collection of image tools for checking photos for blur and duplicates, and handle fake PNG transparency'

setup(
        name='imgtoolkit',
        version=VERSION,
        python_requires='>3.8.0',
        author="Raptor K",
        author_email='findme' '@' 'raptor.hk',
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        url='https://github.com/shivanraptor/imgtoolkit',
        packages=find_packages(),
        install_requires=['dhash', 'alive-progress', 'Pillow', 'opencv-python', 'about-time', 'grapheme'],
        entry_points = {
            'console_scripts': [
                'imgtoolkit = imgtoolkit.tools:main'
            ]
        },
        keywords=['image', 'find duplicate', 'find blur', 'fake png'],
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Programming Language :: Python :: 3",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
            "License :: OSI Approved :: MIT License",
        ]
)
