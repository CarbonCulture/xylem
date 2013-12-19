#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Methods for retreiving basic info about a subject's feeds."""
from datetime import datetime
from collections import defaultdict

import pytz


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


def write_app_claim(conn, app_slug, claim_slug, claim_data, subject_id,
                    subject_type_plural='communities'):
    """Write claim_data to the subject's claim_slug channel.

    :param xylem.Connection conn: The connection configured to the API.
    :param str app_slug: Slug of app for which this claim is being written.
    :param str claim_slug: Slug of claim for which this data is being written
    :param dict claim_data: key-value of data that describes this claim.
    :param int subject_id: ID of the subject about which this claim is made.
    :param str subject_type_plural: Default: 'communities'

    """
    channel_slug = ".".join([
        subject_type_plural, str(subject_id),
        'apps', app_slug, 'claims', claim_slug,
    ])
    now = datetime.utcnow().replace(tzinfo=pytz.utc)
    code, message = conn.write_channel_values(
        channel_slug, [(now.isoformat(), claim_data)])
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
    channels = conn.list_channels(slug__startswith=channel_root)
    apps = defaultdict(dict)
    for slug, ch in channels.items():
        app_part = slug[slug.index(channel_root) + len(channel_root):]
        app_slug = app_part.split('.')[0]
        apps[app_slug][slug] = ch

    return apps
