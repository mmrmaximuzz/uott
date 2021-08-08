import setuptools


setuptools.setup(
    name="uott",
    version="0.1.0",
    author="Maxim Petrov",
    author_email="mmrmaximuzz@gmail.com",
    description="UDP Over TCP Tunneling",
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
)
