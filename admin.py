import cgi

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from models import *
import request

class ShowArticlesHandler(request.BlogRequestHandler):
        def get(self):
            articles = Article.get_all()
            template_vars = {'articles' : articles}

            self.response.out.write(self.render_template('admin.html', template_vars))

class NewArticleHandler(request.BlogRequestHandler):
        def get(self):
            article = Article(title='Title',
                              body='Contents',
                              short_url='',
                              draft=True)
            template_vars = {'article' : article}
            self.response.out.write(self.render_template('edit.html', template_vars))

class SaveArticleHandler(request.BlogRequestHandler):
        def post(self):
            title = cgi.escape(self.request.get('title'))
            body = self.request.get('content')
            short_url = cgi.escape(self.request.get('short_url'))
            slug = cgi.escape(self.request.get('slug'))
            s_id = cgi.escape(self.request.get('id'))
            id = int(s_id) if s_id else None
            tags = cgi.escape(self.request.get('tags'))
            date_published = cgi.escape(self.request.get('date_published'))
            draft = cgi.escape(self.request.get('draft'))
            if tags:
                tags = [t.strip() for t in tags.split(',')]
            else:
                tags = []
            tags = Article.convert_string_tags(tags)

            if not draft:
                draft = False
            else:
                draft = (draft.lower() == 'on')

            article = Article.get_id(id) if id else None
            if article:
                # It's an edit of an existing item.
                article.title = title
                article.body = body
                article.tags = tags
                article.short_url = short_url
                article.id = id
                article.draft = draft
            else:
                # It's new.
                article = Article(title=title,
                                  body=body,
                                  tags=tags,
                                  short_url=short_url,
                                  slug=slug,
                                  id=id,
                                  draft=draft)


            article.save()




            edit_again = cgi.escape(self.request.get('edit_again'))
            edit_again = edit_again and (edit_again.lower() == 'true')

            if edit_again:
                self.redirect('/admin/article/edit/?id=%s' % id)
            else:
                self.redirect('/admin/')

class EditArticleHandler(request.BlogRequestHandler):
        def get(self):
            id = int(self.request.get('id'))
            article = Article.get_id(id)
            if not article:
                raise ValueError, 'Article with id %s does not exist.' % id

            article.tag_string = ', '.join(article.tags)
            template_vars = {'article'  : article}
            self.response.out.write(self.render_template('edit.html', template_vars))

class DeleteArticleHandler(request.BlogRequestHandler):
        def get(self):
            id = int(self.request.get('id'))
            article = Article.get_id(id)
            if article:
                article.delete()

            self.redirect('/admin/')

application = webapp.WSGIApplication(
        [('/admin/?', ShowArticlesHandler),
         ('/admin/article/new/?', NewArticleHandler),
         ('/admin/article/delete/?', DeleteArticleHandler),
         ('/admin/article/save/?', SaveArticleHandler),
         ('/admin/article/edit/?', EditArticleHandler),
         ],

        debug=True)

def main():
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()
