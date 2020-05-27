import copy
import json
import os
import shutil
import subprocess
import time

import yaml

import cv2
import tf
import numpy
import ros_numpy

from datetime import datetime

from cv_bridge import CvBridge
from colorama import Style, Fore
from interactive_markers.menu_handler import *
from rospy_message_converter import message_converter
from tf.listener import TransformListener
from sensor_msgs.msg import *

from utilities import printRosTime, getMaxTimeDelta, getAverageTime, getMaxTime
from interactive_calibration.utilities import loadJSONConfig
from interactive_calibration.interactive_data_labeler import InteractiveDataLabeler


def execute(cmd, blocking=True, verbose=True):
    """ @brief Executes the command in the shell in a blocking or non-blocking manner
        @param cmd a string with teh command to execute
        @return
    """
    if verbose:
        print "Executing command: " + cmd
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if blocking:  # if blocking is True:
        for line in p.stdout.readlines():
            if verbose:
                print line,
            p.wait()


class DataCollectorAndLabeler:

    def __init__(self, args, server, menu_handler):
        # def __init__(self, output_folder, server, menu_handler, marker_size, calibration_file, args):

        interactive = sys.stdin.isatty() and sys.stdout.isatty()
        print("is interactive = " + str(interactive))
        exit(0)

        if os.path.exists(args['output_folder']):
            now = datetime.now()
            dt_string = now.strftime("%Y-%m-%d-%H-%M-%S")
            basename = os.path.basename(args['output_folder'])
            new_folder = '/tmp/dataset_backups/' + basename + '_' + dt_string
            print('Dataset ' + Fore.YELLOW + args['output_folder'] + Style.RESET_ALL +
                  ' exists. Moving it to a new folder: ' + Fore.YELLOW + new_folder + Style.RESET_ALL)

            # shutil.copy2(args['output_folder'], new_folder)
            execute('mv ' + args['output_folder'] + ' ' + new_folder, verbose=True)
        #     shutil.rmtree(args['output_folder'])  # Delete old folder
        #
        #     os.mkdir(args['output_folder'])  # Recreate the folder
        # elif sys.stdout.isatty():  # check if this was called from an interactive terminal (i.e., not from roslaunch )
        #     while True:
        #         msg = Fore.YELLOW + "To continue, the directory '{}' will be deleted.\n"
        #         msg = msg + "Do you wish to continue? [y/N] " + Style.RESET_ALL
        #         answer = raw_input(msg.format(args['output_folder']))
        #         if len(answer) > 0 and answer[0].lower() in ('y', 'n'):
        #             if answer[0].lower() == 'n':
        #                 sys.exit(1)
        #             else:
        #                 break
        #         else:
        #             sys.exit(1)  # defaults to N
        #
        #     shutil.rmtree(args['output_folder'])  # Delete old folder
        #     os.mkdir(args['output_folder'])  # Recreate the folder
        # else:
        #     print(Fore.YELLOW + 'Dataset ' + args['output_folder'] +
        #           'exists. If you want to delete the existing folder, add the "--overwrite" (or overwrite:=true for '
        #           'launch files) flag.' + Style.RESET_ALL)
        #     sys.exit(1)  # defaults to N

        exit(0)

        self.output_folder = args['output_folder']
        self.listener = TransformListener()
        self.sensors = {}
        self.sensor_labelers = {}
        self.server = server
        self.menu_handler = menu_handler
        self.data_stamp = 0
        self.collections = {}
        self.bridge = CvBridge()

        # self.config = loadJSONConfig(calibration_file)
        self.config = yaml.load(open(args['calibration_file']), Loader=yaml.CLoader)
        if self.config is None:
            sys.exit(1)  # loadJSON should tell you why.

        self.world_link = self.config['world_link']

        # Add sensors
        print(Fore.BLUE + 'Sensors:' + Style.RESET_ALL)
        print('Number of sensors: ' + str(len(self.config['sensors'])))

        # Go through the sensors in the calib config.
        for sensor_key, value in self.config['sensors'].items():

            # Create a dictionary that describes this sensor
            sensor_dict = {'_name': sensor_key, 'parent': value['link'],
                           'calibration_parent': value['parent_link'],
                           'calibration_child': value['child_link']}

            # TODO replace by utils function
            print("Waiting for message " + value['topic_name'] + ' ...')
            msg = rospy.wait_for_message(value['topic_name'], rospy.AnyMsg)
            print('... received!')
            connection_header = msg._connection_header['type'].split('/')
            ros_pkg = connection_header[0] + '.msg'
            msg_type = connection_header[1]
            print('Topic ' + value['topic_name'] + ' has type ' + msg_type)
            sensor_dict['topic'] = value['topic_name']
            sensor_dict['msg_type'] = msg_type

            # If topic contains a message type then get a camera_info message to store along with the sensor data
            if sensor_dict['msg_type'] == 'Image':  # if it is an image must get camera_info
                sensor_dict['camera_info_topic'] = os.path.dirname(sensor_dict['topic']) + '/camera_info'
                from sensor_msgs.msg import CameraInfo
                print('Waiting for camera_info message on topic ' + sensor_dict['camera_info_topic'] + ' ...')
                camera_info_msg = rospy.wait_for_message(sensor_dict['camera_info_topic'], CameraInfo)
                print('... received!')
                from rospy_message_converter import message_converter
                sensor_dict['camera_info'] = message_converter.convert_ros_message_to_dictionary(camera_info_msg)

            # Get the kinematic chain form world_link to this sensor's parent link
            now = rospy.Time()
            print('Waiting for transformation from ' + value['link'] + ' to ' + self.world_link)
            self.listener.waitForTransform(value['link'], self.world_link, now, rospy.Duration(5))
            print('... received!')
            chain = self.listener.chain(value['link'], now, self.world_link, now, self.world_link)

            chain_list = []
            for parent, child in zip(chain[0::], chain[1::]):
                key = self.generateKey(parent, child)
                chain_list.append({'key': key, 'parent': parent, 'child': child})

            sensor_dict['chain'] = chain_list  # Add to sensor dictionary
            self.sensors[sensor_key] = sensor_dict

            sensor_labeler = InteractiveDataLabeler(self.server, self.menu_handler, sensor_dict,
                                                    args['marker_size'], self.config['calibration_pattern'])

            self.sensor_labelers[sensor_key] = sensor_labeler

            print('Setup for sensor ' + sensor_key + ' is complete.')
            print(Fore.BLUE + sensor_key + Style.RESET_ALL + ':\n' + str(sensor_dict))

        # print('sensor_labelers:')
        # print(self.sensor_labelers)

        self.abstract_transforms = self.getAllAbstractTransforms()
        # print("abstract_transforms = " + str(self.abstract_transforms))

    def getTransforms(self, abstract_transforms, time=None):
        transforms_dict = {}  # Initialize an empty dictionary that will store all the transforms for this data-stamp

        if time is None:
            time = rospy.Time.now()

        for ab in abstract_transforms:  # Update all transformations
            self.listener.waitForTransform(ab['parent'], ab['child'], time, rospy.Duration(1.0))
            (trans, quat) = self.listener.lookupTransform(ab['parent'], ab['child'], time)
            key = self.generateKey(ab['parent'], ab['child'])
            transforms_dict[key] = {'trans': trans, 'quat': quat, 'parent': ab['parent'], 'child': ab['child']}

        return transforms_dict

    def lockAllLabelers(self):
        for sensor_name, sensor in self.sensors.iteritems():
            self.sensor_labelers[sensor_name].lock.acquire()
        print("Locked all labelers")

    def unlockAllLabelers(self):
        for sensor_name, sensor in self.sensors.iteritems():
            self.sensor_labelers[sensor_name].lock.release()
        print("Unlocked all labelers")

    def getLabelersTimeStatistics(self):
        stamps = []  # a list of the several time stamps of the stored messages
        for sensor_name, sensor in self.sensors.iteritems():
            stamps.append(copy.deepcopy(self.sensor_labelers[sensor_name].msg.header.stamp))

        max_delta = getMaxTimeDelta(stamps)
        # TODO : this is because of Andre's bag file problem. We should go back to the getAverageTime
        # average_time = getAverageTime(stamps)  # For looking up transforms use average time of all sensor msgs
        average_time = getMaxTime(stamps)  # For looking up transforms use average time of all sensor msgs

        print('Times:')
        for stamp, sensor_name in zip(stamps, self.sensors):
            printRosTime(stamp, prefix=sensor_name + ': ')

        return stamps, average_time, max_delta

    def saveCollection(self):

        # --------------------------------------
        # Collect sensor data and labels (images, laser scans, etc)
        # --------------------------------------

        # Lock the semaphore for all labelers
        self.lockAllLabelers()

        # Analyse message time stamps and decide if collection can be stored
        stamps, average_time, max_delta = self.getLabelersTimeStatistics()

        if max_delta is not None:  # if max_delta is None (only one sensor), continue
            if max_delta.to_sec() > float(self.config['max_duration_bekween_msgs']):  # times are close enough?
                rospy.logwarn('Max duration between msgs in collection is ' + str(max_delta.to_sec()) +
                              '. Not saving collection.')
                self.unlockAllLabelers()
                return None
            else:  # test passed
                rospy.loginfo('Max duration between msgs in collection is ' + str(max_delta.to_sec()))

        # Collect all the transforms
        transforms = self.getTransforms(self.abstract_transforms, average_time)  # use average time of sensor msgs
        printRosTime(average_time, "Collected transforms for time ")

        all_sensor_data_dict = {}
        all_sensor_labels_dict = {}
        for sensor_name, sensor in self.sensors.iteritems():
            print('collect sensor: ' + sensor_name)

            msg = copy.deepcopy(self.sensor_labelers[sensor_name].msg)
            labels = copy.deepcopy(self.sensor_labelers[sensor_name].labels)

            # TODO add exception also for point cloud and depth image
            # Update sensor data ---------------------------------------------
            if sensor['msg_type'] == 'Image':  # Special case of requires saving image data as png separate files
                cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")  # Convert to opencv image and save image to disk
                filename = self.output_folder + '/' + sensor['_name'] + '_' + str(self.data_stamp) + '.jpg'
                filename_relative = sensor['_name'] + '_' + str(self.data_stamp) + '.jpg'
                cv2.imwrite(filename, cv_image)

                image_dict = message_converter.convert_ros_message_to_dictionary(
                    msg)  # Convert sensor data to dictionary
                del image_dict['data']  # Remove data field (which contains the image), and replace by "data_file"
                image_dict['data_file'] = filename_relative  # Contains full path to where the image was saved

                # Update the data dictionary for this data stamp
                all_sensor_data_dict[sensor['_name']] = image_dict

            else:
                # Update the data dictionary for this data stamp
                all_sensor_data_dict[sensor['_name']] = message_converter.convert_ros_message_to_dictionary(msg)

            # Update sensor labels ---------------------------------------------
            if sensor['msg_type'] in ['Image', 'LaserScan', 'PointCloud2']:
                all_sensor_labels_dict[sensor_name] = labels
            else:
                raise ValueError('Unknown message type.')

        collection_dict = {'data': all_sensor_data_dict, 'labels': all_sensor_labels_dict, 'transforms': transforms}
        self.collections[self.data_stamp] = collection_dict
        self.data_stamp += 1

        # Save to json file
        D = {'sensors': self.sensors, 'collections': self.collections, 'calibration_config': self.config}
        self.createJSONFile(self.output_folder + '/data_collected.json', D)

        self.unlockAllLabelers()

    def getAllAbstractTransforms(self):

        # Get a list of all transforms to collect
        transforms_list = []

        now = rospy.Time.now()
        all_frames = self.listener.getFrameStrings()

        for frame in all_frames:
            # print('Waiting for transformation from ' + frame + ' to ' + self.world_link + '(max 3 secs)')
            try:
                self.listener.waitForTransform(frame, self.world_link, now, rospy.Duration(3))
                chain = self.listener.chain(frame, now, self.world_link, now, self.world_link)
            except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
                rospy.logerr('Could not get transform from ' + frame + ' to ' + self.world_link + '(max 3 secs)')
                continue

            for idx in range(0, len(chain) - 1):
                parent = chain[idx]
                child = chain[idx + 1]
                transforms_list.append({'parent': parent, 'child': child, 'key': self.generateKey(parent, child)})

        # https://stackoverflow.com/questions/31792680/how-to-make-values-in-list-of-dictionary-unique
        uniq_l = list(map(dict, frozenset(frozenset(i.items()) for i in transforms_list)))
        return uniq_l  # get unique values

    def createJSONFile(self, output_file, D):
        print("Saving the json output file to " + str(output_file) + ", please wait, it could take a while ...")
        f = open(output_file, 'w')
        json.encoder.FLOAT_REPR = lambda f: ("%.6f" % f)  # to get only four decimal places on the json file
        print >> f, json.dumps(D, indent=2, sort_keys=True)
        f.close()
        print("Completed.")

    @staticmethod
    def generateKey(parent, child, suffix=''):
        return parent + '-' + child + suffix
