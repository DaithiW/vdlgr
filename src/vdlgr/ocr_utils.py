import site

site.USER_SITE = ""

from paddleocr import PaddleOCR, draw_ocr
from paddleocr.tools.infer import utility
import numpy as np
import cv2
import io
import base64
from PIL import Image

def initialize_ocr():
    '''
    Just initialize the OCR object once, outside the loop
    '''
    return PaddleOCR(use_angle_cls=True, lang="en", show_log=False)

# take frame from opencv frame generator and yield ocr results
def ocr_generator(subframe_generator):
    '''
    Needs to take a subframe generator as input, and yield results (plural)
    '''
    ocr = initialize_ocr()  # Initialize OCR once, outside the loop
    results = []
    while True:
        try:
            frames, meta = next(subframe_generator)
            for frame in frames:
                result =  ocr.ocr(frame, cls=False)
                # results[i] = result
                # result = ocr.ocr(frame, cls=True)
                results.append(result)
            yield results, frames[0], meta
            results = []
        except StopIteration:
            # Break the loop if there are no more frames
            break

def visualize_ocr_result(image, result, font_path=None):
   
    # Unpack paddleocr results
    boxes = [detection[0] for line in result for detection in line]
    # below lines for paddleocr built-in draw func.
    #txts = [detection[1][0] for line in result for detection in line]
    #scores = [detection[1][1] for line in result for detection in line]


    for i, box in enumerate(boxes):
        cv2.polylines(image, [np.array(box).astype(np.int32).reshape((-1,1,2))], True, color=(0,255,0), thickness=2)
        cv2.putText(image, str(i+1), (int(box[0][0]), int(box[0][1])), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0),2)

    return image, boxes



    # below snippet uses built in func in paddleocr to draw boxes on image, but it make the image too wide

    # uncomment below to disable drawing the text area
    #txts = None

    # Draw the bounding boxes and text
    #if font_path:
    #    im_show = draw_ocr(image, boxes, txts, scores, font_path=font_path)
    #else:
    #    im_show = draw_ocr(image, boxes, txts, scores)

    #return im_show, boxes

def convert_img_b64(img_array):
    """base64 image needed by flet"""
    # Convert img array to RGB
    img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)    
    # Convert numpy array to PIL Image
    image = Image.fromarray(img_array.astype('uint8'), 'RGB')
    # Create a bytes buffer
    buffered = io.BytesIO()
    # Save image to the buffer in PNG format
    image.save(buffered, format="PNG")
    # Get the byte data
    img_bytes = buffered.getvalue()
    # Encode as base64
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return img_base64
