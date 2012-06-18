#! /usr/bin/env python
import datetime
import sys
import re
from unidecode import unidecode

from google.appengine.ext import db

FETCH_THEM_ALL = ((sys.maxint - 1) >> 32) & 0xffffffff
_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.:]+')

def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        result.extend(unidecode(word).split())
    return unicode(delim.join(result))


class Article(db.Model):
    title = db.StringProperty(required=True)
    body = db.TextProperty()
    date_published = db.DateTimeProperty(auto_now_add=True)
    tags = db.ListProperty(db.Category)
    slug = db.StringProperty()
    short_url = db.StringProperty()
    id = db.IntegerProperty()
    draft = db.BooleanProperty(required=True, default=False)

    @classmethod
    def get_all(cls):
        q = db.Query(Article)
        q.order('-date_published')
        return q.fetch(FETCH_THEM_ALL)

    @classmethod
    def get(cls, slug):
        q = db.Query(Article)
        q.filter('slug = ', slug)
        return q.get()

    @classmethod
    def get_id(cls, id):
        q = db.Query(Article)
        q.filter('id = ', id)
        return q.get()

    @classmethod
    def get_short_url(cls, short_url):
        q = db.Query(Article)
        q.filter('short_url = ', short_url)
        return q.get()

    @classmethod
    def published_query(cls):
        q = db.Query(Article)
        q.filter('draft = ', False)
        return q

    @classmethod
    def published(cls):
        return Article.published_query().order('-date_published').fetch(FETCH_THEM_ALL)


    @classmethod
    def get_all_tags(cls):
        """
        Return all tags, as TagCount objects, optionally sorted by frequency
        (highest to lowest).
        """
        tag_counts = {}
        for article in Article.published():
            for tag in article.tags:
                tag = unicode(tag)
                try:
                    tag_counts[tag] += 1
                except KeyError:
                    tag_counts[tag] = 1

        return tag_counts

    @classmethod
    def get_all_datetimes(cls):
        dates = {}
        for article in Article.published():
            date = datetime.datetime(article.date_published.year,
                                     article.date_published.month,
                                     article.date_published.day)
            try:
                dates[date] += 1
            except KeyError:
                dates[date] = 1

        return dates


    @classmethod
    def all_for_month(cls, year, month):
        start_date = datetime.date(year, month, 1)
        if start_date.month == 12:
            next_year = start_date.year + 1
            next_month = 1
        else:
            next_year = start_date.year
            next_month = start_date.month + 1

        end_date = datetime.date(next_year, next_month, 1)
        return Article.published_query()\
                       .filter('date_published >=', start_date)\
                       .filter('date_published <', end_date)\
                       .order('-date_published')\
                       .fetch(FETCH_THEM_ALL)

    @classmethod
    def all_for_tag(cls, tag):
        return Article.published_query()\
                      .filter('tags = ', tag)\
                      .order('-date_published')\
                      .fetch(FETCH_THEM_ALL)

    @classmethod
    def convert_string_tags(cls, tags):
        new_tags = []
        for t in tags:
            if type(t) == db.Category:
                new_tags.append(t)
            else:
                new_tags.append(db.Category(unicode(t)))
        return new_tags

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return '[%s] %s' %\
               (self.date_published.strftime('%Y/%m/%d %H:%M'), self.title)

    def save(self):
        previous_version = Article.get_id(self.id)
        try:
            draft = previous_version.draft
        except AttributeError:
            draft = False

        if draft and (not self.draft):
            self.date_published = datetime.datetime.now()

        try:
            obj_id = self.key().id()
            resave = False
        except db.NotSavedError:
            resave = True

        self.put()

        if resave:

            self.slug = slugify(self.title)
            self.id = self.key().id()
            self.put()
    
