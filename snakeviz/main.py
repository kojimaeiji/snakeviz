#!/usr/bin/env python

import os.path
from pstats import Stats
import requests
import logging

try:
    from urllib.parse import unquote_plus
except ImportError:
    from urllib import unquote_plus

import tornado.ioloop
import tornado.web

from snakeviz.stats import table_rows, json_stats
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('snakeviz')

settings = {
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
    'debug': True,
    'gzip': True
}


class VizStats(Stats):

    def load_stats(self, arg):
        import marshal
        if arg is None:
            self.stats = {}
            return
        elif isinstance(arg, bytes):
            self.stats = marshal.loads(arg)
        elif hasattr(arg, 'create_stats'):
            arg.create_stats()
            self.stats = arg.stats
            arg.stats = {}
        if not self.stats:
            raise TypeError("Cannot create or construct a %r object from %r"
                            % (self.__class__, arg))
        return


class VizHandler(tornado.web.RequestHandler):

    def get(self, profile_name):
        profile_name = unquote_plus(profile_name)

        try:
            proxy_headers = self.request.headers._dict
            proxy_headers.pop('Host', None)
            proxy_params = self.request.query_arguments
            proxy_params['profiling'] = '1'
            proxy_params['dump'] = '1'
            logger.info('headers:' + str(proxy_headers))
            logger.info('querys:' + str(proxy_params))
            r = requests.get(
                'http://local-api2.cchan.tv/%s' % profile_name,
                headers=proxy_headers, params=proxy_params)
            try:
                json_resp = r.json()
                self.write(json_resp)
            except:
                s = VizStats(r.content)
                self.render(
                    'viz.html', profile_name=profile_name,
                    table_rows=table_rows(s), callees=json_stats(s))
        except:
            raise RuntimeError('Could not read %s.' % profile_name)


handlers = [(r'/snakeviz/(.*)', VizHandler)]

app = tornado.web.Application(handlers, **settings)

if __name__ == '__main__':
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
