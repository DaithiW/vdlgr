import asyncio
import io
import os

import cv2
import toga
from PIL import Image
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from vdlgr.ocr_utils import ocr_generator, visualize_ocr_result
from vdlgr.video_utils import (calculate_frame_interval, frame_generator,
                                   get_video_info, subframe_generator)


class VideoOCRApp(toga.App):
    def startup(self):
        self.main_window = toga.MainWindow(title="vdlgr")

        # Initialize variables
        self.video_path = None
        self.interval = None
        self.fps = None
        self.frame_count = None
        self.duration = None
        self.selected_boxes = []
        self.output_file = None
        self.ff_gen = None
        self.boxes = None
        self.boxes_vars = []

        # Initialize UI
        self.init_ui()
        self.main_window.show()

    def init_ui(self):
        # Video file selection
        self.select_video_button = toga.Button(
            "Select Video File", on_press=self.select_video_file, style=Pack(padding=5)
        )
        self.video_file_label = toga.Label(
            "No video file selected", style=Pack(padding=5)
        )
        video_file_box = toga.Box(
            children=[self.select_video_button, self.video_file_label],
            style=Pack(direction=ROW),
        )

        # Interval input
        self.interval_label = toga.Label("Interval (s):", style=Pack(padding=5))
        self.interval_slider = toga.Slider(
            range=(0.5, 10),
            value=5,
            tick_count=20,
            on_change=self.slider_callback,
            style=Pack(width=300),
        )
        # self.interval_slider.style.flex = 1
        self.interval_value = toga.Label(
            f"{self.interval_slider.value}s", style=Pack(padding=5)
        )
        interval_box = toga.Box(
            children=[self.interval_label, self.interval_slider, self.interval_value],
            style=Pack(direction=ROW),
        )

        # Output file selection
        self.select_output_button = toga.Button(
            "Select Output File",
            on_press=self.select_output_file,
            style=Pack(padding=5),
        )
        self.output_file_label = toga.Label(
            "No output file selected", style=Pack(padding=5)
        )
        output_file_box = toga.Box(
            children=[self.select_output_button, self.output_file_label],
            style=Pack(direction=ROW),
        )

        # Process video button
        self.process_button = toga.Button(
            "Analyse First Frame", on_press=self.process_video, style=Pack(padding=5)
        )
        process_button_box = toga.Box(
            children=[self.process_button], style=Pack(direction=ROW)
        )

        # Video info display
        self.video_info_label = toga.Label("Video Info: N/A", style=Pack(padding=5))
        video_info_box = toga.Box(
            children=[self.video_info_label], style=Pack(direction=ROW)
        )

        # Image display
        self.image_view = toga.ImageView(style=Pack(padding=5, height=600))
        image_box = toga.Box(children=[self.image_view], style=Pack(direction=ROW))

        # Label for checkboxes
        self.checkbox_label = toga.Label("Select Text Regions:", style=Pack(padding=5))
        checkbox_label_box = toga.Box(
            children=[self.checkbox_label], style=Pack(direction=ROW)
        )

        # Frame for checkboxes
        self.checkboxes_box = toga.Box(style=Pack(direction=COLUMN, padding=5))

        # Start OCR button
        self.start_ocr_button = toga.Button(
            "Start OCR Processing",
            on_press=self.start_ocr_processing,
            enabled=False,
            style=Pack(padding=5),
        )
        self.progress = toga.Label(
            "",
            style=Pack(
                padding=5,
            ),
        )
        start_ocr_button_box = toga.Box(
            children=[self.start_ocr_button, self.progress], style=Pack(direction=ROW)
        )

        # Main box
        self.main_box = toga.Box(
            children=[
                video_file_box,
                interval_box,
                output_file_box,
                process_button_box,
                video_info_box,
                image_box,
                checkbox_label_box,
                self.checkboxes_box,
                start_ocr_button_box,
            ],
            style=Pack(direction=COLUMN, padding=10),
        )
        self.main_window.content = self.main_box

    async def select_video_file(self, widget):
        try:
            video_file = await self.main_window.open_file_dialog(
                title="Select Video File",
                file_types=["mp4", "avi", "mov", "mkv"],
                multiple_select=False,
            )
            if video_file is not None:
                self.video_path = video_file
                self.video_file_label.text = str(self.video_path)

                self.checkboxes_box.clear() # don't want boxes referring to a previous video
                self.image_view.image = None
                print(f"Video path set to: {self.video_path}")  # Debug print
            else:
                self.video_file_label.text = "No video file selected"
                print("No file selected")  # Debug print
        except ValueError:
            print("Open file dialog was canceled")
            self.video_file_label.text = "File selection canceled"

    async def select_output_file(self, widget):
        try:
            output_file = await self.main_window.save_file_dialog(
                title="Select Output File",
                suggested_filename="output.txt",
                file_types=["csv"],
            )
            if output_file is not None:
                self.output_file = output_file
                self.output_file_label.text = str(self.output_file)
                print(f"Output file set to: {self.output_file}")  # Debug print
            else:
                self.output_file_label.text = "No output file selected"
                print("No output file selected")  # Debug print
        except ValueError:
            print("Save file dialog was canceled")
            self.output_file_label.text = "File selection canceled"

    def slider_callback(self, widget):
        self.interval_value.text = f"{self.interval_slider.value} s"

    def process_video(self, widget):
        if not self.video_path:
            self.main_window.error_dialog("Error", "Please select a video file.")
            return

        try:
            self.interval = float(self.interval_slider.value)
        except ValueError:
            self.main_window.error_dialog("Error", "Please enter a valid interval.")
            return

        if not self.output_file:
            self.main_window.error_dialog("Error", "Please specify an output file.")
            return

        # Get video info
        self.fps, self.frame_count, self.duration = get_video_info(self.video_path)
        info_str = f"FPS: {self.fps:.2f}, Frames: {self.frame_count}, Duration: {self.duration:.2f}s"
        self.video_info_label.text = info_str

        # Process first frame
        self.process_first_frame()

    def process_first_frame(self):
        interval_frames = calculate_frame_interval(self.fps, self.interval)
        self.ff_gen = ocr_generator(frame_generator(self.video_path, interval_frames))

        try:
            result, frame, _ = next(self.ff_gen)
        except StopIteration:
            self.main_window.error_dialog("Error", "No frames found in video.")
            return

            # Construct the absolute path to the font file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(script_dir, "resources", "PressStart2P-Regular.ttf")

        # Visualize OCR result
        visimg, self.boxes = visualize_ocr_result(frame, result[0], font_path)

        # Show image
        self.show_image(visimg)

        # Display checkboxes
        self.display_boxes(self.boxes)

    def show_image(self, image):
        # Convert image to PIL Image
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(image)

        # Save the image to an in-memory bytes buffer
        buffer = io.BytesIO()
        im.save(buffer, format="PNG")
        buffer.seek(0)

        image_data = buffer.getvalue()

        # Create a Toga Image
        toga_image = toga.Image(data=image_data)

        # Set the image on the ImageView
        self.image_view.image = toga_image

    def display_boxes(self, boxes):
        # Clear previous checkboxes
        #self.checkboxes_box.children.clear()

        self.checkboxes_box.clear()
        self.boxes_vars = []

        for idx, box in enumerate(boxes):
            var = toga.Switch(f"Box {idx+1}", style=Pack(padding=2))
            self.boxes_vars.append((var, box))
            self.checkboxes_box.add(var)

        self.start_ocr_button.enabled = True

    async def start_ocr_processing(self, widget):
        self.progress.text = "OCR in progress, please wait!"
        await asyncio.sleep(0)  # allow gui to update

        self.selected_boxes = [box for var, box in self.boxes_vars if var.value]
        if not self.selected_boxes:
            self.main_window.error_dialog(
                "Error", "Please select at least one text region."
            )
            return

        # Process video and save output
        await self.process_and_save()

    async def process_and_save(self):
        # Process video and save output
        with open(self.output_file, "w") as f:
            f.write("Box,Data,Frame,Time,"*len(self.selected_boxes))
            f.write(f"\n")
            for results, frame, meta in ocr_generator(
                subframe_generator(
                    frame_generator(self.video_path, self.interval), self.selected_boxes
                )
            ):
                for idx, result in enumerate(results):
                    try:
                        txts = [
                            detection[1][0] for line in result for detection in line
                        ]
                        f.write(f"{idx+1},{txts[0]},{meta[0]},{meta[1]},")
                    except Exception:
                        f.write(f"{idx+1},no data found,{meta[0]},{meta[1]},")
                        # allow gui to update
                        await asyncio.sleep(0)
                f.write(f"\n")
        self.progress.text = "OCR complete."
        self.main_window.info_dialog(
            "Success", "OCR processing completed and output saved."
        )


def main():
    return VideoOCRApp("vdlgr", "org.example.vdlgr")


if __name__ == "__main__":
    app = main()
    app.main_loop()
