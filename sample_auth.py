#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2014 george 
#
# Distributed under terms of the MIT license.
from datetime import datetime
import hashlib
from google.appengine.api import urlfetch
import urllib



def gen_token(token):
    token = datetime.now().strftime(token + '%Y%m%d')
    hash_token = hashlib.sha224(token).hexdigest()
    return hash_token

def auth(request, token):
    assert request.headers.get('token') == gen_token(token), 'auth token error'


def send(token, url, method='GET', params={}):
    result = urlfetch.fetch(url)

    result = urlfetch.fetch(url=url,
        payload=urllib.urlencode(params),
        method=urlfetch.POST,
        headers={'token': gen_token(token)})


if __name__ == '__main__':
    print gen_token('george')
