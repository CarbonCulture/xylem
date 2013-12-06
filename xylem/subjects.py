#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Methods for retreiving basic info about a subject's feeds."""


def discover_available_resources(conn, subject_id, subject_type_plural='places'):
    """Return a dictionary of channels keyed by the resource slug.

    :param xylem.XylemConnector conn: The XylemConnector configured to the API
    :param int subject_id: ID of the subject to locate.
    :param str subject_type_plural: Default: 'places'.
    :rtype dict: Resource-keyed channel info (such as {'elec': {...}})

    """
    resources = {}
    channel_root = '{0}.{1}'.format(subject_type_plural, subject_id)
    channels = conn.list_channels(slug__startswith=channel_root)
    for slug, ch in channels.items():
        resource_slug = slug[slug.index(channel_root) + len(channel_root) + 1:]
        resources[resource_slug] = ch

    return resources


