from CEEC_Library import GetStatus,GetRaw,GetSeg,AVControl,CloseSocket
import cv2
import numpy as np
import time
import os
import torch

from ultralytics import YOLO

from tools.custom import LandDetect
from tools.controller1 import Controller
from utils.config import ModelConfig, ControlConfig
from utils.socket import create_socket
from tools.ChienSegmentation import myGetSegment, filter_masks_by_confidence

if __name__ == "__main__":
    # Create socket
    # Config model
    config_model = ModelConfig()
    device = torch.device('cuda')
    # device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    half = device.type != 'cpu'

    # Config control
    config_control = ControlConfig()

    # Controller
    controller = Controller()

    # Load YOLOv8
    yolo = YOLO(config_model.weights_yolo)

    # Load PIDNet
    image_save_folder = "training_images"
    if not os.path.exists(image_save_folder):
        os.makedirs(image_save_folder)
    image_counter = 0

    #land_detector = LandDetect('pidnet-s', os.path.join(config_model.weights_lane))
    try:
        cnt_fps = 0
        t_pre = 0

        # Mask segmented image
        mask_lr = False
        mask_l = False
        mask_r = False
        mask_t = False

        # Counter for speed up after turning
        reset_counter = 0

        while True:
            s = GetStatus()
            """
            Input:
                image: the image returned from the car
                current_speed: the current speed of the car
                current_angle: the current steering angle of the car
            You must use these input values to calculate and assign the steering angle and speed of the car to 2 variables:
            Control variables: sendBack_angle, sendBack_Speed
                where:
                sendBack_angle (steering angle)
                sendBack_Speed (speed control)
            """
            
            # try:
            
            


            try:
                # Decode image in byte type recieved from server
                # image = GetRaw()
                # image = cv2.resize(image, (640, 384))
                # ============================================================ PIDNet
                # image_filename = os.path.join(image_save_folder, f"image_{image_counter:04d}.jpg")
                # cv2.imwrite(image_filename, image)
                # print(f"Saved image: {image_filename}")
                # image_counter += 1
                
                # segmented_image = land_detector.reference(
                #     image, config_model.segmented_output_size, mask_lr, mask_l, mask_r, mask_t)
                # #segmented_image = GetSeg()
                #segmented_image = cv2.cvtColor(segmented_image, cv2.COLOR_BGR2RGB)
                # ============================================================ YOLO
                # Resize the image to the desired dimensions
                

                # with torch.no_grad():
                #     yolo_output = yolo(image)[0]

                # ============================================================ Controller
                # angle, speed, next_step, mask_l, mask_r = controller.control(segmented_image=segmented_image,
                #                                                             yolo_output=yolo_output)

                # Control when turining
                # if next_step:
                #     print("Next step")
                #     print("Angle:", angle)
                #     print("Speed:", speed)
                #     config_control.update(-angle, speed)

                #     reset_counter = 1

                # # Default control
                # else:
                # img = GetRaw()
                # # with torch.no_grad():
                # #      yolo_output = yolo(img)[0]
                # segmented_image = yolo(img)[0]
                # for i, mask in enumerate(segmented_image['masks']):
                #     mask_np = mask.cpu().numpy() * 255
                #     mask_image = np.uint8(mask_np)
                #     img = cv2.bitwise_and(img, img, mask=mask_image)
                segmented_image = GetSeg()
                segmented_image = cv2.cvtColor(GetSeg(), cv2.COLOR_BGR2GRAY)
                segmented_image = (segmented_image*(255/np.max(segmented_image))).astype(np.uint8)
                if True:
                    error = controller.calc_error(segmented_image)
                    angle = controller.PID(error, p=0.2, i=0.0, d=0.02)
                    # Speed up after turning (in 35 frames)
                    if reset_counter >= 1 and reset_counter < 35:
                        speed = 50
                        reset_counter += 1
                    elif reset_counter == 35:
                        reset_counter = 0
                        speed = 50 
                    else:
                        speed = controller.calc_speed(angle)

                        if float(config_control.current_speed) > 44.5:
                            speed = 15

                    print("Error:", error)
                    print("Angle:", angle)
                    print("Speed:", speed)

                    config_control.update(-angle, speed)
                
                AVControl(speed = speed, angle = -angle)
                # # ============================================================ Show image
                # Resize image if it's too small for you to see
                #segmented_image = cv2.resize(segmented_image, (336, 200), interpolation=cv2.INTER_NEAREST)

                
                #yolo_output = yolo_output.plot()
                #segmented_image = segmented_image.plot()
                # if config_model.view_seg:
                #     cv2.imshow("segmented image", segmented_image)
                cv2.imshow("segmented image", segmented_image)
                # if config_model.view_first_view:
                #     cv2.imshow("first view image", yolo_output)
                
                key = cv2.waitKey(1)
                if key == ord('q'):
                    break
                # ============================================================ Calculate FPS
                if cnt_fps >= 90:
                    t_cur = time.time()
                    fps = (cnt_fps + 1)/(t_cur - t_pre)
                    t_pre = t_cur
                    print('FPS: {:.2f}\r\n'.format(fps))
                    cnt_fps = 0

                cnt_fps += 1

            except Exception as er:
                pass

    finally:
        print('closing socket')
        CloseSocket()