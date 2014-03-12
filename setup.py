from setuptools import setup

packages = ['dcmetrometrics',
          'dcmetrometrics.common',
          'dcmetrometrics.eles',
          'dcmetrometrics.hotcars',
          'dcmetrometrics.keys',
          'dcmetrometrics.test',
          'dcmetrometrics.third_party',
          'dcmetrometrics.web']

setup(name='DC Metro Metrics',
      version='1.1',
      description='Collecting and sharing public data related to the DC WMATA Metrorail system.',
      author='Lee Mendelowitz',
      author_email='Lee.Mendelowitz@gmail.com',
      url='https://github.com/LeeMendelowitz/DCMetroMetrics',
      #  Uncomment one or more lines below in the install_requires section
      #  for the specific client drivers/modules your application needs.
      install_requires=[   'greenlet',
                           'gevent',
                           'requests',
                           'python-dateutil==1.5',
                           'oauth2',
                           'pymongo',
                           'simplejson',
                           'httplib2',
                           'bottle',
                           'mongoengine'
      ],
      packages = []
 )
