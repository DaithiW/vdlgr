# vdlgr - Video DataLoGgeR

## Description

vdlgr uses optical character recognigition (OCR) and optical character detection (OCD) to enable data-logging from video files.

Data-loggers are devices used in various engineering, scientific, commercial / industrial contexts. These devices can be expensive, and may not facilitate all the desired input types, for example if you wished to data-log mass/weight, temperature and voltage, such a device may not exist. However, plausibly you could have a digital thermometer, a digital scales, and a mulitmeter.

By setting up your at-hand devices (with their own digital displays) in a stationary video shot for the duration of an experiment - this video can then be used with vdlgr to extract the data from the displays.

It is ideal of anyone looking to capture data from devices they already own, or low-cost alternatives to common data-loggers, engineers, scientists, in education.

## Demo

To follow.

## Installation

At this time a Windows installer (msi) is provided. No signing is provided, so users will need to dismiss security warnings to install.

## What it does

vdlgr assume that the user has recorded a video where a data source is at a fixed location in the frame, and that it is visible from the first frame of the video.
The first frame is extracted from the video file (using OpenCV), and then passed to PaddleOCR to run detection and recognition on the frame.
An image is created of the first frame with numbered boxes corresponding to where text has been detected.
The user selects which boxes should be logged, the time interval for logging, and the output file (csv format).
vdlgr will through the entire video file at the time interval, extract the frames, pass them to PaddleOCR and write the results to the output file.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Email: daitiw@proton.me

