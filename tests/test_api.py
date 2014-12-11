#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from datetime import datetime
from unittest import TestCase

import httpretty

from xylem.connection import Connection, ROOT
from xylem.subjects import (
    discover_available_resources, minimum_data_presence_for_range
)


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


class QATests(TestCase):

    @httpretty.activate
    def test_min_presence_check(self):
        httpretty.register_uri(
            httpretty.GET, "{0}/api/v1".format(ROOT),
            body=BASIC_RESOURCES_AVAILABLE, content_type="application/json"
        )
        resp = {
            "meta": {
                "qa_only": True,
                "quality_assurance": [
                    "presence"
                ],
                "values__earliest": "2014-12-01T00:00:00Z",
                "values__latest": "2014-12-10T00:00:00Z"
            },
            "objects": [
                {
                    "quality_assurance": [
                        ('TS HERE', [0.3]),
                        ('TS HERE', [1]),
                    ]
                },
                {
                    "quality_assurance": [
                        ('TS HERE', [0.5]),
                        ('TS HERE', [1]),
                    ]
                }
            ]
        }
        xc = Connection('fake', 'fake')
        httpretty.register_uri(
            httpretty.GET, xc.services['channel'],
            body=json.dumps(resp), content_type="application/json"
        )

        min_presence = minimum_data_presence_for_range(
            xc, datetime.now(), datetime.now(), subject_id=1, utilities=[
                'elec', 'gas'
            ]
        )
        self.assertEqual(min_presence, 0.3)

        del resp['objects'][0]
        httpretty.register_uri(
            httpretty.GET, xc.services['channel'],
            body=json.dumps(resp), content_type="application/json"
        )
        min_presence = minimum_data_presence_for_range(
            xc, datetime.now(), datetime.now(), slug='a.b.c'
        )
        self.assertEqual(min_presence, 0.5)
