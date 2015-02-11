#!/usr/bin/env python
"""
Generate a sitemap.xml file for dc metro metrics
and a json file with an array of urls.

The json file is used with grunt in order to crawl dcmetrometrics.com and regenerate
the static version of the site.
"""

from dcmetrometrics.eles import models as models_eles
from dcmetrometrics.hotcars import models as models_hotcars
import sys

#######################
# Set up logging
import logging
sh = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SiteMapGenerator')
logger.setLevel(logging.DEBUG)
logger.addHandler(sh)
#######################

URL_ROOT = 'http://localhost:80'

def unit_urls():
  logger.info("Generating Unit URLS...")
  units = models_eles.Unit.objects
  return ['{URL_ROOT}/unit/%s'%(unit.unit_id) for unit in units]

def hotcar_urls():
  logger.info("Generating HotCar URLS...")
  hotcars = models_hotcars.HotCarReport.objects
  return list(set(['{URL_ROOT}/hotcars/detail/%s'%(h.car_number) for h in hotcars]))

def station_urls():
  logger.info("Generating Station URLS...")  
  stations = models_eles.Station.objects
  short_names = set(s.short_name for s in stations)
  return ['{URL_ROOT}/stations/detail/%s'%(s) for s in short_names]

def main_urls():
  logger.info("Generating Main URLS...")
  pages = ['home', 'stations/list', 'about', 'outages', 'rankings', '']
  return ['{URL_ROOT}/%s'%(p) for p in pages]

URLS = unit_urls() + hotcar_urls() + station_urls() + main_urls()


def make_site_map(output_file_name, URL_ROOT = URL_ROOT):
  import xml.etree.ElementTree as ET
  urls = [u.format(URL_ROOT = URL_ROOT) for u in URLS]
  urlset_node = ET.Element('urlset')
  urlset_node.set('xmlns',  'http://www.sitemaps.org/schemas/sitemap/0.9')
  tree = ET.ElementTree(urlset_node)

  for url in urls:
    url_node = ET.SubElement(urlset_node, 'url')
    loc_node = ET.SubElement(url_node, 'loc')
    loc_node.text = url
    changefreq_node = ET.SubElement(url_node, 'changefreq')
    changefreq_node.text = 'daily'

  with open(output_file_name, 'w') as fout:
    tree.write(fout, encoding="utf-8", xml_declaration = True)

def write_url_json(output_file_name, URL_ROOT = URL_ROOT):
  import json
  urls = [u.format(URL_ROOT = URL_ROOT) for u in URLS]
  with open(output_file_name, 'w') as fout:
    json.dump(urls, fout)

if __name__ == "__main__":
  #make_site_map('sitemap.xml', URL_ROOT='http://www.dcmetrometrics.com')
  write_url_json('site_urls.json', URL_ROOT='')





