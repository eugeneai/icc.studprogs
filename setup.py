from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()


version = '0.1'

install_requires = [
    "pybison==0.1",
]

dependency_links = [
    'https://github.com/eugeneai/pybison/archive/master.zip#egg=pybison-0.1',
]

setup(name='icc.studprogs',
    version=version,
    description="Manage Study Working Programs by means of NLP",
    long_description=README + '\n\n' + NEWS,
    classifiers=[
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    keywords='NLP NLTK',
    author='Evgeny Cherkashin',
    author_email='eugeneai@irnok.net',
    url='',
    license='GPL',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    namespace_packages = ['icc'],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    dependency_links = dependency_links,
    entry_points={
        'console_scripts':
            ['icc.studprogs=icc.studprogs:main']
    }
)
