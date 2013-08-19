"""
Module: dcmetrometrics

This python package defines classes/functions:
    - to pull WMATA data from the WMATA API and Twitter
    - to process and store this data in a MongoDB database
    - to generate the DC Metro Metrics website
    - to run the automated Twitter accounts @MetroHotCars, @MetroEscalators, @MetroElevators.

The package is organized as follows:
 - eles: package for escalator/elevator data
 - common: package for common utility classes/functions used throughout
           the application.
 - hotcars: package for #wmata #hotcar data
 - web: package for generating the DC Metro Metrics website
 - third_party: third party packages used by this application.
"""

from .common import *
