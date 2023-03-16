import setuptools

version = {}
with open("ultrasonic_matrix/version.py") as fp:
    exec(fp.read(), version)

setuptools.setup(name='ultrasonic_matrix',
    version=version['__version__'],
    description='Software interface for ultrasonic transducer matrix',
    url='#',
    author='Andrew Palmer',
    install_requires=[''],
    author_email='',
    packages=setuptools.find_packages(),
    zip_safe=False
)