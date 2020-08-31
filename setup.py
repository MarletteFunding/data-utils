from setuptools import setup, find_packages

requires = [
    "python-dotenv",
    "pysftp",
    "sendgrid",
    "slackclient",
    "snowflake-connector-python",
]

setup(
    name="data-utils",
    version="0.1.1",
    url="https://github.com/MarletteFunding/data-utils",
    author="Marlette Data Team",
    author_email="data-team@bestegg.com",
    description="Shared data team utilities.",
    install_requires=requires,
    dependency_links=["https://pypi.fury.io/TAeHp1T6JhyNRkPiK3xt/marlettefunding/",],
    packages=find_packages(),
)
