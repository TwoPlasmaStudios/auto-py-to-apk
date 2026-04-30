import os
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="py2apk",
    version="0.1.0",
    author="Twoplasma Studios",
    description="Python kodunu tek tıkla APK'ya dönüştür. Docker'sız, QEMU build motoruyla.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/twoplasmastudios/auto-py-to-apk",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
    ],
    keywords="python apk android packager build qemu",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "py2apk=py2apk.main:main",
            "auto-py-to-apk=py2apk.main:main",
        ],
    },
    include_package_data=True,
)