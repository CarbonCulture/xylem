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


def minimum_data_presence_for_range(conn, earliest, latest, slug=None,
                                    subject_id=None, subject_type_plural=None,
                                    utilities=None):

    """Return minimum data presence for given subject: 0 to 1 (100%).

    Note that for subjects with real-time data, this is currently unreliable.
    Note that this represents data presence for known & configured sources.

    :param xylem.Connection conn: The connection configured to the API
    :param datetime earliest: from when to get presence value
    :param datetime latest: up to (inclusive) when to get presence value
    :param str slug: slug to get presence for, or None to use subject type/id
    :param int subject_id: ID of the subject to locate, or None if using slug
    :param str subject_type_plural: Default: 'places'
    :param list utilities: list of utilities (elec, gas, etc.) or None
    :rtype: float
    :return: a value between 0 (no data) and 1 (100% expected data present)
    :raises: APIError in the case that either the request fails or isn't 200 OK

    """
    subject_type_plural = subject_type_plural or 'places'
    slugs = []
    if slug is None:
        if utilities:
            for util in utilities:
                slug = ".".join([subject_type_plural, subject_id, util])
                slugs.append(slug)
        else:
            slugs = [".".join([subject_type_plural, subject_id])]
    else:
        slugs = [slug]

    params = {
        'qa_only': True,
        'quality_assurance': 'presence',
        'values__earliest': earliest.isoformat(),
        'values__latest': latest.isoformat(),
        'slug__in': ",".join(slugs)
    }
    try:
        resp = conn.get(
            endpoint=conn.services['channels'], params=params
        )
    except HttpError as e:
        raise APIError("API Error: {}".format(e))

    if resp.status_code != 200:
        raise APIError(
            "API Error: ({}) {}".format(resp.status_code, resp.content))

    min_presence = 1
    for channel in resp.json()['objects']:
        qa_presence = channel['quality_assurance']
        presence_vals = [vals[0] for ts, vals in qa_presence]
        min_presence = min(min_presence, min(presence_vals))
    return min_presence
