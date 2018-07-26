from styx_msgs.msg import TrafficLight
import numpy as np
import cv2
import tensorflow as tf
from collections import defaultdict
from io import StringIO
#from matplotlib import pyplot as plt
import time
from glob import glob
import rospy

class TLClassifier(object):
    def __init__(self, abIsSimulator):
        #TODO load classifier
        #TODO load classifier
        MODEL_NAME = "SIM_TL_INFERENCE"
        MODEL_NAMES = "SITE_TL_INFERENCE"
        PATH_TO_CKPT = MODEL_NAMES + '/frozen_inference_graph.pb'
        if abIsSimulator :
            #PATH_TO_CKPT = MODEL_NAMES + '/frozen_inference_graph.pb'
            PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'

        self.detection_graph = tf.Graph()

        self.isSim = abIsSimulator
        #setting GPU
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True

        with self.detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

            self.sess = tf.Session(graph=self.detection_graph, config=config)
            # Definite input and output Tensors for detection_graph
            self.image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')
            # Each box represents a part of the image where a particular object was detected.
            self.boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')
            # Each score represent how level of confidence for each of the objects.
            # Score is shown on the result image, together with the class label.
            self.scores = self.detection_graph.get_tensor_by_name('detection_scores:0')
            self.classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
            self.num_detections = self.detection_graph.get_tensor_by_name('num_detections:0')

    def get_classification(self, image):
        """Determines the color of the traffic light in the image

        Args:
            image (cv::Mat): image containing the traffic light

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """
        #TODO implement light color prediction
        #(im_width, im_height) = image.size
        #image = np.array(image.getdata()).reshape((im_height, im_width, 3)).astype(np.uint8)
        image = np.asarray(image, dtype="uint8" )
        
        liRet = TrafficLight.UNKNOWN
        #TODO implement light color prediction
        with self.detection_graph.as_default():
            image_exp = np.expand_dims(image, axis=0)
            (boxes, scores, classes, Ndetected) = self.sess.run(
                    [self.boxes, self.scores, self.classes, self.num_detections],
                    feed_dict={self.image_tensor: image_exp})

            detect_count = Ndetected[0]
            classes = np.squeeze(classes).astype(np.int32)
            scores = np.squeeze(scores)  
            boxes = np.squeeze(boxes)
            lstClasses = classes.tolist() 
            
            lorder = np.argsort(-scores)
            scores = scores[lorder]
            classes = classes[lorder]
            
            rospy.loginfo("scores:%s boxes:%s",scores[0:3],boxes[0:1])
            rospy.loginfo("classes:%s",classes[0:3])
            if detect_count > 0 :
                maxIdx =np.argmax(scores)
                if ((scores[maxIdx] > 0.6) or (lstClasses[maxIdx]==1)):
                    liRet = int(lstClasses[maxIdx]) - 1
                    #rospy.loginfo("scroes:%s classes:%s",scores[maxIdx],lstClasses[maxIdx])


        return liRet
