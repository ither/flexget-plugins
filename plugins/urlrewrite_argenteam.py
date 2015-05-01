from __future__ import unicode_literals, division, absolute_import
import urllib2
import logging
import re

from flexget import plugin
from flexget.event import event
from flexget.plugins.plugin_urlrewriting import UrlRewritingError
from flexget.utils.tools import urlopener
from flexget.utils.soup import get_soup


log = logging.getLogger('argenteam')
QUALITY = ['sd', 'hd']


class UrlRewriteArgenteam(object):
    """Argenteam urlrewriter.
    """

    schema = {
        'type': 'object',
        'properties': {
            'quality': {'type': 'string', 'enum': QUALITY, 'default': 'hd'}
        },
        'additionalProperties': False
    }

    # urlrewriter API
    def url_rewritable(self, task, entry):
        url = entry['url']
        if url.startswith('http://www.argenteam.net/episode') or url.startswith('http://www.argenteam.com/movie'):
            return True
        return False

    # urlrewriter API
    def url_rewrite(self, task, entry):
        self.config = task.config.get('argenteam')
        entry['url'] = self.parse_download_page(entry['url'])

    @plugin.internet(log)
    def parse_download_page(self, url):
        txheaders = {'User-agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
        req = urllib2.Request(url, None, txheaders)
        page = urlopener(req, log)
        try:
            soup = get_soup(page)
        except Exception as e:
            raise UrlRewritingError(e)

        config = self.config or {}
        config.setdefault('quality', 'hd')

        links = soup.find_all('a', text="Descargar", href=re.compile("/subtitles"))
        if not links:
            raise UrlRewritingError('Unable to locate subtitle download link from url %s' % url)

        subtitle_url = ''
        for link in links:
            sub_url = link['href']
            log.verbose('Found url %s', sub_url)
            if config['quality'] == 'hd' and re.search("720p|1080p",sub_url):
                subtitle_url = 'http://www.argenteam.net' + sub_url
                log.verbose('is a match')
                break
            if config['quality'] == 'sd' and re.search("720p|1080p",sub_url) == None:
                subtitle_url = 'http://www.argenteam.net' + sub_url
                log.verbose('is a match')
                break
        if subtitle_url == '':
            raise UrlRewritingError('Unable to locate download link %s from url %s' % (config['quality'], url))
        return subtitle_url

@event('plugin.register')
def register_plugin():
    plugin.register(UrlRewriteArgenteam, 'argenteam', groups=['urlrewriter'], api_ver=2)
