#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import requests

from xylem import __version__

ROOT = 'http://nectarine.infra.carbonculture.net'

log = logging.getLogger(__name__)


class HttpError(Exception):
    pass


class Connection(object):
    """Basic class configured to make requests to CarbonCulture's Data API."""

    def __init__(self, access_name, api_key, root=None, format=None):
        self.access_name = access_name
        self.api_key = api_key
        self.root = root or ROOT
        self.endpoint = '{0}/api/v1/'.format(self.root)
        self.format = format or 'application/json'

        self.headers = {
            'Authorization': 'ApiKey {0}:{1}'.format(
                self.access_name, self.api_key),
            'User-Agent': 'XylemConnection Version {0}'.format(__version__),
            'Accept': self.format,
        }
        self.services = {}
        self._discover(self._test_connection())

    def get(self, endpoint=None, params=None):
        """Make a get."""
        log.debug('Get: {0}'.format(endpoint or self.endpoint), extra=params)
        r = requests.get(
            endpoint or self.endpoint,
            params=params,
            headers=self.headers,
        )
        return r

    def _test_connection(self):
        """Ping the endpoint and check we get a 200"""
        r = self.get()
        if r.status_code != 200:
            raise HttpError(
                "Got response code {0} from {1}".format(
                    r.status_code, self.endpoint))
        return r

    def _discover(self, response=None):
        """Get a list of accessible services.

        :param request.Response response: A previously fetched response

        """
        response = response or self.get()
        available = response.json()
        for key, meta in available.items():
            self.services[key] = self.root + meta['list_endpoint']

    def list_channels(self, **kwargs):
        """Get a list of channels, maybe filtered with kwargs"""
        r = self.get(
            self.services['channel'],
            params=kwargs
        )
        content = r.json()

        channels = dict([(ch['slug'], ch) for ch in content['objects']])
        while content['meta']['next'] is not None:
            r = self.get(self.root + content['meta']['next'])
            content = r.json()
            channels.update(dict(
                [(ch['slug'], ch) for ch in content['objects']]))
        return channels
