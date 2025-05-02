import numpy as np
import io
import boto3
import torch
from PIL import Image, ImageDraw, ImageFont
import os
import time
import uuid

def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0) 
       
class ImagePassThrough:     

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
               
        return {
            "required": {
                "image": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "pass_through"
    CATEGORY = "🧩 Tutorial Nodes"

    def pass_through(self, image):
        """
        Simply returns the input image without modification.
        
        Parameters:
        -----------
        image : torch.Tensor
            Input image tensor in ComfyUI format
            
        Returns:
        --------
        tuple
            Contains the same image tensor
        """

        print(f"Received image")

        return (image,)

class ImageToS3:
    """
    A node that receives an image and uploads it to an S3 bucket.
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):

        return {
            "required": {
                "image": ("IMAGE",),
                "bucket_name": ("STRING", {
                    "default": "your-bucket-name",
                    "multiline": False
                }),
                "file_prefix": ("STRING", {
                    "default": "comfyui_image_",
                    "multiline": False
                }),
                "image_format": (["png", "jpeg", "webp"],),
                "aws_access_key": ("STRING", {
                    "default": AWS_ACCESS_KEY,
                    "multiline": False
                }),
                "aws_secret_key": ("STRING", {
                    "default": AWS_SECRET_KEY,
                    "multiline": False
                }),
                "aws_region": ("STRING", {
                    "default": AWS_REGION,
                    "multiline": False
                }),
            },
            "optional": {
                "image_quality": ("INT", {
                    "default": 95,
                    "min": 1,
                    "max": 100,
                    "step": 1
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "s3_url")
    FUNCTION = "upload_to_s3"
    CATEGORY = "utils/aws"
    
    def upload_to_s3(self, image, bucket_name, file_prefix, image_format, aws_access_key, aws_secret_key, aws_region, image_quality=95):
        """
        Uploads the input image to an S3 bucket and returns the image and S3 URL.
        
        Parameters:
        -----------
        image : torch.Tensor
            Input image tensor in ComfyUI format
        bucket_name : str
            Name of the S3 bucket
        file_prefix : str
            Prefix for the file name in S3
        image_format : str
            Format to save the image (png, jpeg, webp)
        aws_access_key : str
            AWS access key ID
        aws_secret_key : str
            AWS secret access key
        aws_region : str
            AWS region
        image_quality : int
            Quality for JPEG and WebP images (1-100)
            
        Returns:
        --------
        tuple
            Contains the original image tensor and the S3 URL
        """
        try:
            # Use environment variables if credentials are not provided
            if not aws_access_key:
                aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
            if not aws_secret_key:
                aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
            
            # Check if we have credentials
            if not aws_access_key or not aws_secret_key:
                print("Error: AWS credentials not provided. Please provide them as inputs or set environment variables.")
                return (image, "Error: AWS credentials not provided")
            
            # Convert image tensor to PIL Image
            # First, make sure it's on CPU and the right shape
            i = 0
            if len(image.shape) == 4:
                img_tensor = image[i].cpu().numpy()
            else:
                img_tensor = image.cpu().numpy()
            
            # Convert from float [0,1] to uint8 [0,255]
            img_np = (img_tensor * 255).astype(np.uint8)
            
            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(img_np)
            
            # Create a buffer to store the image
            image_buffer = io.BytesIO()
            
            # Save image to buffer
            if image_format == "png":
                pil_image.save(image_buffer, format="PNG")
            elif image_format == "jpeg":
                pil_image.save(image_buffer, format="JPEG", quality=image_quality)
            else:  # webp
                pil_image.save(image_buffer, format="WEBP", quality=image_quality)
            
            # Reset buffer position
            image_buffer.seek(0)
            
            # Generate a unique filename
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{file_prefix}{timestamp}-{unique_id}.{image_format}"
            
            # Configure S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
            
            # Upload to S3
            s3_client.upload_fileobj(
                image_buffer,
                bucket_name,
                filename,
                ExtraArgs={'ContentType': f'image/{image_format}'}
            )
            
            # Generate the URL
            s3_url = f"https://{bucket_name}.s3.{aws_region}.amazonaws.com/{filename}"
            print(f"Successfully uploaded image to S3: {s3_url}")
            
            return (image, s3_url)
            
        except Exception as e:
            import traceback
            error_message = f"Error uploading to S3: {str(e)}"
            print(error_message)
            print(traceback.format_exc())  # Print the full error traceback for debugging
            return (image, error_message)   
        
