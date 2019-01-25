import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='jwt_authenticator',
    version='0.1',
    author="Mike Nacey",
    author_email="nobody@teletracking.com",
    description="Simple JWT token flask service security library.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/javatechy/dokr",
    packages=['jwt_authenticator'],
    install_requires=['Flask', 'python-jose'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
