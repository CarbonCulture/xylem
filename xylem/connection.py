#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import json

import iso8601
import requests

from xylem import __version__

ROOT = 'https://rhizome.carbonculture.net'
API_PREFIX = 'api/v1'

log = logging.getLogger(__name__)


class HttpError(Exception):
    pass


class Connection(object):
    """Basic class configured to make requests to CarbonCulture's Data API."""

    def __init__(self, access_name, api_key, root=None, format=None):
        self.access_name = access_name
        self.api_key = api_key
        self.root = root or ROOT
        self.endpoint = '/'.join([self.root, API_PREFIX])
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
        if isinstance(data, dict):
            data = json.dumps(data)
        return self._request(
            endpoint, params=params, data=data, method='patch',
            extra_headers={
                'Content-Type': 'application/json',
            }
        )

    def post(self, endpoint=None, params=None, data=None):
        """Create resource."""
        if isinstance(data, dict):
            data = json.dumps(data)
        return self._request(
            endpoint, params=params, data=data, method='post',
            extra_headers={
                'Content-Type': 'application/json',
            }
        )

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
        if r.status_code == 200:
            content = r.json()

            channels = dict([(ch['slug'], ch) for ch in content['objects']])
            while content['meta']['next'] is not None:
                r = self.get(self.root + content['meta']['next'])
                content = r.json()
                channels.update(dict(
                    [(ch['slug'], ch) for ch in content['objects']]))
            return channels
        else:
            raise HttpError(
                "Got response code {0} from {1}".format(
                    r.status_code, self.endpoint))

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

    def create_channel(self, channel_data):
        """Posts to the API to make a new channel. Doesn't do existence check.

        :param dict channel_data: keys and values to make this channel.
        :rtype (int, str): (status code (one of: 202, 401), message)

        """
        _r = self.post(
            self.services['channel'],
            data=channel_data,
        )

        return (_r.status_code, _r.content)

    def create_channels(self, channel_data_list):
        """Convenience method to create several channels on one channels

        :param list channel_data_list: list of dicts 
        with keys and values for the channels
        :rtype list: status codes for each of the channel creation calls.

        """
        responses = []
        for ch in channel_data_list:
            responses.append(self.create_channel(ch))
        return responses

    def read_channel_latest_n_values(self, channel_slug, n=1):
        """Retrieve the latest n points from a channel.

        :param str channel_slug: Slug of channel for which to get data.
        :param int n: defaults to 1, number of points to get.
        :rtype list: tuple list of values
        """
        _r = self.get(
            self.services['channel'],
            params={
                'slug': channel_slug,
                'values__latest_n': n,
            }
        )
        response = _r.json()
        ch = response['objects'][0]
        values = ch['values']
        if isinstance(values, dict) and 'error' in values:
            raise ValueError(values['error'])
        return [
            (iso8601.parse_date(t), v)
            for t, v in values
        ]

    def assign_permissions_for_user_on_channel(
            self, user, channel_slug, permissions):
        """Assign the set of permissions for the user
        and the channel.

        :param str user: User access_name.
        :param str channel_slug: Slug of the channel.
        :param list permissions: List of codenames of permissions.
        :rtype (int, str): (status code, message)
        """
        _r = self.patch(
            self.services['channel'] + channel_slug,
            data={
                'user': user,
                'permissions': permissions
            },
        )

        return (_r.status_code, _r.content)

    def list_datausers(self):
        """Retrieves a list of the datausers.

        :rtype (int, str):
        :return: (status code, message)
        """
        _r = self.get(
            self.services['datauser']
        )
        return (_r.status_code, _r.content)

    def get_datauser(self, access_name):
        """Retrieve a datauser based on an access name.

        :rtype dict:
        :return: Dict with the information for that datauser.
        """
        _r = self.get(
            self.services['datauser'],
            data={'access_name': access_name}
        )
        return (_r.status_code, _r.content)

    def create_datauser(self, access_name):
        """Create datauser in Rhizome. Requires staff or admin user.

        :param str access_name: DataUser access name.
        :rtype (int, str): (status code, message).
        """
        _r = self.post(
            self.services['datauser'],
            data={"access_name": access_name},
        )

        return (_r.status_code, _r.content)

    def create_datausers(self, access_names):
        """Convenience method to create several datausers.

        :param list access_names: list of access names of users.
        with keys and values for the datausers
        :rtype list: status codes for each of the datauser creation calls.
        """
        responses = []
        for name in access_names:
            r = self.create_datauser(name)
            responses.append(r)
        return responses
