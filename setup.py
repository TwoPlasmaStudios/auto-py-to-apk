from setuptools import setup, find_packages

setup(
    name="auto-py-to-apk",
    version="2.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["flask", "werkzeug"],
    entry_points={
        "console_scripts": [
            "auto-py-to-apk=auto_py_to_apk.cli:main",
        ]
    },
)