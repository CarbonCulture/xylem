#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Methods for retreiving basic info about an asset's feeds."""


def discover_available_resources(conn, asset_id, asset_type='places'):
    """Return a dictionary of channels keyed by the resource slug.

    :param xylem.XylemConnector conn: The XylemConnector configured to the API
    :param int asset_id: ID of the asset to locate.
    :param str asset_type: Default: 'places'.
    :rtype dict: Resource-keyed channel info (such as {'elec': {...}})

    """
    resources = {}
    channel_root = '{0}.{1}'.format(asset_type, asset_id)
    channels = conn.list_channels(slug__startswith=channel_root)
    for slug, ch in channels.items():
        resource_slug = slug[slug.index(channel_root) + len(channel_root) + 1:]
        resources[resource_slug] = ch

    return resources


