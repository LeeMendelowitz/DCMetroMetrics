from setuptools import setup

setup(name='MetroEscalators', version='1.0',
      description='WMATA Escalator Data',
      author='Lee Mendelowitz', author_email='MetroEscalators@gmail.com',
      url='http://www.python.org/sigs/distutils-sig/',
      #  Uncomment one or more lines below in the install_requires section
      #  for the specific client drivers/modules your application needs.
      install_requires=[
                           'setuptools==0.6c11',
                           'greenlet',
                           'gevent',
                           'requests',
                        #  'MySQL-python',
                        #  'psycopg2',
                           'python-dateutil==1.5',
                        #  'tweepy',
                           'oauth2',
                           'pymongo',
                           'simplejson',
                           'httplib2',
                           #'python-twitter',
                           'bottle'
      ],
     )
