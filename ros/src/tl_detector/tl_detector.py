#!/usr/bin/env python
import rospy
import numpy as np
from std_msgs.msg import Int32
from geometry_msgs.msg import PoseStamped, Pose
from styx_msgs.msg import TrafficLightArray, TrafficLight
from styx_msgs.msg import Lane
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from light_classification.tl_classifier import TLClassifier
import tf
import cv2
import yaml
from scipy.spatial import KDTree
import os

STATE_COUNT_THRESHOLD = 4

class TLDetector(object):
    def __init__(self):
        rospy.init_node('tl_detector')

        self.pose = None
        self.waypoints = None
        self.waypoints_2d = None
        self.waypoint_tree = None

        self.stateCount = 0

        self.image_count = 0

        self.state = TrafficLight.RED
        self.last_state = TrafficLight.UNKNOWN

        self.last_wp = -1
        self.state_count = 0

        self.camera_image = None
        self.lights = []

        self.saveImgs = True
        if self.saveImgs:
            if not (os.path.exists("./saveImgs")):
                os.mkdir("./saveImgs")
        self.saveCount= 0
        
        config_string = rospy.get_param("/traffic_light_config")
        #config_string2 = config_string
        #rospy.loginfo("+++++++++++++++Using simulator+++++++++++++++%s",config_string)
        self.config = yaml.load(config_string)
        
        #rospy.loginfo("+++++++++++++++Using simulator+++++++++++++++%s",self.config) 
        isSite = bool(rospy.get_param("~is_siteP", True))
        if  isSite:
            self.usingSimulator = False
            rospy.loginfo("+++++++++++++++Using simulator+++++++++++++++") 
        else:
            self.usingSimulator = True
            rospy.loginfo("+++++++++++++++Using simulator+++++++++++++++")
            
        self.usingSystemLightState = 0
        #self.usingSimulator = 0 if self.config['is_site'] else 1
        #self.usingSimulator = bool(rospy.get_param("~is_siteP", False))
        

        self.bridge = CvBridge()
        self.light_classifier = TLClassifier(self.usingSimulator)
        self.listener = tf.TransformListener()

        self.stop_closest_waypoint = []

        sub1 = rospy.Subscriber('/current_pose', PoseStamped, self.pose_cb)
        sub2 = rospy.Subscriber('/base_waypoints', Lane, self.waypoints_cb)

        '''
        /vehicle/traffic_lights provides you with the location of the traffic light in 3D map space and
        helps you acquire an accurate ground truth data source for the traffic light
        classifier by sending the current color state of all traffic lights in the
        simulator. When testing on the vehicle, the color state will not be available. You'll need to
        rely on the position of the light and the camera image to predict it.
        '''
        sub3 = rospy.Subscriber('/vehicle/traffic_lights', TrafficLightArray, self.traffic_cb)
        #sub6 = rospy.Subscriber('/image_color', Image, self.image_cb)
        sub6 = rospy.Subscriber('/image_color', Image, self.image_cb,queue_size=1, buff_size=2*52428800)
        
        self.upcoming_red_light_pub = rospy.Publisher('/traffic_waypoint', Int32, queue_size=1)


        self.lastTime = rospy.get_time()      
        
        
        
        rate = rospy.Rate(200)
        while not rospy.is_shutdown():
            if self.pose and self.waypoints and self.lights:
                #get closest waypoint
                #closest_waypoint_idx = self.get_closest_waypoint_idx()
                #rospy.loginfo('closest_waypoint_index:%s', closest_waypoint_idx)
                #self.publish_waypoints(closest_waypoint_idx)
                
                self.InitializeImage = True
                light_wp, state = self.process_traffic_lights()
                self.find_traffic_lights(light_wp, state)
                rospy.loginfo("=============finish initialize image===========")
                self.InitializeImage = False
                break
            rate.sleep()
        
        rospy.spin()


    def pose_cb(self, msg):
        self.pose = msg

    def waypoints_cb(self, waypoints):
        self.waypoints = waypoints
        if not self.waypoints_2d:
            self.waypoints_2d = [[waypoint.pose.pose.position.x, waypoint.pose.pose.position.y] for waypoint in waypoints.waypoints]
            self.waypoint_tree = KDTree(self.waypoints_2d)

    def traffic_cb(self, msg):
        self.lights = msg.lights

    def image_cb(self, msg):
        """Identifies red lights in the incoming camera image and publishes the index
            of the waypoint closest to the red light's stop line to /traffic_waypoint

        Args:
            msg (Image): image from car-mounted camera

        """
        self.has_image = True
        
        ThisTime = rospy.get_time()
        #rospy.loginfo("Time elapsed:%s",ThisTime - self.lastTime)
        self.lastTime = ThisTime
        self.image_count = self.image_count + 1
        
        THRESHOLD_SAMPLE = 1
        #if self.usingSimulator:
            #THRESHOLD_SAMPLE = 1 

        if (self.image_count >= THRESHOLD_SAMPLE):
            self.lastTime = rospy.get_time()
            self.image_count = 0
            self.has_image = True
            self.camera_image = msg
            light_wp, state = self.process_traffic_lights()
            if (state != 0)and self.saveImgs:
                iimage = self.bridge.imgmsg_to_cv2(self.camera_image, "rgb8")
                h,w,_ = iimage.shape
                #rospy.loginfo("image width:%s height:%s state:%s",w,h,state)
                if self.usingSimulator:            
                    iimage = iimage[0:int(0.7*h),0:w]
                else:
                    iimage = iimage[0:int(0.7*h),50:int(w-50)]
                self.saveImags(iimage, state)
            ThisTime = rospy.get_time()
            #rospy.loginfo("Time elapsed:%s, light state:%s",ThisTime - self.lastTime,state)

            self.find_traffic_lights(light_wp, state)
            
        
    def saveImags(self, image, state):
        dictTL = {0:"R",1:"Y",2:"G",4:"U"}
        takeImage = image
        if not self.usingSimulator:
            lsImageName ="./saveImgs/image0{0:0>5}.jpg".format(self.saveCount)
            #rospy.loginfo("save image:%s",lsImageName)
            cv2.imwrite(lsImageName, takeImage)
        else:
            lsImageName ="./saveImgs/{0}_image6{1:0>5}.jpg".format(dictTL[state],self.saveCount)
            rospy.loginfo("save image:%s",lsImageName)
            cv2.imwrite(lsImageName, takeImage)
        self.saveCount += 1
        

    def find_traffic_lights(self,light_wp, state):
        
        '''
        Publish upcoming red lights at camera frequency.
        Each predicted state has to occur `STATE_COUNT_THRESHOLD` number
        of times till we start using it. Otherwise the previous stable state is
        used.
        '''
        if state == TrafficLight.YELLOW:
            state = TrafficLight.RED
            
            
        if self.InitializeImage:
            self.last_wp = light_wp
            self.upcoming_red_light_pub.publish(Int32(light_wp))
            return
            
        if self.state != state:
            self.state_count = 0
            self.state = state
        elif self.state_count >= STATE_COUNT_THRESHOLD:
            self.last_state = self.state
            
            light_wp = light_wp if state == TrafficLight.RED else -1
            self.last_wp = light_wp
            rospy.loginfo("---light changed,wp is:%s state:%s s state:%s",light_wp,state,self.state)
            self.upcoming_red_light_pub.publish(Int32(light_wp))
            
        else:
            rospy.loginfo("---light remained,wp is:%s state:%s s state:%s",self.last_wp,state,self.state)
            self.upcoming_red_light_pub.publish(Int32(self.last_wp))
            

        self.state_count += 1
            
        

    def get_closest_waypoint(self, x,y):
        """Identifies the closest path waypoint to the given position
            https://en.wikipedia.org/wiki/Closest_pair_of_points_problem
        Args:
            pose (Pose): position to match a waypoint to

        Returns:
            int: index of the closest waypoint in self.waypoints

        """
        #TODO implement
        closest_idx = self.waypoint_tree.query([x,y],1)[1]

        # check if the closest is ahed or behind the vehicle
        closest_coord = self.waypoints_2d[closest_idx]
        prev_coord = self.waypoints_2d[closest_idx - 1]

        closest_v = np.array(closest_coord)
        prev_v = np.array(prev_coord)
        pos_v = np.array([x, y] )

        val = np.dot(closest_v - prev_v, pos_v - closest_v)

        if val > 0:
            closest_idx = (closest_idx + 1) % len(self.waypoints_2d)
        
        
        return closest_idx

    def get_light_state(self, light):
        """Determines the current color of the traffic light

        Args:
            light (TrafficLight): light to classify

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """
        if self.usingSystemLightState > 0:
            if (self.stateCount > 2):
                #rospy.loginfo("light state:{0}".format(light.state))
                self.stateCount = 0
                
            self.stateCount = self.stateCount + 1    
            return light.state

        
        cv_image = self.bridge.imgmsg_to_cv2(self.camera_image, "rgb8")
        #cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        #narrow down seaching area of the image    
        
        h,w,_ = cv_image.shape
        if self.usingSimulator:            
            cv_image = cv_image[0:int(0.7*h),0:w]
        else:
            cv_image = cv_image[0:int(0.7*h),0:w]
            
        #Get classification
        return self.light_classifier.get_classification(cv_image)
    
    def process_traffic_lights(self):
        """Finds closest visible traffic light, if one exists, and determines its
            location and color

        Returns:
            int: index of waypoint closes to the upcoming stop line for a traffic light (-1 if none exists)
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """
        light = None
        light_wp = None
        # List of positions that correspond to the line to stop in front of for a given intersection
        stop_line_positions = self.config['stop_line_positions']
        if (self.pose):
            car_position = self.get_closest_waypoint(self.pose.pose.position.x,self.pose.pose.position.y)

            #TODO find the closest visible traffic light (if one exists)
            diff = 200
            
            #for fast get
            if len(self.stop_closest_waypoint) == 0:
                for i, lightP in enumerate(self.lights):
                    line = stop_line_positions[i]
                    self.stop_closest_waypoint.append(self.get_closest_waypoint(line[0] , line[1]))
                    
            #rospy.loginfo("len of waypoints:%s  car wp:%s",diff,car_position)
            for i, lightP in enumerate(self.lights):
                tmp_waypoint_idx = self.stop_closest_waypoint[i]
                d = tmp_waypoint_idx - car_position
                if d>=0 and d< diff:
                    diff = d
                    light = lightP
                    light_wp = tmp_waypoint_idx
        
        if light:
            rospy.loginfo("car pos:%s closest light idx %s diff:%s" ,car_position,light_wp, diff)
            if self.InitializeImage:
                #for first image latency
                state = 0 
            else:
                state = self.get_light_state(light)
            
            return light_wp, state

        #self.waypoints = None
        return -1, TrafficLight.UNKNOWN


if __name__ == '__main__':
    try:
        TLDetector()
    except rospy.ROSInterruptException:
        rospy.logerr('Could not start traffic node.')
