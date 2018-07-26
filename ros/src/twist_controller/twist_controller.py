
from pid import PID
from lowpass import LowPassFilter
from yaw_controller import YawController
import rospy

GAS_DENSITY = 2.858
ONE_MPH = 0.44704
MAX_SPEED = 40.0

class Controller(object):
    def __init__(self, vehicle_mass, fuel_capacity, brake_deadband, decel_limit, accel_limit, wheel_radius,
                        wheel_base, steer_ratio, max_lat_accel, max_steer_angle):
        # TODO: Implement
        self.yaw_controller = YawController(wheel_base, steer_ratio, 0.05, max_lat_accel, max_steer_angle)

        kp = 0.53
        ki = 0.001
        kd = 0.00001
        mn = -5 #Minimum throttle value
        mx = 1 #maximum throttle value
        self.throttle_controller = PID(kp, ki, kd, mn, mx)

        tau = 0.22
        ts = 0.02
        self.vel_lpf = LowPassFilter(tau, ts)
        self.yaw_lp = LowPassFilter(0.2, 0.1)
        self.brake_lp = LowPassFilter(0.045, 0.02)

        self.vehicle_mass = vehicle_mass
        self.fuel_capacity = fuel_capacity
        self.brake_deadband = brake_deadband
        self.decel_limit = decel_limit
        self.accel_limit = accel_limit
        self.wheel_radius = wheel_radius

        self.total_mass = vehicle_mass + fuel_capacity * GAS_DENSITY

        self.last_time = None

    def control(self, current_vel, dbw_enabled, linear_vel, angular_vel):
        # TODO: Change the arg, kwarg list to suit your needs
        # Return throttle, brake, steer

        if not dbw_enabled:
            self.throttle_controller.reset()
            self.yaw_lp.filt(0.0)
            self.brake_lp.set(0.0)
            return 0., 0., 0.
        
        if self.last_time is None:
            self.last_time = rospy.get_time()
            return 0., 0., 0.
        
        
        linear_vel2 = linear_vel
        #if linear_vel < 0.:
        #    linear_vel = 0
        
        #current_vel = self.vel_lpf.filt(current_vel)

        ''' rospy.logwarn("angular vel: {0}".format(angular_vel))
            rospy.logwarn("Target vel: {0}".format(linear_vel))
            rospy.logwarn("Target angular: {0}".format(angular_vel))
            rospy.logwarn("Current vel: {0}".format(current_vel))
            rospy.logwarn("Filtered vel: {0}".format(self.vel_lpf.get()))'''
        current_time = rospy.get_time()
        sample_time = current_time - self.last_time
        self.last_time = current_time

        steer_err = self.yaw_controller.get_steering(linear_vel, angular_vel, current_vel)
        steering = self.yaw_lp.filt(steer_err)
        vel_error = min(linear_vel, MAX_SPEED*ONE_MPH) - current_vel
        vel_error = max(vel_error, self.decel_limit*sample_time)
        self.last_vel = current_vel
        #rospy.loginfo("vel error:%s,time:%s, target vel:linear_vel",vel_error,sample_time)        

        throttle = self.throttle_controller.step(vel_error, sample_time)
        brake = 0
        throttle2 = throttle

        sss = "a"
        '''if linear_vel == 0. and current_vel < 0.1:
            throttle = 0
            brake = 701
            #rospy.loginfo("break 701")
        elif throttle < .1 and vel_error < 0:
            throttle = 0
            decel = max(vel_error, self.decel_limit)
            brake = 0.8*abs(decel)* self.total_mass * self.wheel_radius # Torque
            rospy.loginfo("linear_vel:{0}   current_vel:{1}  vel_err:{2}  throttle:{3}    decel:{4}   brake:{5}".format(linear_vel,current_vel,vel_error,throttle2, decel,brake))
        '''
        #rospy.loginfo("linear_vel:%s   current_vel:%s  throttle:%s",linear_vel,current_vel,throttle2)


        if (vel_error > 0.0):
            self.brake_lp.set(0.)
            brake = 0.
        else:
            
            decel = max(vel_error,self.decel_limit * sample_time)
            brake = abs(decel) * 0.80 * self.total_mass * self.wheel_radius # Torque
            #brake = self.brake_lp.filt(brake)
            #rospy.loginfo("brake:%s",brake)

            throttle = 0.0
            if (brake <= 0.5):
                brake = 0.5

            if linear_vel <= 0.1:
                brake = 800
            
        rospy.loginfo('linearV:%s   currentV:%s  brake:%s  throttle:%s    decel:%s  steer:%s',linear_vel2,current_vel,brake,throttle2, self.decel_limit,steer_err)
            #sss = "linearV:{0}   currentV:{1}  brake:{2}  throttle:{3}  decel:{4}".format(linear_vel,current_vel,brake,throttle2, decel)
            #print(sss)
        return throttle, brake, steering
    
