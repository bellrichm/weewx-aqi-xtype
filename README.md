# weewx-aqi-xtype

## Description

This extension uses WeeWX [Xtypes](http://www.weewx.com/docs/latest/customizing.htm#Adding_new,_derived_types) capability to dynamically calculate AQI.
Currently it only supports pm 2.5 and pm 10.
For supported pollutants, mutiple sensors are supported.
Currently only the US EPA algorithm is supported.

## Installation notes

Because there are [multiple methods to install WeeWX](http://weewx.com/docs/usersguide.htm#installation_methods), location of files can vary.
See [where to find things](http://weewx.com/docs/usersguide.htm#Where_to_find_things)
in the WeeWX [User's Guide](http://weewx.com/docs/usersguide.htm") for the definitive information.
The following symbolic names are used to define the various locations:

- *$DOWNLOAD_ROOT* - The directory containing the downloaded *weewx-aqi-xtype* extension.
- *$BIN_ROOT* - The directory where WeeWX executables are located.
- *$CONFIG_ROOT* - The directory where the configuration (typically, weewx.conf) is located.

The notation vX.Y.Z designates the version being installed.
X.Y.Z is the release.

Prior to making any updates/changes, always make a backup.

## Preqrequisites

|WeeWX version   |Python version                               |
|----------------|---------------------------------------------|
|4.6.0 or greater|Python 3.6 or greater                        |

## Installation

1. Download weewx-aqi-xtype

    ```text
    wget -P $DOWNLOAD_ROOT https://github.com/bellrichm/weewx-aqi-ztype/archive/vX.Y.Z.tar.gz
    ```

    All of the releases can be found [here](https://github.com/bellrichm/weewx-xtype-aqi/releases) and this is the [latest](https://github.com/bellrichm/weewx-aqi-xtype/releases/latest).

2. Install weewx-aqi-xtype

    ```text
    wee_extension --install=$DOWNLOAD_DIR/vX.Y.Z.tar.gz
    ```

3. Restart WeeWX

    ```text
    sudo /etc/init.d/weewx restart
    ```

    or

    ```text
    sudo sudo service restart weewx
    ```

    or

    ```text
    sudo systemctl restart weewx
    ```

## Customizing

The installation of weewx-aqi-xtype configures it so that will work with the WeeWX 'extended schema.'
It will calculate the Instacast AQI and NowCast AQI for the value of pm 2.5.
To do this three sections of weewx configuration are updated.
The first is `[[[Generic]]]` section of `[StdReport][[Labels]]`.
Here the default label is added.

```text
[StdReport]
    [[Labels]]
        [[[Generic]]]
            .
            .
            .
            pm2_5_aqi = AQI
            pm2_5_aqi_nowcast = AQI (NowCast)
```

The second is the `[[Calculations]]` section of `[StdWXCalculate]`.
Here, the calculated AQI field is added.
Doing this adds it to the WeeWX loop packets and archive records.

```text
[StdWXCalculate]
    [[Calculations]]
    .
    .
    .
        pm2_5_aqi = prefer_hardware
        # Since this requires a database look up, by default do not populate loop packets
        pm2_5_aqi_nowcast = prefer_hardware, archive        
```

The third update is an additional section, `[aqitype]`.
This is where the information needed to calculate the AQI is configured.

```text
[aqitype]
    # The name of AQI field.
    # Create a section for each field to be calculated.
    [[pm2_5_aqi]]
        # The name of the WeeWX observation to be used in the calculation.
        input = pm2_5
        # The name of the algorithm.
        # Supported values: EPAAQI
        algorithm = EPAAQI
        # If the algorithm supports different pollutants(pm 2.5, pm 10, etc)
        # Supported values: pm2_5, pm10
        type = pm2_5
    [[pm2_5_aqi_nowcast]]
        # The name of the WeeWX observation to be used in the calculation.
        input = pm2_5
        # The name of the algorithm.
        # Supported values: EPAAQI, NowCast
        algorithm = NowCast
        # If the algorithm supports different pollutants(pm 2.5, pm 10, etc)
        # Supported values: pm2_5, pm10
        type = pm2_5                
```

Suppose one has a second air quality sensor and WeeWX has been configured to store it in `pm2_51`.
To calculate the AQI value for this sensor, both the `[[Calculations]]` section and `[aqitype]` section need to be updated.
The result should look something like this.

```text
[StdReport]
    [[Labels]]
        [[[Generic]]]
            .
            .
            .
            pm2_5_aqi = Inside AQI
            pm2_5_aqi = Outside AQI
            pm2_5_aqi_nowcast = Inside AQI (NowCast)
            pm2_51_aqi_nowcast = Outside AQI (NowCast)
```

```Text
[StdWXCalculate]
    [[Calculations]]
    .
    .
    .
        pm2_5_aqi = prefer_hardware
        pm2_51_aqi = prefer_hardware
        # Since this requires a database look up, by default do not populate loop packets
        pm2_5_aqi_nowcast = prefer_hardware, archive     
        pm2_51_aqi_nowcast = prefer_hardware, archive                     
```

```text
[aqitype]
    # The name of AQI field.
    # Create a section for each field to be calculated.
    [[pm2_5_aqi]]
        # The name of the WeeWX observation to be used in the calculation.
        input = pm2_5
        # The name of the algorithm.
        # Supported values: EPAAQI
        algorithm = EPAAQI
        # If the algorithm supports different pollutants(pm 2.5, pm 10, etc)
        # Supported values: pm2_5, pm10
        type = pm2_5      
    [[pm2_51_aqi]]
        # The name of the WeeWX observation to be used in the calculation.
        input = pm2_51
        # The name of the algorithm.
        # Supported values: EPAAQI
        algorithm = EPAAQI
        # If the algorithm supports different pollutants(pm 2.5, pm 10, etc)
        # Supported values: pm2_5, pm10
        type = pm2_5         
    [[pm2_51_aqi_nowcast]]
        # The name of the WeeWX observation to be used in the calculation.
        input = pm2_51
        # The name of the algorithm.
        # Supported values: EPAAQI, NowCast
        algorithm = NowCast
        # If the algorithm supports different pollutants(pm 2.5, pm 10, etc)
        # Supported values: pm2_5, pm10
        type = pm2_5                 
```

By default `aqi_xtype` is added to the beginning of the list of xtypes.
This has the effect of overriding other xtypes (except for any added to the beginning after `aqi-xtype`).
If for some reason it is desired to add it to the end, set `prepend = False`

```text
[aqitype]
    # Add aqi-xtype to the end of the list of xtypes.
    prepend = False
```

## Using

Now the calculated value, pm2_5_aqi can be used like any built-in WeeWX type.

Note: NowCast values are only available with the $current and $latest tags.
It does not support aggregation nor series.

### Display values

For example, in a Cheetah template

|Desired display                                                   |Cheetah code |
|------------------------------------------------------------------|--------------------|
| Current value                                                    | $current.pm2_5_aqi |
| Maximum value for the year                                       | $year.pm2_5_aqi.max |
| A json series of maximum values for the days of the current year | $year.pm2_5_aqi.series(aggregate_type='max', aggregate_interval='day').json |

### Charting

#### WeeWX ImageGenerator

The values are also available to the builtin WeeWX charting subsystem
Here are two charts.
One of the calculated pm 2.5 AQI.
The scond of the pm 2.5 values.

``` text
    [[year_images]]
        aggregate_type = max
        aggregate_interval = 86400

        [[[yearaqi]]]
            yscale = 0, None, None
            [[[[pm2_5_aqi]]]]

        [[[yearpm2_5]]]
            yscale = 0, None, None
            [[[[pm2_5]]]]
```

#### weewx-jas

The values are also available to user extensions.
For exanmple a graph in the [weewx-jas](https://github.com/bellrichm/weewx-jas) would look like this

```text
    [[jas]]
        [[[Extras]]]
            [[[[chart_definitions]]]]
                [[[[[pm]]]]]
                    [[[[[[series]]]]]]
                        [[[[[[[pm2_5]]]]]]]
                            yAxisIndex = 0
                        [[[[[[[pm2_5_aqi]]]]]]]
                            yAxisIndex = 1
                        [[[[[[[pm10_0]]]]]]]
```

### Additional Cheetah Tags

In addition to the XTtype to calculate the AQI, WeeWX-aqi-xtype has a WeeWX SearchList extension which given an AQI value and standard/algorithm will return the associated color hex value. It also can look up the AQI label for a given AQI value and standard/algorithm.

#### $AQIColor

This is called like, `$AQIColor(value, standard)`.

#### $AQIDescription

This is called like, `$AQIDescription(value, standard)`.

## Logging

In an attempt to reduce the amount of data that is logged, weewx-aqi-xtype supports different logging levels for each configured AQI field.
The python logging facility and its logging levels are leveraged to accomplish this.
The configuration option, `log_level`, is used to accomplish this.
This option uses a subset of the [python logging levels](https://docs.python.org/3/library/logging.html#logging-levels).
The valid values for `weewx-aqi-xtype` `log_level` configuration setting are:

| Setting | Description                                              |
|---------|----------------------------------------------------------|
| 10      | Debug messages will be logged.                           |
| 20      | Informational and Debug messages will be logged.         |
| 30      | Error, Informational, and Debug messages will be logged. |

Suppose that `weewx-aqi-xtype` has two AQI fields, `aqi_field_one` and `aqi_field_two`.
And it is desired to only log `informmational` and `error` messages for `aqi_field_one`.
But, one wants to log all three for `aqi_field_two`.
The following configuration would accomplish this.

Note, `# log_level = 20` is included only to show that it could be overriden at this level.
So, if it was desired to see `debug` messages for both fields, this could be uncommented out.

``` text
[aqitype]
    # This is the default log_level. 
    # Even if WeeWX has a 'log_level of debug' (typically debug = 1), debug messages will not be logged.
    # log_level = 20
    [[aqi_field_one]]
        .
        .
        .   
    [[aqi_field_two]]
        # This overrides the log_level.
        # The result is for this AQI field, debug messages will be logged.
        log_level = 10
        .
        .
        .
```

In addition to understanding the [debug = 1 setting](https://weewx.com/docs/5.1/reference/weewx-options/general/?h=debug#debug),
I would recommend reading up on [WeeWX's improved logging](https://github.com/weewx/weewx/wiki/WeeWX-v4-and-logging#customizing-what-gets-logged) that was introduced in V4.

## Getting Help

Feel free to [open an issue](https://github.com/bellrichm/weewx-aqi-xtype/issues/new),
[start a discussion in github](https://github.com/bellrichm/weewx-aqi-xtype/discussions/new),
or [post on WeeWX google group](https://groups.google.com/g/weewx-user).
When doing so, see [Help! Posting to weewx user](https://github.com/weewx/weewx/wiki/Help!-Posting-to-weewx-user)
for information on capturing the log.
And yes, **capturing the log from WeeWX startup** makes debugging much easeier.
