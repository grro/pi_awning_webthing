# example hardware setup

Here the setup of a motorized awning with 4 lanes is descriped
![anwing picture](awning_small.jpg)

The awning will be extended and retracted by using a bidirectional DC motor [DGO-3512ADA](https://www.ebay.co.uk/itm/Gear-Motor-Direct-Current-6-12V-Electric-With-Removable-Crank-DGO-3512ADA-/183375290396) motor is used. 
To control the motor the [TB6612FNG](https://www.pololu.com/product/713) dual motor driver is used. 

Extracting and expanding is time-controlled. This means the motor will be supplied with forward or backward power for a certain period of time. 
To save the motor a limit switch is used which will interrupt the power circuit, if the end position is reached.
 
![awning picture](switch_small.jpg)

The motor driver is connected with a Rasperry Pi Zero using the layout as shown below:
 
![circuit board](circuitboard.png)