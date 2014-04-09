from datetime import date, datetime, timedelta
from urlparse import parse_qsl
from collections import defaultdict
from mapreduce import operation
from mapreduce import base_handler
from mapreduce.lib import pipeline
import logging
import json
import webapp2
import os
from webapp2 import Route
import urllib2
from bs4 import BeautifulSoup
from django.utils.encoding import smart_str
import re
import urllib
import time
from google.appengine.api import taskqueue


class Create_product(webapp2.RequestHandler):
    def get(self):
        item_page = self.request.get('target')
        html = urllib2.urlopen(item_page).read()
        body = BeautifulSoup(html)
        title = smart_str(body.select("#trace_hid_name")[0].attrs.get('value'))
        price = int(re.match("\d+", body.select("[itemprop=price]")[0].attrs.get('content')).group())
        logging.info(price)
        logging.info(title)


class ParsePage(base_handler.PipelineBase):
    def run(self, page):
        html = urllib2.urlopen(page).read()
        body = BeautifulSoup(html)
        items = body.select('[href^=http://tw.page.bid.yahoo.com/tw/auction/]')
        items = [item.attrs.get('href') for item in items]
        items = set(items)
        for item_url in items:
            taskqueue.add(url="/create_product?" + urllib.urlencode({"target":item_url}), method='GET')
            logging.info(item_url)

class Parse(base_handler.PipelineBase):
    def run(self, target):
        html = urllib2.urlopen(target).read()
        body = BeautifulSoup(html)
        end = body.select('.ft em')[-1].text
        for i in xrange(1, int(end) + 1):
            if target.find('?') == -1:
                page_url = target + "?apg=" + str(i)
            else:
                page_url = target + "&apg=" + str(i)
            yield ParsePage(page_url)


from sample_auth import auth
class SummaryHandler(webapp2.RequestHandler):
    def get(self):
        auth(self.request, "george")
        import pdb;pdb.set_trace()

        target = self.request.get("target")

        job = Parse(target)
        job.start()
        
        if not self.request.get('X-Appengine-Cron'):
            self.redirect("%s/status?root=%s#pipeline-%s" % (
                job.base_path,
                job.root_pipeline_id,
                job.pipeline_id
            ))

app = webapp2.WSGIApplication([
    Route('/', handler=SummaryHandler, name='summary'),
    Route('/create_product', handler=Create_product, name='create'),
], debug=True)
