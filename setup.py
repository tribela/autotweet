import os.path
import sys
from autotweet import __version__ as version

try:
    from setuptools import find_packages, setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import find_packages, setup


def readme():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
            return f.read()
    except (IOError, OSError):
        return ''


install_reqs = [
    'sqlalchemy>=0.9.6',
    'tweepy>=2.3.0',
]
extra_reqs = {
    'telegram': [
        'python-telegram-bot>=5.2.0',
    ],
}
if sys.version_info < (3, 2):
    install_reqs.append('futures')


setup(
    name='autotweet',
    version=version,
    description='learn your tweet and auto tweet it.',
    long_description=readme(),
    url='https://github.com/Kjwon15/autotweet/',
    download_url='https://github.com/Kjwon15/autotweet/releases',
    author='Kjwon15',
    author_email='kjwonmail' '@' 'gmail.com',
    license='MIT',
    entry_points={
        'console_scripts': [
            'autotweet = autotweet.command:main'
        ]
    },
    packages=find_packages(exclude=['tests']),
    install_requires=install_reqs,
    extras_require=extra_reqs,
    tests_require=['pytest >= 2.4.0'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: No Input/Output (Daemon)',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Communications :: Chat',
        'Topic :: Utilities',
    ]
)
