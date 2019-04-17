from setuptools import setup

setup(
        name = "robostat3-web",
        version = "0.1",
        packages = [
            "robostat.web",
        ],
        install_requires = [
            "robostat3-core @ https://github.com/teknologiakerho/robostat-core/tarball/master",
            "sqlalchemy",
            "flask"
        ],
        extras_require = {
            "dev": [
                "pytest",
                "pttt @ https://github.com/vfprintf/pttt/tarball/master"
            ]
        }
)
