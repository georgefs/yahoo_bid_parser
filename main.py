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


class ParserItem(base_handler.PipelineBase):
    def run(self, item_page):
        html = urllib2.urlopen(item_page).read()
        body = BeautifulSoup(html)
        title = smart_str(body.select("#trace_hid_name")[0].attrs.get('value'))
        price = int(re.match("\d+", body.select("[itemprop=price]")[0].attrs.get('content')).group())
        logging.info(title,price)


class ParsePage(base_handler.PipelineBase):
    def run(self, page):
        html = urllib2.urlopen(page).read()
        body = BeautifulSoup(html)
        items = body.select('[href^=http://tw.page.bid.yahoo.com/tw/auction/]')
        for item in items:
            item_url = item.attrs.get('href')
            yield ParserItem(item_url)

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


class SummaryHandler(webapp2.RequestHandler):
    def get(self):
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
], debug=True)
