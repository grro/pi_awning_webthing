# pi_anwing_webthing
A web connected patio awnings controller on Raspberry Pi

Currently supported are [TB6612FNG driven](https://www.pololu.com/product/713) motors such 
as [DGO-3512ADA](https://www.ebay.co.uk/itm/Gear-Motor-Direct-Current-6-12V-Electric-With-Removable-Crank-DGO-3512ADA-/183375290396). 
The concrete motor configuration(s) are defined by using a config file. For TB6612FNG driven motors the filename has to include 
the term *tb6612fng* such as tb6612fng_motors.config  
```
# name, gpio_forward, gpio_backward, step_duration_in_sec
lane1, 2, 3, 0.5
lane2, 19, 26, 0.5
lane3, 5, 6, 0.5
lane4, 10, 9, 0.5
```

Regarding the hardware setup and wiring please refer [example hardware setup](dgo-3512ada.md)

To install this software you may use [PIP](https://realpython.com/what-is-pip/) package manager such as shown below
```
sudo pip install pi_anwing_webthing
```

After this installation you may start the webthing http endpoint inside your python code or via command line using
```
sudo anwing --command listen --port 9500 --filename /etc/anwing/tb6612fng_motors.config 
```
Here, the webthing API will be bind to the local port 9500 

Alternatively to the *listen* command, you can use the *register* command to register and start the webthing service as systemd unit. 
By doing this the webthing service will be started automatically on boot. Starting the server manually using the *listen* command is no longer necessary. 
```
sudo anwing --command register --port 9500 --filename /etc/anwing/tb6612fng_motors.config 
```

The anwing service exposes an http webthing endpoint supporting the anwing properties. E.g. 
```
# webthing has been started on host 192.168.0.23

curl http://192.168.0.23:9500/properties 

{
   ...
}
```