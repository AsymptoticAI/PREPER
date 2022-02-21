#!/usr/bin/env python3

# Copyright 2022 Jörg Bakker, jorg.bakker@asymptotic.ai
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import math
import cv2
import numpy as np

#--- Extrinsics ----------------------------------------------------------------

def tvec(cam="front"):
    tx = +0.20
    ty = +1.80
    tz = -1.50
    if cam == "right":
        tx = -0.20
        tz = -1.75
    return np.array([tx, ty, tz])

def rvec(cam="front"):
    pitch = +4.66
    yaw   = -0.73
    roll  = +0.00
    if cam == "right":
        pitch = +5.90
        yaw   = -43.00
    return np.array([pitch, yaw, roll]) / 180.0 * math.pi

#--- Intrinsics ----------------------------------------------------------------

fxy = 1716
pcx = 1072
pcy =  699

def intrinsic():
    return np.array([
        [ fxy, 0.0, pcx],
        [ 0.0, fxy, pcy],
        [ 0.0, 0.0, 1.0]
        ])

distortion = np.zeros([5])

#--- Target shape --------------------------------------------------------------

target_width = 1.73
target_length = 4.00
target_height = 1.50
target_hoff = -0.40

#--- Projection and drawing functions ------------------------------------------

def bbox(width, height, length):
    rect = np.array([
            [+0.5 * width, 0, -0.5 * length],
            [-0.5 * width, 0, -0.5 * length],
            [-0.5 * width, 0, +0.5 * length],
            [+0.5 * width, 0, +0.5 * length],
            ])
    bbox = np.concatenate([rect, rect])
    bbox[4:,1] -= height
    return bbox


def get_transformation(target_pose):
    translation = np.array([
        target_pose[1], -(target_pose[3] + target_hoff), target_pose[2]])
    rotx, jac = cv2.Rodrigues(np.array([target_pose[5], 0.0, 0.0]))
    roty, jac = cv2.Rodrigues(np.array([0.0, target_pose[4], 0.0]))
    rotz, jac = cv2.Rodrigues(np.array([0.0, 0.0, target_pose[6]]))
    rotation = np.matmul(np.matmul(rotx, rotz), roty)
    return rotation, translation


def project_points(cam, scenario, rotation, translation, points):
    image_points, jacobi = cv2.projectPoints(
            points, rvec(cam), tvec(cam), intrinsic(), distortion)
    uv = image_points.astype(int)[:,0,:]
    return uv


def draw_bbox(img, projected_points):
    white  = (0xff, 0xff, 0xff)
    cv2.polylines(img, [projected_points[4:]], True, white, 2)
    for i in range(4):
        cv2.line(img, tuple(projected_points[i]), tuple(projected_points[i+4]), white, 2)
    cv2.polylines(img, [projected_points[0:4]], True, white, 2)
    return img


def project(scenario, sequence, frame, cam="front", out_dir="/tmp"):
    target_pose_file = os.path.join(scenario, "%02d" % sequence, "targetpose.csv")
    target_pose = np.genfromtxt(target_pose_file, delimiter=",", skip_header=1)
    tpose = target_pose[frame, :]
    timestamp = tpose[0]
    rotation, translation = get_transformation(tpose)
    points = bbox(target_width, target_height, target_length)
    points = np.matmul(rotation, np.array(points).T).T + translation
    projected_points = project_points(cam, scenario, rotation, translation, points)
    img_name = "%010d.%s" % (timestamp, "png")
    if cam == "right":
        img_name = "%010d_right.%s" % (timestamp, "png")
    img = cv2.imread(os.path.join(os.path.join(scenario, "%02d" % sequence), img_name))
    img = draw_bbox(img, projected_points)
    cv2.imwrite(os.path.join(out_dir, img_name), img)


if __name__ == "__main__":
    project("straight", 1, 120)
    project("cross1", 1, 170, cam="right")
