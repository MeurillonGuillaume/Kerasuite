from setuptools import find_packages, setup

setup(
    name='Kerasuite',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask==1.1.1',
        'numpy==1.16.3',
        'pandas==0.24.2',
        'passlib==1.7.1',
        'bcrypt==3.1.7'
    ],
)
