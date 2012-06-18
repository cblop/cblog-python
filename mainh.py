#! /usr/bin/env/ python

import os
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

class MainHandler(webapp.RequestHandler):
    def get(self):

        path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
        self.response.out.write(

                template.render( path,{
                    "title":"commander blop"
                    }))
