import cv2
from contextlib import contextmanager
import os
import numpy as np

@contextmanager
def open_video(video_path):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise IOError(f"Error opening video file: {video_path}")
    
    try:
        yield cap
    finally:
        cap.release()

def get_video_info(video_path):
    with open_video(video_path) as cap:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
    return fps, frame_count, duration

def frame_generator(video_path, interval):
    with open_video(video_path) as cap:
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        current_frame = 0
        current_time = 0
        
        while current_frame < frame_count:
            # Set the position of the next frame to be captured
            old_frame = current_frame
            current_frame = round(current_frame)
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)


            ret, frame = cap.read() # frame is a numpy array format BGR
            if not ret:
                break # something more here? Like error handling?
            
            yield [frame], (current_frame, current_time)  # tuple containing 1 item list and tuple
            
            # Move to the next frame of interest
            current_time = current_time + interval
            current_frame = old_frame + (interval * fps)

def calculate_frame_interval(fps, time_interval):
    return int(fps * time_interval)

def show_frame(frame):
    '''
    Displays the frame in a window.
    '''
    cv2.imshow("Frame", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def subframe_generator(frame_generator, bboxes, padding=10):
    '''
    Yields the subframes of the given frame generator that are within the given bounding box.
    '''
    try:
        while True:
            subframes = []
            # next 3 lines should be before start of for loop?
            frame, meta = next(frame_generator)
            frame = frame[0]  # this is a bit dirty
            height, width = frame.shape[:2]  # expecting frame.shape to be (height, width, channels)
            for bbox in bboxes:
                                
                x_min = max(0, int(min(point[0] for point in bbox)) - padding)
                y_min = max(0, int(min(point[1] for point in bbox)) - padding)
                x_max = min(width, int(max(point[0] for point in bbox)) + padding)
                y_max = min(height, int(max(point[1] for point in bbox)) + padding)
                
                if x_max > x_min and y_max > y_min:
                    subframe = frame[y_min:y_max, x_min:x_max]
                    print(f"Subframe shape: {subframe.shape}, from coordinates: [{x_min}:{x_max}, {y_min}:{y_max}]")
                    subframes.append(subframe)
                else:
                    print(f"Warning: Invalid subframe dimensions: [{x_min}:{x_max}, {y_min}:{y_max}]")
                    yield None
            yield subframes, meta  # tuple containing list & tuple
            subframes = []
    except StopIteration:
        pass
