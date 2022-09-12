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
import numpy as np

#--- KPI parameters ----------------------------------------------------------------

ego_width = 1.92
target_width = 1.73
target_length = 4.00
lateral_safety_margin = 0.9 * ego_width
lateral_collision_offset = 3.0
bearing_tolerance = 0.00025

high_warn_dist = {
        "straight":    44.0,
        "curve_left":  22.0,
        "curve_right": 33.0,
        "cross1":      22.0,
        "cross2":      22.0,
        "cross3":      22.0,
        "cross4":      22.0,
        "turn":        11.0,
        }

no_warn_dist = {
        "straight":    44.0 + 44.0,
        "curve_left":  22.0 + 44.0,
        "curve_right": 33.0 + 33.0,
        "cross1":      22.0 + 22.0,
        "cross2":      22.0 + 22.0,
        "cross3":      22.0 + 22.0,
        "cross4":      22.0 + 22.0,
        "turn":        11.0 + 22.0,
        }

#--- KPI calculation -----------------------------------------------------------

def warning_level(scenario, dist, val, thresh):
    hwdist = high_warn_dist[scenario]
    nwdist = no_warn_dist[scenario]
    def ipol(alpha):
        return hwdist + alpha * (nwdist - hwdist)
    ret = np.zeros(len(dist))
    ret[(val <= thresh) & (dist <  0.50 * hwdist)] = 7
    ret[(val <= thresh) & (dist >= 0.50 * hwdist)] = 6
    ret[(val <= thresh) & (dist >= 0.75 * hwdist)] = 5
    ret[(val <= thresh) & (dist >= 1.00 * hwdist)] = 4
    ret[(val <= thresh) & (dist >= ipol(0.25))] = 3
    ret[(val <= thresh) & (dist >= ipol(0.50))] = 2
    ret[(val <= thresh) & (dist >= ipol(0.75))] = 1
    ret[dist >= nwdist] = 0
    return ret

def projected_width(yaw, width, length):
    return np.cos(yaw) * width + np.sin(yaw) * length

def diff(a, stride_length):
    ret = a[stride_length:] - a[:-stride_length]
    ret = np.pad(ret, (stride_length, 0), mode="edge")
    return ret

def collwarn(scenario, sequence):
    target_pose_file = os.path.join(scenario, "%02d" % sequence, "targetpose.csv")
    target_pose      = np.genfromtxt(target_pose_file, delimiter=",", skip_header=1)
    distance         = np.sqrt(np.square(target_pose[:,1]) + np.square(target_pose[:,2]))
    lateral_offset   = np.abs(target_pose[:,1])
    bearing          = np.arcsin(target_pose[:,1] / distance)
    object_width     = projected_width(target_pose[:,4], target_width, target_length)
    stride_length    = 5
    delta_bearing    = np.abs(diff(bearing, stride_length))
    margin           = 0.0
    if scenario == "curve_right":
        margin = lateral_safety_margin
    thresh_bearing = diff(np.arctan2(object_width + margin, distance), stride_length)
    if scenario == "turn":
        thresh = np.ones(len(distance)) * lateral_collision_offset
        ret = warning_level(scenario, distance, lateral_offset, thresh)
    else:
        thresh = thresh_bearing + bearing_tolerance
        ret = warning_level(scenario, distance, delta_bearing, thresh)
    return ret

if __name__ == __main__:
	# Examples for calcualting the collision warnings in a scenario
	# Scenario "straight", sequence 1 is a reference scenario with no collision
	collwarn("straight", 1)
	# Scenario "straight", seuqnces 8 and 21 generate collision warnings (like most other sequences)
	collwarn("straight", 8)
	collwarn("straight", 21)
