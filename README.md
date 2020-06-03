# <img align="left" width="257" height="215" src="https://github.com/lardemua/atom/blob/master/docs/logo2.png?raw=true/514/431"> ATOM Calibration 
###### A Calibration Framework using the **A**tomic **T**ransformation **O**ptimization **M**ethod 

Atom is a set of calibration tools for multi-sensor, multi-modal, robotic systems. 

It is based on the optimization of atomic transformations as provided by a ros based robot description. 
Moreover, **ATOM** provides several scripts to facilitate all the steps of a calibration procedure. 

# How to Use - Quick Start

Unlike most other calibration approaches, **ATOM** offers tools to address the complete calibration pipeline:
1. **Create a calibration package** for you robotic system
   ```bash
   rosrun atom_calibration create_calibration_pkg --name <your_robot_calibration>
   ```
2. **Configure your calibration package** - edit the file 
_<your_robot_calibration>/calibration/config.yml_ with your system information.
   ```bash
   rosrun <your_robot_calibration> configure 
   ```
3. **Set initial estimate** - deployment of interactive tools based on rviz that allow the user to set the pose of the sensors to be calibrated, while receiving visual feedback;
   ```bash
   roslaunch <your_robot_calibration> set_initial_estimate.launch 
   ```
4. **Collect Data** - Extraction of snapshots of data (ta.k.a., collections)
   ```bash
   roslaunch <your_robot_calibration> collect_data.launch 
   ```

# System calibration - Detailed Description

To calibrate your robot you must define your robotic system, (e.g. <your_robot>). You should also have a **system description** in the form of an urdf or a xacro file(s). This is normally stored in a ros package named **<your_robot>_description**. 

Finally, **ATOM** requires a bagfile with a recording of the data from the sensors you wish to calibrate. Transformations in the bagfile (i.e. topics /tf and /tf_static) will be ignored, so that they do not collide with the ones being published by the _robot_state_publisher_. Thus, if your robotic system contains moving parts, the bagfile should also record the _sensor_msgs/JointState_ message. 

It is also possible to record compressed images, since **ATOM** can decompress them while playing back the bagfile.

## Creating a calibration package

To start you should create a calibration ros package specific for your robot. **ATOM** provides a script for this:
```bash
rosrun atom_calibration create_calibration_pkg --name <your_robot_calibration>
```

This will create the ros package <your_robot_calibration> in the current folder, but you can also specify the folder, e.g.:
```bash
rosrun atom_calibration create_calibration_pkg --name ~/my/path/<your_robot_calibration>
```

## Configuring a calibration package

Once your calibration package is created you will have to configure the calibration procedure by editing the 
_<your_robot_calibration>/calibration/config.yml_ file with your system information. Here is an example of a [config.yml](templates/config.yml) file.

After filling the config.yml file, you can run the package configuration:

```bash
rosrun <your_robot_calibration> configure 
```

This will create a set of files for launching the system, configuring rviz, etc.

## Set initial estimate

Iterative optimization methods are often sensitive to the initial parameter configuration. Here, the optimization parameters represent the poses of each sensor. **ATOM** provides an interactive framework based on rviz which allows the user to set the pose of the sensors while having immediate visual feedback.

To set an initial estimate run:
```bash
roslaunch <your_robot_calibration> set_initial_estimate.launch 
```

Here are a couple of examples:

[Atlascar2](https://github.com/lardemua/atlascar2)  | [AgrobV2](https://github.com/aaguiar96/agrob)
------------- | -------------
<img align="center" src="https://github.com/lardemua/atom/blob/master/docs/set_initial_estimate_atlascar2.gif" width="450"/>  | <img align="center" src="https://github.com/lardemua/atom/blob/master/docs/set_initial_estimate_agrob.gif" width="450"/>

## Collect data 

To run a system calibration, one requires sensor data collected at different time instants. We refer to these as **data collections**. To collect data, the user should launch:
```bash
roslaunch <your_robot_calibration> collect_data.launch  output_folder:=<your_dataset_folder>
```

Depending on the size and number of topics in the bag file, it may be necessary (it often is) to reduce the playback rate of the bag file.
```bash
roslaunch <your_robot_calibration> collect_data.launch  output_folder:=<your_dataset_folder> bag_rate:=<playback_rate>
```

Here are some examples of the system collecting data:

[Atlascar2](https://github.com/lardemua/atlascar2)  | [AgrobV2](https://github.com/aaguiar96/agrob)
------------- | -------------
<img align="center" src="https://github.com/lardemua/atom/blob/master/docs/collect_data_atlascar2.gif" width="450"/>  | <img align="center" src="https://github.com/lardemua/atom/blob/master/docs/collect_data_agrob.gif" width="450"/>

A dataset is a folder which contains a set of collections. There, a _data_collected.json_ file stores all the information required for the calibration.

<img align="center" src="https://github.com/lardemua/atom/blob/master/docs/viewing_data_collected_json.gif" width="600"/> 



# Contributors

 * Miguel Riem Oliveira - University of Aveiro
 * Afonso Castro - University of Aveiro
 * Eurico Pedrosa - University of Aveiro
 * Tiago Madeira - University of Aveiro
 * André Aguiar - INESC TEC

# Maintainers

 * Miguel Riem Oliveira - University of Aveiro
 * Eurico Pedrosa - University of Aveiro

# AtlasCarCalibration
Reading the sensors starting position of a robot xacro file (atlas car sample) and create interactive markers associated to them.
Saving the markers final position and reopen the robot with the sensors at the updated position.

# Table of Contents

- [AtlasCarCalibration](#atlascarcalibration)
- [Table of Contents](#table-of-contents)
- [Installation](#installation)
  * [Using PR2 robot instead of AtlasCar2](#using-pr2-robot-instead-of-atlascar2)
- [Usage Instructions](#usage-instructions)
  * [For PR2 robot model](#for-pr2-robot-model)
  * [Visualizing the calibration graphs](#visualizing-the-calibration-graphs)
- [Known problems](#known-problems)
  * [urdf model not showing on rviz or urdf model showed up misplaced](#urdf-model-not-showing-on-rviz-or-urdf-model-showed-up-misplaced)
- [Recording a bag file of the ATLASCAR2](#recording-a-bag-file-of-the-atlascar2)
- [Run cos optimization first test](#run-cos-optimization-first-test)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

# Installation

It will be needed some sensors packages.
In the same directory (catkin_ws/src):
```
git clone https://github.com/clearpathrobotics/LMS1xx.git
git clone https://github.com/ros-drivers/pointgrey_camera_driver.git
git clone https://github.com/SICKAG/sick_ldmrs_laser.git
git clone https://github.com/SICKAG/libsick_ldmrs.git
```
Also, in the same directory (catkin_ws/src), clone the atlas car model:
````
git clone https://github.com/lardemua/atlascar2.git
```` 

In order to compile this package, flycap is needed. Install from

https://flir.app.boxcn.net/v/Flycapture2SDK/folder/72274730742


To run FlyCapture2 on a Linux Ubuntu system, install the following dependencies:

```
sudo apt-get install libraw1394-11 libgtkmm-2.4-1v5 libglademm-2.4-1v5 libgtkglextmm-x11-1.2-dev libgtkglextmm-x11-1.2 libusb-1.0-0
```
And then:
```
sudo sh install_flycapture.sh
```
(See if flycap works. It probably need some updates as well)

Finally, you will need colorama:
```
sudo pip install colorama
```
## Using PR2 robot instead of AtlasCar2
If you want to try it with the PR2 robot model too, it is needed to have the robot xacro files on your catkin source.
For that, clone the package:

```
git clone https://github.com/PR2/pr2_common.git
```

# Usage Instructions
First , add this package to your catkin workspace source.

Run the command:
```
roslaunch atom_calibration atlascar2_calibration.launch 
```

Rviz will open. It is better if you check the Fixed Frame: it must be 'base_link'. 
You must also add the location and name of the file that will store the first guess data with the -f argument. 
Location is given starting from the path of the atom_calibration ros package.
Besides that, it is also required the path to the calibration JSON file.
Now you are able to see the atlas car model with the sensors in their first position.

Then, in a new terminal:
```
rosrun atom_calibration set_initial_estimate -s 0.5 -f /calibrations/atlascar2/first_guess.urdf.xacro -c ~/catkin_ws/src/AtlasCarCalibration/atom_calibration/calibrations/atlascar2/atlascar2_calibration.json
```

Now you can move the green markers and save the new sensors configuration.
Kill the booth process in the terminals, and run:

```
roslaunch atom_calibration atlascar2_calibration.launch read_first_guess:=true
```
Now you will see the atlas car model with the sensors in the updated position (don't forget: Fixed Frame should be 'base_link').

To continue the AtlasCar2 multi-modal sensors calibration, it is required to collect some sensors data and optimizing the sensors poses. This next steps are described in the README file of OptimizationUtils repository (https://github.com/miguelriemoliveira/OptimizationUtils#calibration-of-sensors-in-the-atlascar).
## For PR2 robot model
For seeing the PR2 model instead of the AtlasCar2, just run the command (it's the same but with the car_model argument set as false)
```
roslaunch atom_calibration rviz.launch car_model:=false read_first_guess:=false
```
You need to set Fixed Frame as 'base_footprint' in order to see the urdf robot model.


# Agrob

Install the agrob description package
```bash
cd <your_catkin_ws>/src
git clone https://github.com/aaguiar96/agrob
```

For running a bag file run 
```bash
roslaunch atom_calibration agrob_calibration.launch bag:=<path_to_your_bag_file>
```


## Visualizing the calibration graphs

In order to visualize the calibration graphs you may run:

```
rosrun atom_calibration draw_calibration_graph.py -w {world_frame}
```

Annotated tf trees are displayed to better understand the calibration process. Here are some examples for the PR2 robot:

![calibration_full](https://github.com/lardemua/AtlasCarCalibration/blob/master/docs/calibration_full.png) 

![calibration_per_sensor](https://github.com/lardemua/AtlasCarCalibration/blob/master/docs/calibration_per_sensor.png) 



# Known problems

## urdf model not showing on rviz or urdf model showed up misplaced

If you can't see the car on rviz or the model showed up on a wrong place, you
have to run this command before everything:

```
export LC_NUMERIC="en_US.UTF-8"
```

If this worked out, you must run always this command at the first place. To avoid this constant work, you can always
add this command to your .bashrc file (copy and paste at the end of the bashrc document).
Now you don't have to worry about this anymore!

# Recording a bag file of the ATLASCAR2

This should be echanced with the cameras.

```
rosbag record /left_laser/laserscan /right_laser/laser_scan

```
# Run cos optimization first test

```
rosrun atom_calibration first_optimization.py
```

If it not works, run first 

```
chmod +xfirst_optimization.py
```

# Convert to and from RWHE Datasets

#### To convert from an RWHE dataset run

```
rosrun atom_calibration convert_from_rwhe_dataset.py -out /home/mike/datasets/kuka_1 -rwhe /home/mike/workingcopy/RWHE-Calib/Datasets/kuka_1/ -s hand_camera -json /home/mike/catkin_ws/src/AtlasCarCalibration/atom_calibration/calibrations/rwhe_kuka/config.json 
```

Note that you must define the sensor's name with the -s argument. To run this conversion you must also have a config.json file. 
Here's what I am using, its in **calibrations/rwhe_kuka**:

```json
{
    "sensors": {
         "hand_camera": {
                "link": "hand_camera_optical",
                "parent_link": "base_link",
                "child_link": "hand_camera",
                "topic_name": "/hand_camera/image_color"
        }
    },

    "anchored_sensor": "hand_camera",
    "world_link": "base_link",
    "max_duration_between_msgs": 0.1,

    "calibration_pattern" : {
        "link": "chessboard_link",
        "parent_link": "base_link",
        "origin": [0.0, 0.0, 0.0, 1.5, 0.0, 0.0],
        "fixed": false,
        "pattern_type": "chessboard",
        "border_size": 0.5,
        "dimension": {"x": 28, "y": 17},
        "size": 0.02,
        "inner_size": 0.0000001
    }
}
```


#### To convert to an RWHE dataset run

Use this script:

```
rosrun atom_calibration convert_to_rwhe_dataset.py
```


# Convert to and from Tabb Datasets

#### To convert from an Tabb dataset run

will add this later ...

#### To convert to an Tabb dataset run

Here's an example:

```
rosrun atom_calibration convert_to_tabb_dataset.py -json /home/mike/datasets/eye_in_hand10/data_collected.json -out /home/mike/datasets/eye_in_hand10_converted_to_tabb
```


