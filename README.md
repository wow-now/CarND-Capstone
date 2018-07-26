## Final project
This is the final project for SDC-ND
This project ought to be finished by team, but I tried to reach the sign up sheet and udacitie's wechat group in China and got nothing. But thanks the help of ZhengLei, He download the traffic light bag file through VPN which let me passthrough the training image for the real car. After 1 month hard work in spare time. I finally finish this project.
 All nodes in the project was implemented follow the walkthrough video.
It has one month since I start the project.

#### Zig zag and Project time consumption(one month)
1. I used VMWare to install the vm disk image and my Host(win10) to run the simulator. It runs very well at the begining, but few hours later, the network service of the VMWare in the host computer began crushed. So I have to install the vm disk image to the VirtualBox.
2. After intalled the vm disk image to the VirtualBox, another problem arised. The resolution of the lubuntu was so poor that it split the whole line of code into several lines. After several hours, I finally find the way to make it right.
3. After coding the waypoint updater and bdw node, I found the pid controller could run steadily through the whole path. But when I switched on the image option, the whole wold turned over. The PID controller never ran smooth again, the car always ran out of the road and rushed into trees or hills. I didn't realize it untill I found the latancy problem on the slack. Two solution I have to choose, install simulator to the lubuntu or find another computer with high performance. I tried the easy one. But that wouldn't work because the OPENGL version couldn't match with the lubuntu. It has only 20 days to my deadline.
4. Since I couldn't run the project on my computer, I skipped this step and began to training the traffic light image. Still there's the version problem for the training process when I tried to train the image with google API. The tensor flow installed in car and vm is v1.3, so I have to use the correct verion of API for the training. That takes several days to compile and find the correct version. Can't  download the labelImg binary file, can't compile the source code on vm, can't download the traffic light bag file. There's too many difficult to train the image. Finally I build the labelImg on another linux vm. And My friend download the bag file through VPN. 
5. The training images count from simulator I sampled is 1800(600 for each color * 3 color). It took me 16 hours for labeling and 16 hours for training. The training images count from bag I sampled is 1200(400 for each color * 3 color). It took me 12 hours for labeling and 16 hours for training. It already took 20 days to finish this step. The accuracy is 99.2% for simulator and 99.6% for bag file.
6. Finally it's the time to put all together. For my poor performance of my computer, I use workspace instead. But It still has latency problem especially on 10 o'clock am.
7. Integration test is a big trouble. It should be 99.2% accuracy in isolated objection dectection procedure, but in integration test was terrible things. Sometimes the traffic light classifiction can't work. I tuned the parameter of the system to optimize the performance, but nothing worked before the latency.
8. Finally, It could work in the simulator. Every thing is worthing this time.

#### Running with simulator:
installing ROS
(cloning the project)
cd CarND-Capstone pip install -r requirements.txt (install python dependencies)
cd CarND-Capstone/ros
catkin_make
source devel/setup.sh
roslaunch launch/styx.launch

#### Running with real car:
installing ROS
(cloning the project)
cd CarND-Capstone pip install -r requirements.txt (install python dependencies)
cd CarND-Capstone/ros
catkin_make
source devel/setup.sh
roslaunch launch/site.launch

#### Tuning parameters
To eliminate the loginfo displayed in the console, delete the  output="screen" in the launch file.
To save the camera image to the "saveImgs" folder, set self.saveImgs = True in __init__ function in file tl_detect.py.
I couldn't find parameter "isSite"  mentioned in the project introduction, instead I add parameter "isSiteP" in the launch file of tl_detector node.

