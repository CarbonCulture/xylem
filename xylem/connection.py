#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import json

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

    def _request(self, endpoint=None, method=None, params=None, data=None,
                 extra_headers=None):
        """Generic request, default to GET."""
        method = method or 'get'
        headers = extra_headers or {}
        headers.update(self.headers)
        log.debug(
            '{0}: {1}'.format(method, endpoint or self.endpoint),
            extra={
                'params': params,
                'data': data,
                'headers': headers,
            }
        )
        fn = getattr(requests, method)
        r = fn(
            endpoint or self.endpoint,
            params=params,
            data=data,
            headers=headers,
        )
        return r

    def get(self, endpoint=None, params=None):
        """Make a get."""
        return self._request(endpoint, params=params)

    def patch(self, endpoint=None, params=None, data=None):
        """Partial update to resource (e.g. put history or change meta)."""
        return self._request(
            endpoint, params=params, data=json.dumps(data), method='patch',
            extra_headers={
                'Content-Type': 'application/json',
            }
        )

    def post(self, endpoint=None, params=None, data=None):
        """Partial update to resource (e.g. put history or change meta)."""
        return self._request(
            endpoint, params=params, data=data, method='post')

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

    def write_channel_values(self, channel_slug, values):
        """Write the given values to the channel identified by channel_slug.

        :param str channel_slug: Slug of channel to which data will be written
        :param list values: (timestamp, value) list to write to channel
        :rtype (int, str): (status code (one of: 202, 401), message)

        """
        _r = self.patch(
            self.services['channel'] + channel_slug,
            data={
                'values': values
            },
        )

        return (_r.status_code, _r.content)