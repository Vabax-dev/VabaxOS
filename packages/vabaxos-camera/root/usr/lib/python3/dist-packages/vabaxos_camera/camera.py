"""The webcam through GStreamer: open once, a frame whenever asked.

    camera = Camera()       the first webcam (or device="/dev/video2")
    camera.start()          CameraError if there is none
    camera.frame()          a PIL picture, or None
    camera.stop()
"""

import glob
import os


class CameraError(RuntimeError):
    pass


def devices():
    """The video devices that capture (index 0 of each camera)."""
    found = []
    for path in sorted(glob.glob("/sys/class/video4linux/video*")):
        try:
            with open(os.path.join(path, "index"), encoding="utf-8") as f:
                if f.read().strip() != "0":
                    continue
        except OSError:
            pass
        found.append("/dev/" + os.path.basename(path))
    return found


class Camera:

    def __init__(self, device=None):
        import gi
        gi.require_version("Gst", "1.0")
        from gi.repository import Gst
        Gst.init(None)
        self.Gst = Gst
        device = device or (devices() or [None])[0]
        if device is None:
            raise CameraError("no camera")
        self.pipeline = Gst.parse_launch(
            f"v4l2src device={device} ! videoconvert ! video/x-raw,format=RGB ! "
            "appsink name=sink max-buffers=1 drop=true sync=false")
        self.sink = self.pipeline.get_by_name("sink")

    def start(self):
        if self.pipeline.set_state(self.Gst.State.PLAYING) == self.Gst.StateChangeReturn.FAILURE:
            raise CameraError("the camera does not start")

    def frame(self, timeout=2):
        from PIL import Image
        sample = self.sink.emit("try-pull-sample", int(timeout * self.Gst.SECOND))
        if sample is None:
            return None
        structure = sample.get_caps().get_structure(0)
        width, height = structure.get_value("width"), structure.get_value("height")
        data = sample.get_buffer().extract_dup(0, sample.get_buffer().get_size())
        stride = len(data) // height if height else width * 3
        return Image.frombytes("RGB", (width, height), data, "raw", "RGB", stride)

    def stop(self):
        self.pipeline.set_state(self.Gst.State.NULL)
