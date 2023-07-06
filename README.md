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
It will calculate the AQI for the value of pm 2.5.
To do this two sections of weewx configuration are updated.
The first is the `[[Calculations]]` section of `[StdWXCalculate]`.
Here, the calculated AQI field is added.
Doing this adds it to the WeeWX loop packets and archive records.

```text
[StdWXCalculate]
    [[Calculations]]
    .
    .
    .
        pm2_5_aqi = prefer_hardware
```

The second update is an additional section, `[aqitype]`.
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
```

Suppose one has a second air quality sensor and WeeWX has been configured to store it in `pm2_51`.
To calculate the AQI value for this sensor, both the `[[Calculations]]` section and `[aqitype]` section need to be updated.
The result should look something like this.

```text
[StdWXCalculate]
    [[Calculations]]
    .
    .
    .
        pm2_5_aqi = prefer_hardware
        pm2_51_aqi = prefer_hardware
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
```

## Using

Now the calculated value, pm2_5_aqi can be used like any built-in WeeWX type.

### Display values

For example, in a Cheetah template
|Desired display                                                   |Cheetah code |
|------------------------------------------------------------------|--------- ----------|
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


## Getting Help

Feel free to [open an issue](https://github.com/bellrichm/weewx-aqi-xtype/issues/new),
[start a discussion in github](https://github.com/bellrichm/weewx-aqi-xtype/discussions/new),
or [post on WeeWX google group](https://groups.google.com/g/weewx-user).
When doing so, see [Help! Posting to weewx user](https://github.com/weewx/weewx/wiki/Help!-Posting-to-weewx-user)
for information on capturing the log.
And yes, **capturing the log from WeeWX startup** makes debugging much easeier.
