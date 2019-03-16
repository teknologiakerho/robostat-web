from setuptools import setup

setup(
        name = "robostat3-web",
        version = "0.1",
        packages = [
            "robostat.web",
        ],
        install_requires = [
            "robostat3-core",
            "sqlalchemy",
            "flask"
        ]
)
