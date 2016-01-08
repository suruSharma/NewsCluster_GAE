import sys
sys.path.insert(0, 'libs')

import webapp2
import requests
import urllib2
from bs4 import BeautifulSoup
from google.appengine.ext import ndb
from google.appengine.ext import db
import logging

class NewsData(ndb.Model):
    seedUrl = ndb.StringProperty(indexed=False)
    url = ndb.StringProperty(indexed=False)
    tags = ndb.StringProperty(indexed=False,repeated=True)
    title = ndb.StringProperty(indexed=False)
    description = ndb.StringProperty(indexed=False)

def newsData_key(seedUrl):
    return ndb.Key('NewsData', seedUrl)
    
def bbc_crawler(self):
    url = 'http://www.bbc.com/'
    source_code = urllib2.urlopen(url).read()
    soup = BeautifulSoup(source_code)
    for link in soup.findAll('a', {'class': 'media__link'}):
        href = link.get('href')
        #This is to ignore video and image galleries
        if 'video-extras' in href or 'in-pictures-' in href:
            continue
            
        #Append the parent url only if the url is not well formed
        if href.startswith( '/' ) == True:
            href = url + href
        #logging.info("Href : "+href)
        title = link.text.strip()
        #logging.info("Title : "+title)
        bbc_getContent(self,href,url,title)

def bbc_getContent(self,item_url,seedUrl,title):
    try:
        logging.info('Inside inner method')
        source_code = urllib2.urlopen(item_url).read()
        soup = BeautifulSoup(source_code)
        resource = NewsData(parent=newsData_key(seedUrl))
        resource.seedUrl = seedUrl
        resource.url = item_url
        resource.title = title
        desc = ''
        for intro in soup.findAll('p', {'class' : 'story-body__introduction'}):
            introText = intro.text
            desc += introText
            desc += '\n'
            
        for para in soup.findAll('p', {'class' : ''}):
            cls = para.attrs.get("class")
            if not cls:
                paraText = para.text
                desc += paraText
                desc += '\n'
        
        #logging.info("Description : "+desc)
        resource.description = desc
        
        ct = []
        for tag in soup.findAll('meta', {'property' : 'og:description'}):
            content = tag.attrs.get("content").lower()
            contentTag = content.split(" ")
            for t in contentTag:
                ct.append(t.strip())
        
        #logging.info("Tags : "+ct)
        resource.tags = ct    
        
        resource.put()
        
    except Exception as inst:
        logging.info(inst)
        logging.info('Inside exception')
        pass
    
            
class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        bbc_crawler(self)
        
app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)