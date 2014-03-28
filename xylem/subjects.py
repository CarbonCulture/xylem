#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Methods for retreiving basic info about a subject's feeds."""
from datetime import datetime
from collections import defaultdict

import pytz

from xylem.connection import HttpError


class APIError(Exception):
    pass


def discover_available_resources(conn, subject_id,
                                 subject_type_plural='places'):
    """Return a dictionary of channels keyed by the resource slug.

    :param xylem.Connection conn: The connection configured to the API
    :param int subject_id: ID of the subject to locate.
    :param str subject_type_plural: Default: 'places'.
    :rtype dict: Resource-keyed channel info (such as {'elec': {...}})

    """
    resources = {}
    channel_root = ".".join([subject_type_plural, str(subject_id)]) + '.'
    channels = conn.list_channels(slug__startswith=channel_root)
    for slug, ch in channels.items():
        resource_slug = slug[slug.index(channel_root) + len(channel_root):]
        resources[resource_slug] = ch

    return resources


def write_app_event(conn, app_slug, event_slug, event_data, subject_id,
                    subject_type_plural='communities'):
    """Write event_data to the subject's event_slug channel.

    :param xylem.Connection conn: The connection configured to the API.
    :param str app_slug: Slug of app for which this event is being written.
    :param str event_slug: Slug of event for which this data is being written
    :param dict event_data: key-value of data that describes this event.
    :param int subject_id: ID of the subject about which this event is made.
    :param str subject_type_plural: Default: 'communities'

    """
    channel_slug = ".".join([
        subject_type_plural, str(subject_id),
        'apps', app_slug, 'events', event_slug,
    ])
    now = datetime.utcnow().replace(tzinfo=pytz.utc)
    code, message = conn.write_channel_values(
        channel_slug, [(now.isoformat(), event_data)])
    if code != 202:
        raise APIError("API Error (Code: {0}): {1}".format(code, message))


def discover_installed_apps(conn, subject_id,
                            subject_type_plural='communities'):
    """Return a list of app slugs installed, and visible, on this subject.

    :param xylem.Connection conn: The connection configured to the API
    :param int subject_id: ID of the subject to locate.
    :param str subject_type_plural: Default: 'communities'.
    :rtype dict: keys are app slugs, values are channels dicts keyed by slug
        available in that app

    Note that there may be apps installed which do not make their availability
    visible to other parties.

    """
    channel_root = ".".join([
        subject_type_plural, str(subject_id), 'apps'
    ]) + '.'
    try:
        channels = conn.list_channels(slug__startswith=channel_root)
        apps = defaultdict(dict)
        for slug, ch in channels.items():
            app_part = slug[slug.index(channel_root) + len(channel_root):]
            app_slug = app_part.split('.')[0]
            apps[app_slug][slug] = ch

        return apps
    except HttpError as e:
        raise APIError("API Error: {0}".format(e))
