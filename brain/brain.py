import socket

from message import Message
import sys
sys.path.insert(0, "DifferentialDrivePathTracking/")
sys.path.insert(0, "RouteFinding-A-Star-Algorithm-Implementation/")
from main import State
from route_finder import Thing, Position, a_star_search, createRoute
import math

import imutils
import cv2
import numpy as np
from scipy import stats
from imutils.video import VideoStream
from imutils.contours import sort_contours
import time

from potential_field_planning import potential_field_planning
import signal

frameSize = (640, 480)


def main():

    
    brain = Brain()
    signal.signal(signal.SIGINT, brain.signal_handler)
    while not brain.closed:
        brain.run()


class Brain():
    Init = 0
    Start = 1
    Running = 2

    def __init__(self, ip= '192.168.43.88', bsize=1024, totalRobotCount_=4):
        self.state = self.Init
        self.TCP_IP = ip    #ip
        self.TCP_PORT1 = 5000    #port
        self.TCP_PORT2 = 5001    #port
        self.TCP_PORT3 = 5002    #port
        self.TCP_PORT4 = 5003    #port
        self.BUFFER_SIZE = bsize    #Buffer size

        
        self.totalRobotCount= totalRobotCount_
        self.closed = False
        self.conn1, self.conn2, self.conn3, self.conn4 = None, None, None, None

        s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s1.bind((self.TCP_IP, self.TCP_PORT1))
        s1.listen(1)
        self.conn1, self.addr1 = s1.accept()

        """
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s2.bind((self.TCP_IP, self.TCP_PORT2))
        s2.listen(1)

        self.conn2, self.addr2 = s2.accept()

        s3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s3.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s3.bind((self.TCP_IP, self.TCP_PORT3))
        s3.listen(1)
        self.conn3, self.addr3 = s3.accept()

        s4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s4.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s4.bind((self.TCP_IP, self.TCP_PORT4))
        s4.listen(1)
        self.conn4, self.addr4 = s4.accept()
        """
        print ('Connection address1:', self.addr1)
        #print ('Connection address2:', self.addr2)
        #print ('Connection address3:', self.addr3)
        #print ('Connection address4:', self.addr4)
        self.vs = VideoStream(src=0, usePiCamera=True, resolution=frameSize, framerate=80).start()
        time.sleep(2.0)

        pass
    def configure(self):
        upper = (0, 0, 0)
        lower = (255, 255, 255)
        lowerRobot1 = lowerRobot2 = lowerRobot3 = lowerRobot4 = lowerObstacle = lower
        upperRobot1 = upperRobot2 = upperRobot3 = upperRobot4 = upperObstacle = upper
        while True:
            image = self.vs.read()
            blurred2 = cv2.GaussianBlur(image.copy(), (25, 25), 0)
            blurred = cv2.blur(image.copy(),(25,25))
            hsv = cv2.cvtColor(blurred.copy(), cv2.COLOR_BGR2HSV)

            k = cv2.waitKey(5) & 0xFF
            if (k == 97):  #if key 'a' is pressed
                (lowerRobot1, upperRobot1), (lowerRobot2, upperRobot2), \
                    (lowerRobot3, upperRobot3), (lowerRobot4, upperRobot4), \
                    (lowerObstacle, upperObstacle) = configureColorRange(image, hsv)    
                #robotLow, robotHigh, obstacleLow, obstacleHigh= configureColorRange(image, hsv)
                cv2.destroyAllWindows()
                return (lowerRobot1, upperRobot1), (lowerRobot2, upperRobot2), \
                    (lowerRobot3, upperRobot3), (lowerRobot4, upperRobot4), \
                    (lowerObstacle, upperObstacle)
            cv2.imshow('Robot Detector: Press a to configure filters', image)
    
    def findAllRobots(self, iteration, lowerRobot1, upperRobot1, lowerRobot2, upperRobot2, lowerRobot3, upperRobot3, lowerRobot4, upperRobot4, lowerObstacle, upperObstacle):
        listR1x = np.array([])
        listR1y = np.array([])
        listR1angle = np.array([])
        lastResetCounterR1 = 0

        listR2x = np.array([])
        listR2y = np.array([])
        listR2angle = np.array([])
        

        listR3x = np.array([])
        listR3y = np.array([])
        listR3angle = np.array([])
        

        listR4x = np.array([])
        listR4y = np.array([])
        listR4angle = np.array([])

        x1,y1,degree1, x2,y2,degree2, x3,y3,degree3, x4,y4,degree4 = None, None, None, None, None, None, None, None, None, None, None, None
        
        listObsx = np.array([])
        listObsy = np.array([])
        
        while True:

            
            image = self.vs.read()
            blurred2 = cv2.GaussianBlur(image.copy(), (25, 25), 0)
            blurred = cv2.blur(image.copy(),(25,25))
            hsv = cv2.cvtColor(blurred.copy(), cv2.COLOR_BGR2HSV)
        
            orangeImage = hsv.copy()
            robotImage1 = hsv.copy()
            robotImage2 = hsv.copy()
            robotImage3 = hsv.copy()
            robotImage4 = hsv.copy()
        
            

            cntsRobotGreen, filterGreen = filterAndFindContours(lowerRobot1, upperRobot1, robotImage1)
            cntsRobotBlue, filterBlue = filterAndFindContours(lowerRobot2, upperRobot2, robotImage2)
            cntsRobotYellow, filterYellow = filterAndFindContours(lowerRobot3, upperRobot3, robotImage3)
            cntsRobotRed, filterRed = filterAndFindContours(lowerRobot4, upperRobot4, robotImage4)

            cntsObstacle, filterOrange = filterAndFindContours(lowerObstacle, upperObstacle, orangeImage)

            if len(cntsRobotGreen) >= 1:
                
                #Sort the contours by the area and check is it big enough to be a robot
                cntsRobotGreen.sort(key=cv2.contourArea, reverse=True)
                if cv2.contourArea(cntsRobotGreen[0])>50:
                    (x,y),(MA,ma),angle1 = cv2.fitEllipse(cntsRobotGreen[0])
                    x1,y1 = getCenterOfBox(cntsRobotGreen[0])
                    listR1x = np.append(listR1x, x1)                
                    listR1y = np.append(listR1y, frameSize[1]-y1)
                    listR1angle = np.append(listR1angle, angle1)

                    cv2.circle(image, (x1, y1), 5, (0, 0, 255), -1)
                    cv2.putText(image,'x= '+str(x1)+', y= '+str(frameSize[1]-y1)+', a1= '+str(int(angle1)),(x1+10,y1+10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            
            if len(cntsRobotBlue) >= 1:
                #Sort the contours by the area and check is it big enough to be a robot
                cntsRobotBlue.sort(key=cv2.contourArea, reverse=True)
                if cv2.contourArea(cntsRobotBlue[0])>50:
                    (x,y),(MA,ma),angle2 = cv2.fitEllipse(cntsRobotBlue[0])
                    x2,y2 = getCenterOfBox(cntsRobotBlue[0])
                    listR2x = np.append(listR2x, x2)                
                    listR2y = np.append(listR2y, frameSize[1]-y2)
                    listR2angle = np.append(listR2angle, angle2)

                    cv2.circle(image, (x2, y2), 5, (0, 0, 255), -1)
                    cv2.putText(image,'x= '+str(x2)+', y= '+str(frameSize[1]-y2)+', a1= '+str(int(angle2)),(x2+10,y2+10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            if len(cntsRobotRed) >= 1:
                #Sort the contours by the area and check is it big enough to be a robot
                cntsRobotRed.sort(key=cv2.contourArea, reverse=True)
                if cv2.contourArea(cntsRobotRed[0])>50:
                    (x,y),(MA,ma),angle3 = cv2.fitEllipse(cntsRobotRed[0])
                    x3,y3 = getCenterOfBox(cntsRobotRed[0])
                    listR3x = np.append(listR3x, x3)                
                    listR3y = np.append(listR3y, frameSize[1]-y3)
                    listR3angle = np.append(listR3angle, angle3)

                    cv2.circle(image, (x3, y3), 5, (0, 0, 255), -1)
                    cv2.putText(image,'x= '+str(x3)+', y= '+str(frameSize[1]-y3)+', a1= '+str(int(angle3)),(x3+10,y3+10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            if len(cntsRobotYellow) >= 1:
                #Sort the contours by the area and check is it big enough to be a robot
                cntsRobotYellow.sort(key=cv2.contourArea, reverse=True)
                if cv2.contourArea(cntsRobotYellow[0])>50:
                    (x,y),(MA,ma),angle4 = cv2.fitEllipse(cntsRobotYellow[0])
                    x4,y4 = getCenterOfBox(cntsRobotYellow[0])
                    listR4x = np.append(listR3x, x4)                
                    listR4y = np.append(listR3y, frameSize[1]-y4)
                    listR4angle = np.append(listR4angle, angle4)

                    cv2.circle(image, (x4, y4), 5, (0, 0, 255), -1)
                    cv2.putText(image,'x= '+str(x4)+', y= '+str(frameSize[1]-y4)+', a1= '+str(int(angle4)),(x4+10,y4+10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

            if len(cntsObstacle) >= 1:
                
                listObsx = np.array([])
                listObsy = np.array([])
                for i in range(len(cntsObstacle)):
                    if (cv2.contourArea(cntsObstacle[i])>30):
                        xo,yo = getCenterOfBox(cntsObstacle[i])
                        listObsx = np.append(listObsx, xo)
                        listObsy = np.append(listObsy, frameSize[1]-yo)
                        cv2.circle(image, (xo, yo), 5, (0, 0, 255), -1)
                        cv2.putText(image,'x='+str(xo)+', y='+str(frameSize[1]-yo),(xo+10,yo+10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
            
            cv2.imshow('Robot Detector', image)
            cv2.imshow('Robot Detector1', filterGreen)
            cv2.imshow('Robot Detector2', filterBlue)
            if lastResetCounterR1>iteration:
                break

            lastResetCounterR1+=1
        if(len(listR1x)>0):
            x1 = int(np.mean(listR1x))
            y1 = int(np.mean(listR1y))
            degree1 = int(np.mean(listR1angle))
            

        if(len(listR2x)>0):
            x2 = int(np.mean(listR2x))
            y2 = int(np.mean(listR2y))
            degree2 = int(np.mean(listR2angle))

        if(len(listR3x)>0):
            x3 = int(np.mean(listR3x))
            y3 = int(np.mean(listR3y))
            degree3 = int(np.mean(listR3angle))

        if(len(listR4x)>0):
            x4 = int(np.mean(listR4x))
            y4 = int(np.mean(listR4y))
            degree4 = int(np.mean(listR4angle))


        return x1, y1, degree1, x2, y2, degree2, x3, y3, degree3, x4, y4, degree4, listObsx, listObsy

    def run(self):
        if self.state == self.Init:
            # Get the capture and identify the robots and objects.
            # Calculate the routes
            # Send the each routes to responsible robots.
            # Set current robot to zero
            # Set state to running

            (self.lowerRobot1, self.upperRobot1), (self.lowerRobot2, self.upperRobot2), \
                    (self.lowerRobot3, self.upperRobot3), (self.lowerRobot4, self.upperRobot4), \
                    (self.lowerObstacle, self.upperObstacle) = self.configure()
            

            # identify for 20 iterations and calculate the average x, y and angles for the robots
            # after this process, identify these(robot x values are scaler, but obstacles x's is a list):
            #(r1x, r1y)
            #(r2x, r2y)
            #(r3x, r3y)
            #(r4x, r4y)
            #(obsx, obsy)
            listObsx = None
            x1, y1, degree1, x2, y2, degree2, x3, y3, degree3, x4, y4, degree4, listObsx, listObsy = \
                self.findAllRobots(5, self.lowerRobot1, self.upperRobot1, self.lowerRobot2, self.upperRobot2, self.lowerRobot3, self.upperRobot3, \
                    self.lowerRobot4, self.upperRobot4, self.lowerObstacle, self.upperObstacle)
            
            print("First detection:",x1, y1, degree1, x2, y2, degree2, x3, y3, degree3, x4, y4, degree4, listObsx, listObsy)
            

            
            #while x1 == None or x2 == None or x3==None or x4 == None or listObsx == None:
            while x1 == None or x2 == None or len(listObsx)==0:
                print("Error detecting some robots or obstacles, re localizing.")
                x1, y1, degree1, x2, y2, degree2, x3, y3, degree3, x4, y4, degree4, listObsx, listObsy = \
                    self.findAllRobots(5, self.lowerRobot1, self.upperRobot1, self.lowerRobot2, self.upperRobot2, self.lowerRobot3, self.upperRobot3, \
                        self.lowerRobot4, self.upperRobot4, self.lowerObstacle, self.upperObstacle)

            
            print("Detected robots")
            #robot1start = Thing(Position(x1, y1), degree1, 3, "Start")
            #robot2end = Thing(Position(x2, y2), degree2, 3, "End")
            #robot2start = Thing(Position(x2, y2), degree1, 3, "Start")
            #robot3end = Thing(Position(x3, y3), degree1, 3, "End")
            #robot3start = Thing(Position(x3, y3), degree1, 3, "Start")
            #robot4end = Thing(Position(x4, y4), degree1, 3, "End")
            path1, path2, path3, path4 = None, None, None, None
                
            #came_from, cost_so_far, last = a_star_search(obstacles, robot1start, robot2end, 1, 1, 600)
            #path1 = createRoute(came_from, robot1start, last)
            
            # sx1,sy1 start x,y
            # gx1, gy1 goal x,y
            # ox, oy obstacles x,y
            # grid size
            
            
            grid_size = 12.0  # potential grid size [m]
            robot_radius = 5.0  # robot radius [m]
            rx1, ry1 = potential_field_planning(
                x1, y1, x2, y2, listObsx, listObsy, grid_size, robot_radius)
            #came_from, cost_so_far, last = a_star_search(obstacles, robot2start, robot3end, 3, 4, 200)
            #path2 = createRoute(came_from, robot1start, last)
            print("Calculated path planning")

            
            #came_from, cost_so_far, last = a_star_search(obstacles, robot3start, robot4end, 3, 4, 200)
            #path3 = createRoute(came_from, robot1start, last)

            #came_from, cost_so_far, last = a_star_search(obstacles, robot1start, robot2end, 3, 4, 200)
            #path4 = createRoute(came_from, robot1start, last)
            
            path1 = [(rx1[i], ry1[i]) for i in range(len(rx1))]
            path1 = path1[0::2]
            #path2=[(rx2[i], ry2[i]) for i in range(len(rx2))]
            #path3=[(rx3[i], ry3[i]) for i in range(len(rx3))]
            #path4=[(rx4[i], ry4[i]) for i in range(len(rx4))]
            
            print(path1)
            #print(path2)
            #print(path3)
            #print(path4)
            
            if path1:
                #image = drawGrid(box_count, size, things, path[1:-1])  
                start = State(path1[0][0], path1[0][1], math.radians(90))
                targets = [State(i,j, 0) for (i,j) in path1]
                del targets[0]
                self.conn1.send(Message.createRouteMessage(start, targets).__str__().encode())
            
                data = self.conn1.recv(self.BUFFER_SIZE)
                message = Message.create(data.decode())
                # TODO: Identifying the current robot location is not implemented yet
                if message.type == Message.OkMessageType:
                    self.robotIndex = 0
                    self.state = self.Start
            
            if path2:
                #image = drawGrid(box_count, size, things, path[1:-1])  
                start = State(path2[0][0], path2[0][1], math.radians(90))
                targets = [State(i,j, 0) for (i,j) in path2]
                del targets[0]
                self.conn2.send(Message.createRouteMessage(start, targets).__str__().encode())
            
                data = self.conn2.recv(self.BUFFER_SIZE)
                message = Message.create(data.decode())
                # TODO: Identifying the current robot location is not implemented yet
                if message.type == Message.OkMessageType:
                    self.robotIndex = 0
                    self.state = self.Start
            
            if path3:
                #image = drawGrid(box_count, size, things, path[1:-1])  
                start = State(path3[0][0], path3[0][1], math.radians(90))
                targets = [State(i,j, 0) for (i,j) in path3]
                del targets[0]
                self.conn3.send(Message.createRouteMessage(start, targets).__str__().encode())
            
                data = self.conn3.recv(self.BUFFER_SIZE)
                message = Message.create(data.decode())
                # TODO: Identifying the current robot location is not implemented yet
                if message.type == Message.OkMessageType:
                    self.robotIndex = 0
                    self.state = self.Start
            
            if path4:
                #image = drawGrid(box_count, size, things, path[1:-1])  
                start = State(path4[0][0], path4[0][1], math.radians(90))
                targets = [State(i,j, 0) for (i,j) in path4]
                del targets[0]
                self.conn4.send(Message.createRouteMessage(start, targets).__str__().encode())
            
                data = self.conn4.recv(self.BUFFER_SIZE)
                message = Message.create(data.decode())
                # TODO: Identifying the current robot location is not implemented yet
                if message.type == Message.OkMessageType:
                    self.robotIndex = 0
                    self.state = self.Start
                
            # after that, send these information to route calculator.
            #start, targets = routeCalculator(r1x, r1y, r2x, r2y, r3x, r3y, r4x, r4y, obsx, obsy)

            #TODO: these start and target values will be calculated in route calculator.
            #start = State(-20.0, 15.0, math.radians(90))
            #targets = [State(-20.0, 16.0, 0.0)]


        elif self.state == self.Start:
            # If current robot index is over than number of robots:
                # switch state to init TODO: or finish
            # else:
                # send start message to the current robot
                # set state to running

            if self.robotIndex == self.totalRobotCount:
                self.close()
            else:
                #TODO:In sending message, later we need to implement which robot we are sending the message
                if self.robotIndex == 0:
                    self.conn1.send(Message.createStartMessage().__str__().encode())
                elif self.robotIndex == 1:
                    self.conn2.send(Message.createStartMessage().__str__().encode())
                elif self.robotIndex == 2:
                    self.con3.send(Message.createStartMessage().__str__().encode())
                elif self.robotIndex == 3:
                    self.conn4.send(Message.createStartMessage().__str__().encode())
                
                self.state = self.Running
            

        elif self.state == self.Running:
            # Listen the socket until received a message
            # If the message is a GetLocationMessage:
                # Then identify the current robot
                # Send a LocationMessage to the robot including the location of the robot
            # else if the message is EndMessage:
                # set current robot index to next robot index
                # set state to start
            # else do nothing, pass

            if self.robotIndex == 0:
                data = self.conn1.recv(self.BUFFER_SIZE)
            elif self.robotIndex == 1:
                data = self.conn2.recv(self.BUFFER_SIZE)
            elif self.robotIndex == 2:
                data = self.conn3.recv(self.BUFFER_SIZE)
            elif self.robotIndex == 3:
                data = self.conn4.recv(self.BUFFER_SIZE)
            
            message = Message.create(data.decode())
            # TODO: Identifying the current robot location is not implemented yet
            if message.type == Message.GetLocationMessageType:

                # Calculate the robot location for 20 iteration and send the average values
                # self.robotIndex can help to identify robot color
                x1, y1, degree1, x2, y2, degree2, x3, y3, degree3, x4, y4, degree4, listObsx, listObsy = \
                self.findAllRobots(2, self.lowerRobot1, self.upperRobot1, self.lowerRobot2, self.upperRobot2, self.lowerRobot3, self.upperRobot3, \
                    self.lowerRobot4, self.upperRobot4, self.lowerObstacle, self.upperObstacle)

                if self.robotIndex == 0:
                    if not(x1 and y1 and degree1):
                        x1, y1, degree1 = 0, 0, 0

                    self.conn1.send(Message.createLocationMessage(State(x1, y1, math.radians(degree1))).__str__().encode())

                elif self.robotIndex == 1:
                    if not(x2 and y2 and degree2):
                        x2, y2, degree2 = 0, 0, 0
                    self.conn2.send(Message.createLocationMessage(State(x2, y2, math.radians(degree2))).__str__().encode())

                elif self.robotIndex == 2:
                    if not(x3 and y3 and degree3):
                        x3, y3, degree3 = 0, 0, 0
                    self.conn3.send(Message.createLocationMessage(State(x3, y3, math.radians(degree3))).__str__().encode())

                else:
                    if not(x4 and y4 and degree4):
                        x4, y4, degree4 = 0, 0, 0
                    self.conn4.send(Message.createLocationMessage(State(x4, y4, math.radians(degree4))).__str__().encode())

            elif message.type == Message.EndMessageType:
                self.robotIndex = self.robotIndex + 1
                self.state = self.Start

            else:
                pass

        else:
            pass

    def signal_handler(self, sig, frame):
        self.close()
        sys.exit(0)

    def close(self):
        self.closed = True
        if self.conn1:
            self.conn1.close()
        if self.conn2:
            self.conn2.close()
        if self.conn3:
            self.conn3.close()
        if self.conn4:
            self.conn4.close()

def getCenterOfBox(box):
    M = cv2.moments(box)
    return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))  

def triangle(lower, upper, image, originalImage):
    cntsTriangle, filterTriangle = filterAndFindContours(lower, upper, image)
    cntsTriangle.sort(key=cv2.contourArea, reverse=True)
    #print(cntsTriangle[0])

    if len(cntsTriangle) > 0 :
        peri = cv2.arcLength(cntsTriangle[0], True)
        approx = cv2.approxPolyDP(cntsTriangle[0], 0.04 * peri, True)
        if len(approx) == 3:
            x1, y1, x2, y2, x3, y3 = approx[0,0,0], approx[0,0,1], \
                approx[1,0,0],approx[1,0,1],approx[2,0,0], approx[2,0,1]
            # filter the image for the triangle, after that use contours for getting the A, B and C point for triangle. 
            # calculate the distances between AB, AC and BC. (A is (x1,y1), B is (x2,y2), C is (x3,y3))
            
            distAB = math.sqrt((x1-x2)**2+(y1-y2)**2)
            distAC = math.sqrt((x1-x3)**2+(y1-y3)**2)
            distBC = math.sqrt((x2-x3)**2+(y2-y3)**2)

            # find which one is the smallest, using if else blocks
            # in the if else block, make sure (x1,y1) is more left side point, (x2, y2) is the second and (x3, y3) the other point
            if (distAB < distAC and distAB < distBC):
                if x1<x2:
                    nx1, ny1, nx2, ny2, nx3, ny3 = x1, y1, x2, y2, x3, y3
                else:
                    nx1, ny1, nx2, ny2, nx3, ny3 = x2, y2, x1, y1, x3, y3

            elif (distAC < distAB and distAC < distBC):
                if x1<x3:
                    nx1, ny1, nx2, ny2, nx3, ny3 = x1, y1, x3, y3, x2, y2
                else:
                    nx1, ny1, nx2, ny2, nx3, ny3 = x3, y3, x1, y1, x2, y2

            else:
                if x2<x3:
                    nx1, ny1, nx2, ny2, nx3, ny3 = x2, y2, x3, y3, x1, y1
                else:
                    nx1, ny1, nx2, ny2, nx3, ny3 = x3, y3, x2, y2, x1, y1

            # after that use this formula to calculate the angle:
            # degree = math.degrees(math.radians(90) - math.atan2(y2-y1, x2-x1))
            degree = math.degrees(math.radians(90) + math.atan2(ny2-ny1, nx2-nx1))
            
            #print(nx1, ny1, nx2, ny2, nx3, ny3)
            # calculate the middle point, to calculate use this formula:
            # tmpx, tmpy = ((x1+x2)/2) + ((y1+y2)/2) 
            # cx, cy = tmpx + (x3 - tmpx)/3, tmpx + (x3 - tmpx)/3
            # return cx, cy, degree
            tmpx, tmpy = ((nx1+nx2)/2), ((ny1+ny2)/2) 
            cx, cy = tmpx + (nx3 - tmpx)/3, tmpy + (ny3 - tmpy)/3

            if cy > tmpy:
                degree =  degree + 180

            #cv2.circle(originalImage, (cx, cy), 5, (0, 0, 255), -1)
            #cv2.circle(originalImage, (nx1, ny1), 5, (0, 0, 255), -1)
            #cv2.circle(originalImage, (nx2, ny2), 5, (0, 0, 255), -1)
            #cv2.putText(originalImage,'angle= '+str(int(degree)),(cx+10,cy+10), 
            #            cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 1)
            
            #cv2.drawContours(originalImage, [cntsTriangle[0]], -1, (0, 255, 0), 2)
            return cx, cy, degree, filterTriangle
        else:
            return None, None, None, filterTriangle
    else :
        return None, None, None, filterTriangle

def filterAndFindContours(lower, upper, image, doMorph=True, doErode=True, doDilate=False):
    mask = cv2.inRange(image, lower, upper)   

    kernel = np.ones((5,5),np.uint8)
    if doErode:
        mask = cv2.erode(mask, kernel, iterations=3)
    if doDilate:
        mask = cv2.dilate(mask, kernel, iterations=2)
    if doMorph:
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    #cnts = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_NONE)
        
    cnts = imutils.grab_contours(cnts)
    return cnts, mask

def configureColorRange(image, hsvImage):
    r1 = cv2.selectROI("Select robot1 color", image)
    robotImg1 = hsvImage[int(r1[1]):int(r1[1]+r1[3]), int(r1[0]):int(r1[0]+r1[2])]
    r2 = cv2.selectROI("Select robot2 color", image)
    robotImg2 = hsvImage[int(r2[1]):int(r2[1]+r2[3]), int(r2[0]):int(r2[0]+r2[2])]
    r3 = cv2.selectROI("Select robot3 color", image)
    robotImg3 = hsvImage[int(r3[1]):int(r3[1]+r3[3]), int(r3[0]):int(r3[0]+r3[2])]
    r4 = cv2.selectROI("Select robot4 color", image)
    robotImg4 = hsvImage[int(r4[1]):int(r4[1]+r4[3]), int(r4[0]):int(r4[0]+r4[2])]
    r5 = cv2.selectROI("Select obstacle color", image)
    obstacleImg = hsvImage[int(r5[1]):int(r5[1]+r5[3]), int(r5[0]):int(r5[0]+r5[2])]

    robot1Low, robot1High, robot1AvgL, robot1AvgH= findRanges(robotImg1)
    robot2Low, robot2High, robot2AvgL, robot2AvgH= findRanges(robotImg2)
    robot3Low, robot3High, robot3AvgL, robot3AvgH= findRanges(robotImg3)
    robot4Low, robot4High, robot4AvgL, robot4AvgH= findRanges(robotImg4)
    obstacleLow, obstacleHigh, obstacleAvgL, obstacleAvgH = findRanges(obstacleImg)
    
    robot1Low=(int(robot1Low[0]), int(robot1Low[1]), int(robot1Low[2]))
    robot1High=(int(robot1High[0]), int(robot1High[1]), int(robot1High[2]))

    robot2Low=(int(robot2Low[0]), int(robot2Low[1]), int(robot2Low[2]))
    robot2High=(int(robot2High[0]), int(robot2High[1]), int(robot2High[2]))

    robot3Low=(int(robot3Low[0]), int(robot3Low[1]), int(robot3Low[2]))
    robot3High=(int(robot3High[0]), int(robot3High[1]), int(robot3High[2]))

    robot4Low=(int(robot4Low[0]), int(robot4Low[1]), int(robot4Low[2]))
    robot4High=(int(robot4High[0]), int(robot4High[1]), int(robot4High[2]))

    obstacleLow=(int(obstacleLow[0]), int(obstacleLow[1]), int(obstacleLow[2]))
    obstacleHigh=(int(obstacleHigh[0]), int(obstacleHigh[1]), int(obstacleHigh[2]))
    
    print((robot1Low, robot1High), (robot2Low, robot2High), (robot3Low, robot3High), (robot4Low, robot4High), (obstacleLow, obstacleHigh))
    #return robotLow, robotHigh, obstacleLow, obstacleHigh
    return (robot1Low, robot1High), (robot2Low, robot2High), (robot3Low, robot3High), (robot4Low, robot4High), (obstacleLow, obstacleHigh)
    #return robotAvgL, robotAvgH, obstacleAvgL, obstacleAvgH
    
def findRanges(image):
    lowH=255
    lowS=255
    lowV=255
    highH=0
    highS=0
    highV=0

    #Tmp variables for calculating the average values, used for testing purposes only, not these using anymore
    tmpH=0
    tmpS=0
    tmpV=0
    count=0
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            count+=1
            if(image[i][j][0]<lowH):
                lowH=image[i][j][0]
            if(image[i][j][1]<lowS):
                lowS=image[i][j][1]
            if(image[i][j][2]<lowV):
                lowV=image[i][j][2]

            if(image[i][j][0]>highH):
                highH=image[i][j][0]
            if(image[i][j][1]>highS):
                highS=image[i][j][1]
            if(image[i][j][2]>highV):
                highV=image[i][j][2]
            tmpH+=image[i][j][0]
            tmpS+=image[i][j][1]
            tmpV+=image[i][j][2]
    if(count!=0):
        tmpH=tmpH/(count)
        tmpS=tmpS/(count)
        tmpV=tmpV/(count)

    return (max(0, lowH-12), max(0, lowS-30), max(0, lowV-30)), \
        (min(255, highH+12), min(255, highS+30), min(255, highV+30)), \
        (max(0, tmpH-20), max(100, tmpS-50), max(50, tmpV-60)), \
        (min(255, tmpH+20), min(255, tmpS+50), min(255, tmpV+60))


def fixAngle(angle):
        return math.atan2(math.sin(angle), math.cos(angle))


if __name__ == "__main__":
    main()