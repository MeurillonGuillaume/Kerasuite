from setuptools import find_packages, setup

setup(
    name='Kerasuite',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask==1.1.1',
        'numpy==1.18.1',
        'pandas==1.0.1',
        'passlib==1.7.1',
        'bcrypt==3.1.7',
        'pickledb==0.9.2',
        'Werkzeug==0.15.2',
        'tensorflow==2.1.0'
    ],
)

# Initialise the database
import pickledb

db = pickledb.load('Kerasuite.db', True)
# Add administrator user
db.set('users', {"admin": {"password": "$2b$12$F5t/lNpjbvGMh0m56t1xbe/saHiK.dHKIKif1Q.xOyxcbrr/vKAw."}})
