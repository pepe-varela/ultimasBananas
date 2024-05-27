import grpc
from concurrent import futures
import logging
from time import sleep

# import the generated classes
import image_msg_pb2
import image_msg_pb2_grpc

import cv2
import numpy as np
import zlib
from threading import Thread


img = None

# Define the dimensions of the image
width = 400
height = 400

# Create a black image
crossImage = np.zeros((height, width, 3), dtype=np.uint8)

# Define the color for the cross (in BGR format)
color = (0, 0, 255)  # Red color

# Define the thickness of the cross
thickness = 5

# Draw the horizontal line (cross) on the image
cv2.line(crossImage, (0, height // 2), (width, height // 2), color, thickness)

# Draw the vertical line (cross) on the image
cv2.line(crossImage, (width // 2, 0), (width // 2, height), color, thickness)

from flask import Flask, render_template, Response

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def generate_frames():
    if img is not None:
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
    else:
        ret, buffer = cv2.imencode('.jpg', crossImage)
        frame = buffer.tobytes()
    yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/vel_1')
def vel_1():
    # return a json response with vel_1
    return {"vel_1": 1}

@app.route('/vel_2')
def vel_2():
    # return a json response with vel_2
    return {"vel_2": 2}
    


# based on .proto service
class CloudPointsServicer(image_msg_pb2_grpc.PointsProcessor):
    def getLocation(self, request, context):
        print("Received a request")
        # convert the image to a numpy array
        data = zlib.decompress(request.points.data)
        width = request.points.width
        height = request.points.height
        global img
        img = np.frombuffer(data, dtype=np.uint8).reshape(height, width, 1)
        # print(img)
        response = image_msg_pb2.Pose2D()
        return response


def serve():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_msg_pb2_grpc.add_PointsProcessorServicer_to_server(
        CloudPointsServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()



if __name__ == "__main__":
    logging.basicConfig()
    Thread(target=serve).start()
    task = Thread(target=app.run)
    task.start()
    task.join()