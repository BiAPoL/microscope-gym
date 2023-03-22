import setuptools
setuptools.setup(
    name="microscope_gym",
    version="0.0.1",
    author="Till Korten",
    author_email="webmaster@korten.at",
    description="An interface for smart microscope control",
    license="BSD-3-Clause",
    packages=setuptools.find_packages(exclude=["docs"]),
    include_package_data=True,
    install_requires=["numpy"],
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Development Status :: 3 - Alpha",
    ],
)
