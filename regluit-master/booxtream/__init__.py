import random
from functools import partial
from urllib import quote
from xml.etree import ElementTree

import requests
from django.conf import settings

from django.apps import apps

from . exceptions import BooXtreamError

class BooXtream(object):
    """ ``apikey``

          The API key for your BooXtream account, obtained from BooXtream. Defaults to using
          settings.BOOXTREAM_API_KEY

        ``apiuser``

          The username key for your BooXtream account, obtained from BooXtream. Defaults to using
          settings.BOOXTREAM_API_USER


        ``timeout``

        passed to requests
    """
    def __init__(self,
                 apikey='', apiuser='',
                 timeout=None,
                 **params):
        if not apikey:
            apikey = settings.BOOXTREAM_API_KEY
        if not apiuser:
            apiuser = settings.BOOXTREAM_API_USER
        self.endpoint = 'https://service.booxtream.com/'
        self.postrequest = partial(requests.post, timeout=timeout, auth=(apiuser, apikey))


    def platform(self, epubfile=None, epub=True, kf8mobi=False, **kwargs):
        """ Make an API request to BooXtream
        ``self.apikey``, ``epubfile`` and the supplied ``kwargs``.
        Attempts to deserialize the XML response and return the download link.

        Will raise ``BooXtreamError`` if BooXtream returns an exception
        code.
        """
        Boox = apps.get_model('booxtream', 'Boox')

        url = self.endpoint + 'booxtream.xml'
        kwargs['epub'] = '1' if epub else '0'
        kwargs['kf8mobi'] = '1' if kf8mobi else '0'
        if epubfile:
            if hasattr(epubfile, 'name') and str(epubfile.name).endswith('.epub'):
                files = {'epubfile': (str(epubfile.name), epubfile)}
            else:
                # give it a random file name so that kindlegen doesn't choke
                # needed for in-memory (StringIO) epubs
                files= {'epubfile': ('%012x.epub' % random.randrange(16**12), epubfile)}
        else:
             files = {}
        if settings.LOCAL_TEST:
            # fake it, so you can test other functions without hitting booxtream
            boox = Boox.objects.create(
                download_link_epub='https://github.com/eshellman/42_ebook/blob/master/download/42.epub?raw=true&extra=download.booxtream.com/',
                download_link_mobi='https://github.com/eshellman/42_ebook/blob/master/download/42.mobi?raw=true',
                referenceid= kwargs.get('referenceid', '42'),
                downloads_remaining=kwargs.get('downloadlimit', 10),
                expirydays=kwargs.get('expirydays', 30),
            )
            return boox

        resp = self.postrequest(url, data=kwargs, files=files)
        doc = ElementTree.fromstring(resp.content)

        # it turns out an Error can have an Error in it
        errors = doc.findall('.//Response/Error')
        if len(errors) > 0:
            raise BooXtreamError(errors)
        download_link_epub = doc.find('.//DownloadLink[@type="epub"]')
        if download_link_epub is not None:
            download_link_epub = download_link_epub.text
        download_link_mobi = doc.find('.//DownloadLink[@type="mobi"]')
        if download_link_mobi is not None:
            download_link_mobi = download_link_mobi.text
        boox = Boox.objects.create(
            download_link_epub=download_link_epub,
            download_link_mobi=download_link_mobi,
            referenceid=kwargs.get('referenceid'),
            downloads_remaining=kwargs.get('downloadlimit'),
            expirydays=kwargs.get('expirydays'),
        )
        return boox