#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest import TestCase

import httpretty

from xylem.connection import Connection, ROOT
from xylem.subjects import discover_available_resources


BASIC_RESOURCES_AVAILABLE = """
{
    "channel": {
        "list_endpoint": "/api/v1/channel/",
        "schema": "/api/v1/channel/schema/"
    }
}
"""


PLACE_BASIC_UTILS = """
{
    "meta": {
        "limit": 20,
        "next": null,
        "offset": 0,
        "previous": null,
        "total_count": 2
    },
    "objects": [
        {
            "description": "Total grid electricity consumed at SOMEPLACE",
            "earliest_timestamp": "2000-07-27T01:01:01",
            "gui_max": 500,
            "latest_timestamp": "2013-12-09T10:51:01.719301",
            "licence": "A Licence",
            "permissions": [ "read_history_hh" ],
            "resource_uri": "/api/v1/channel/places.N.elec",
            "slug": "places.N.elec",
            "stats": null,
            "store_history": false,
            "unit": "kWh",
            "value_type": "accum",
            "values": [ ]
        },
        {
            "description": "Total mains gas consumed at SOMEPLACE",
            "earliest_timestamp": "2000-07-27T01:01:01",
            "gui_max": 500,
            "latest_timestamp": "2013-12-09T10:51:01.719301",
            "licence": "A Licence",
            "permissions": [ "read_history_hh" ],
            "resource_uri": "/api/v1/channel/places.N.gas",
            "slug": "places.N.gas",
            "stats": null,
            "store_history": false,
            "unit": "m3",
            "value_type": "accum",
            "values": [ ]
        }
    ]
}
"""


class XylemTestCase(TestCase):

    @httpretty.activate
    def test_resource_discovery(self):
        """Simple test to make sure dict ends up in the right format."""
        httpretty.register_uri(
            httpretty.GET, "{0}/api/v1".format(ROOT),
            body=BASIC_RESOURCES_AVAILABLE, content_type="application/json"
        )
        xc = Connection('fake', 'fake')
        httpretty.register_uri(
            httpretty.GET, xc.services['channel'],
            body=PLACE_BASIC_UTILS, content_type="application/json"
        )
        resources = discover_available_resources(xc, 'N')

        self.assertEqual(sorted(resources.keys()), sorted(['elec', 'gas']))
