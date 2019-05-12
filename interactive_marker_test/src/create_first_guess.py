#!/usr/bin/env python

# ------------------------
#    IMPORT MODULES      #
# ------------------------
import argparse
from interactive_markers.interactive_marker_server import *
from urdf_parser_py.urdf import URDF
import rospkg
from Sensor import *

# ------------------------
#      BASE CLASSES      #
# ------------------------

# ------------------------
#      GLOBAL VARS       #
# ------------------------

server = None
menu_handler = MenuHandler()
br = tf.TransformBroadcaster()
marker_poses = []
robot = []
optimization_parent_link = ""


# ------------------------
#      FUNCTIONS         #
# ------------------------

def menuFeedback(feedback):
    print('called menu')
    # global handle, robot, optimization_parent_link
    # handle = feedback.menu_entry_id
    # listener2 = TransformListener()
    # rospy.sleep(1)
    # if handle == 1:
    #     for joint in robot.joints:
    #         for sensor in robot.sensors:
    #             if sensor.parent == joint.child:
    #                 optimization_parent_link = joint.parent
    #         for mp in marker_poses:
    #             (trans, rot) = listener2.lookupTransform(optimization_parent_link, mp.child_frame_id, rospy.Time(0))
    #             if joint.child + "_first_guess" == mp.child_frame_id:
    #                 joint.origin.xyz[0] = trans[0]
    #                 joint.origin.xyz[1] = trans[1]
    #                 joint.origin.xyz[2] = trans[2]
    #                 joint.origin.rpy[0] = rot[0]
    #                 joint.origin.rpy[1] = rot[1]
    #                 joint.origin.rpy[2] = rot[2]

    for sensor in sensors:
        for joint in robot.joints:  # find corresponding joint for this sensor
            if sensor.opt_child_link == joint.child and sensor.opt_parent_link == joint.parent:
                trans = sensor.optT.getTranslation()
                euler = sensor.optT.getEulerAngles()
                joint.origin.xyz[0] = trans[0]
                joint.origin.xyz[1] = trans[1]
                joint.origin.xyz[2] = trans[2]
                joint.origin.rpy[0] = euler[0]
                joint.origin.rpy[1] = euler[1]
                joint.origin.rpy[2] = euler[2]


    xml_string = robot.to_xml_string()
    filename = rospack.get_path('interactive_marker_test') + "/urdf/atlas2_macro_first_guess.urdf.xacro"
    f = open(filename, "w")
    f.write(xml_string)
    f.close()
    print('Saved first guess to file ' + filename)


def initMenu():
    menu_handler.insert("Save sensors configuration", callback=menuFeedback)


if __name__ == "__main__":

    # Parse command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-w", "--world_link", help='Name of the reference frame wich is common to all sensors. Usually '
                                               'it is the world or base_link.', type=str, required=True)
    args = vars(ap.parse_args())

    # Initialize ROS stuff
    rospy.init_node("sensors_first_guess")
    # br = TransformBroadcaster()
    listener = TransformListener()
    rate = rospy.Rate(10.0)  # 10 Hz
    robot_description = rospy.get_param('/robot_description')
    rospack = rospkg.RosPack()  # get an instance of RosPack with the default search paths
    server = InteractiveMarkerServer("sensors_first_guess")
    rospy.sleep(0.5)

    # Read robot description from param /robot_description
    robot = URDF.from_parameter_server()
    # robot = URDF.from_xml_file(rospack.get_path('interactive_marker_test') + "/urdf/atlas_macro.urdf.xacro")

    # Process robot description and create an instance of class Sensor for each sensor
    number_of_sensors = 0
    sensors = []

    # parsing of robot description
    for robot_sensor in robot.sensors:

        print('\n\nSensor name is ' + robot_sensor.name)

        # if not robot_sensor.name == 'right_laser':
        #     continue

        sensor_link = robot_sensor.name
        print('Sensor data reference frame is ' + sensor_link)

        opt_child_link = robot_sensor.parent
        print('Optimization child is ' + opt_child_link)

        for joint in robot.joints:
            if robot_sensor.parent == joint.child:
                opt_parent_link = joint.parent

        print('Optimization parent ' + opt_parent_link)

        sensors.append(Sensor(robot_sensor.name, server, menu_handler, args['world_link'], opt_parent_link,
                              opt_child_link, sensor_link))

    print('Number of sensors: ' + str(len(sensors)))
    initMenu()
    server.applyChanges()
    print('Changes applied ...')

    rospy.spin()
