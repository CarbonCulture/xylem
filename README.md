# xylem

Library to interact with CarbonCulture's datastore


## Installation

Installation using pip::

    pip install https://github.com/CarbonCulture/xylem/archive/v0.4.11.zip

## Usage

You'll need an API key and an access name (like a username). Please contact
developer@carbonculture.net to request a key and access name.

### CarbonCulture's entities

CarbonCulture's datastreams are divided into entity types, which consist of
Communities, Places and Meters. A Community is a group of people, who may or
may not exist in the same physical location, a Place is a physical entity
around which you could draw a line (if you had enough chalk and lots of
ladders). A Meter is really an energy data-source rather than necessarily
being a true physical metering point, and could be derived from one, two (or
more) input datastreams (e.g. real-time data and a backup half-hourly feed).

You are able to request a section of data for a particular entity on the
CarbonCulture platform, over a time range, at different resolutions, in
different units, and with other helpful metadata -- depending on your access
level and the availability of these data.

In order to access these data, you will need to know the unique identifier (ID)
of the entity, and this can be found in the URL of the page on
carbonculture.net that represents this entity, for example UK Parliament (the
Community) has an ID of 2:

https://platform.carbonculture.net/communities/uk-parliament/2/

Cardiff Castle's ID is 947:

https://platform.carbonculture.net/places/cardiff-castle/947/

Note that a Place or Meter may have the same ID as a Community, but Places
and Meters never share IDs (this is because internally Places and Meters are
both represented as the same data structure - a physical 'Asset').

### Where/how to find data

CarbonCulture's datastreams ('Channels') are named in a similar way to these
URLs, so for example if you want to access UK Parliament's electricity data,
you would need the Channel called `communities.2.elec`, while Cardiff Castle's
gas data will be at `places.947.gas`.

In order to discover what utilities are accessible to you for an entity, you
can use the subject module, so let's look at an example of connecting and
discovering:

```
In [1]: from xylem.connection import Connection

In [2]: xc = Connection(
                'carbonculture@apps.utility-graph?communities.2',
                'bcac16a7f1fc2e32c9e41ea4ff9c7d693e49714e')

In [3]: from xylem.subjects import discover_available_resources

In [4]: discover_available_resources(xc, 2, 'communities')
Out[4]:
{u'elec': {u'data_type': u'',
  u'description': u'All electricity used by the UK Parliament community',
  u'earliest_timestamp': u'2013-07-17T00:00:00',
  u'gui_max': 5500.0,
  u'latest_timestamp': u'2015-05-12T00:00:00',
  u'licence': u'None',
  u'meta': u'',
  u'permissions': [u'read_history_full'],
  u'quality_assurance': [],
  u'resource_uri': u'/api/v1/channel/communities.2.elec',
  u'slug': u'communities.2.elec',
  u'stats': None,
  u'store_history': False,
  u'unit': u'kWh',
  u'value_type': u'accum',
  u'values': []},

...

```

There's quite a lot of info in this result, but the pertinent points are the
result keys:

```
In [5]: resources = discover_available_resources(xc, 2, 'communities')

In [6]: resources.keys()
Out[6]: [u'heat', u'elec', u'gas', u'energy']

```

This tells us what utilities there are available (i.e. configured), though this
is no guarantee that there will be data available -- to check this, inspect the
`earliest_timestamp` and `latest_timestamp` within each dictionary item.

### Fetching data

Once you know what you can see about an entity, it is easy to get data for a
range of time:

```
In [7]: from datetime import datetime, timedelta

In [8]: from pytz import utc

In [9]: earliest = datetime(2015, 01, 01, 0, 0, 0, 0, utc)

In [10]: latest = earliest + timedelta(days=7)

In [11]: values = xc.read_channel_values('communities.2.elec', earliest, latest)

```

`values` now contains a `dict` keyed by timestamp, with each value being a
further `dict` of values given in `kWh` (this Channel's default units as shown
in the earlier metadata request):

```
In [14]: values[earliest]
Out[14]: {u'kWh': 0.0}

In [15]: values[latest]
Out[15]: {u'kWh': 521617.70000000007}

```

### Transforming data

In the request above, the first value (`earliest`) is 0 - this is because this
data is given in a cumulative format ('`accum`', the default on this Channel),
with the origin set to the earliest point requested. If you want to have these
data as usage, you can simply subtract one from the other, or request it as
usage:

```

In [19]: values[latest]['kWh'] - values[latest - timedelta(minutes=30)]['kWh']
Out[19]: 1331.6999999999534

In [20]: values = xc.read_channel_values('communities.2.elec', earliest, latest, value_type='usage')

In [21]: values[latest]
Out[21]: {u'kWh': 1331.6999999999534}

```

Note that the `earliest` timestamp will not be present in a usage data request
since it is still treated as the data origin, and there is nothing to subtract
it from to give a difference (usage) value.

```

In [22]: values[earliest]
---------------------------------------------------------------------------
KeyError                                  Traceback (most recent call last)
<ipython-input-22-90c56dbf46f1> in <module>()
----> 1 values[earliest]

KeyError: datetime.datetime(2015, 1, 1, 0, 0, tzinfo=<UTC>)

```

You can also request energy data transformed into kilograms of carbon
(equivalent) (kgCO2e), and in pence (i.e. GBP). The advantage of asking this
question of the dataserver rather than applying a factor to the resulting kWh
values is that the dataserver knows what each of the Channel's factors are for
these transformations over time, and per component input Channel. For example,
`communities.2.energy` is actually just an aggregation of `communities.2.elec`
and `communities.2.gas`, but gas and electricity have different costs and
different carbon impacts, and these change over time. The transformation to the
input energy use data over time is applied at the lowest level possible so that
it is as close to the truth as possible. This also applies to e.g. an
electricity Channel which may be an aggregate of different Meters, and so on.

Here's how that works:

```

In [27]: values = xc.read_channel_values('communities.2.energy', earliest, latest, units='kWh,pence,kgCO2e')

In [28]: values[latest]
Out[28]:
{u'kWh': 1226567.4950116458,
 u'kgCO2e': 380901.7477941546,
  u'pence': 8488058.28979018}

```

You can also change the resolution of the data, which is half-hourly by
default. In some cases you may have access to higher-resolution data but
generally you will only be able to reduce this, so for example if you want one
point per day over a month:

```

In [32]: values = xc.read_channel_values('communities.2.energy', earliest, latest, resolution=60 * 60 * 24, value_type='usage')

In [33]: values.values()
Out[33]:
[{u'kWh': 196027.87567138532},
 {u'kWh': 148819.09393853648},

 ...

 ```
 
 **NB: Some requests may take a long time to process. If you are experiencing
 multiple time outs or error responses, please let us know
 (developer@carbonculture.net).**
