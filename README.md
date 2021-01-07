# pi_awning_webthing
A web connected terrace awning controller on Raspberry Pi

Currently supported are [TB6612FNG driven](https://www.pololu.com/product/713) motors such 
as [DGO-3512ADA](https://www.ebay.co.uk/itm/Gear-Motor-Direct-Current-6-12V-Electric-With-Removable-Crank-DGO-3512ADA-/183375290396). 
The concrete motor configuration(s) are defined by using a config file such s shown below. 
```
# name, gpio_forward, gpio_backward, step_duration_in_sec
lane1, 2, 3, 0.5
lane2, 19, 26, 0.5
lane3, 5, 6, 0.5
lane4, 10, 9, 0.5
```
For TB6612FNG driven motors the filename has to include the term *tb6612fng* such as tb6612fng_motors.config. Regarding the 
hardware setup and wiring please refer [example hardware setup](doc/dgo-3512ada.md)

To install this software you may use [Docker](https://phoenixnap.com/kb/docker-on-raspberry-pi) or [PIP](https://realpython.com/what-is-pip/) package manager such as shown below

**Docker approach**
```
sudo docker run --privileged -p 9500:9500 -v /etc/awning/:/etc/awning/ -e filename=/etc/awning/tb6612fng_motors.config  grro/pi_awning_webthing:0.2.0
```

**PIP approach**
```
sudo pip install pi-awning-webthing
```

After this installation you may start the webthing http endpoint inside your python code or via command line using
```
sudo awning --command listen--port 9500 --filename /etc/awning/tb6612fng_motors.config
```
Here, the webthing API will be bind on the local port 9500 

Alternatively to the *listen* command, you can use the *register* command to register and start the webthing service as systemd unit. 
By doing this the webthing service will be started automatically on boot. Starting the server manually using the *listen* command is no longer necessary. 
```
sudo awning --command register --port 9500 --filename /etc/awning/tb6612fng_motors.config 
```

The awning service exposes an http webthing endpoint supporting the awning properties. E.g. 
```
# webthing has been started on host 192.168.0.23

curl http://192.168.0.23:9500/properties 

{
 [
    {
       "id":"urn:dev:ops:awning-TB6612FNG",
       "title":"AwningControl",
       "@context":"https://iot.mozilla.org/schemas",
       "properties":{
          "target_position":{
             "@type":"LevelProperty",
             "title":"awning lane1 target position",
             "type":"integer",
             "minimum":0,
             "maximum":100,
             "description":"awning lane1 target position",
             "links":[
                {
                   "rel":"property",
                   "href":"/0/properties/target_position"
                }
             ]
          },
          "current_position":{
             "@type":"LevelProperty",
             "title":"awning lane1 current position",
             "type":"integer",
             "minimum":0,
             "maximum":100,
             "readOnly":true,
             "description":"awning lane1 current position",
             "links":[
                {
                   "rel":"property",
                   "href":"/0/properties/current_position"
                }
             ]
          },
          "retracting":{
             "@type":"OnOffProperty",
             "title":"lane1 is retracting",
             "type":"boolean",
             "readOnly":true,
             "description":"lane1 is retracting",
             "links":[
                {
                   "rel":"property",
                   "href":"/0/properties/retracting"
                }
             ]
          },
          "extending":{
             "@type":"OnOffProperty",
             "title":"lane1 is extending",
             "type":"boolean",
             "readOnly":true,
             "description":"lane1 is extending",
             "links":[
                {
                   "rel":"property",
                   "href":"/0/properties/extending"
                }
             ]
          }
       },
       "actions":{
          
       },
       "events":{
          
       },
       "links":[
          {
             "rel":"properties",
             "href":"/0/properties"
          },
          {
             "rel":"actions",
             "href":"/0/actions"
          },
          {
             "rel":"events",
             "href":"/0/events"
          },
          {
             "rel":"alternate",
             "href":"ws://192.168.0.23:9500/0"
          }
       ],
       "description":"A web connected patio awnings controller on Raspberry Pi",
       "@type":[
          "MultiLevelSensor"
       ],
       "href":"/0",
       "base":"http://192.168.0.23:9500/0",
       "securityDefinitions":{
          "nosec_sc":{
             "scheme":"nosec"
          }
       },
       "security":"nosec_sc"
    },
    ...
 ]
}
```
