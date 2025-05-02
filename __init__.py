from .nodes.nodes import *

# Node class mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "ImagePassThrough": ImagePassThrough,
    "ImageToS3": ImageToS3
}

# Human-readable node names
NODE_DISPLAY_NAME_MAPPINGS = {
    "ImagePassThrough": "Image Pass Through",
    "ImageToS3": "Upload Image to S3"
}
