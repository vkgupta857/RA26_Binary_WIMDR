#from tensorflow.keras.models import load_model
from PIL import Image, ImageOps
import numpy as np


'''
# keep this file and model in the same directory as the main app file
# in the main app file run this to classify image

import waste_classification as wc
label = wc.predict(path_to_img)


'''

def img_preprocessing(path_to_img):
    image = Image.open(path_to_img)
    image = ImageOps.fit(image, (224,224), Image.ANTIALIAS)
    image = np.asarray(image)
    image = (image.astype(np.float32) / 127.0) - 1
    image = np.array([image])
    return(image)

'''
# Load the model
model = load_model('keras_model.h5')


def predict(path_to_img):
    img = img_preprocessing(path_to_img)
    return(np.argmax(model.predict(img)))

'''


'''
# Create the array of the right shape to feed into the keras model
# The 'length' or number of images you can put into the array is
# determined by the first position in the shape tuple, in this case 1.
data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

# Replace this with the path to your image
image = Image.open('image2.jpg')

#resize the image to a 224x224 with the same strategy as in TM2:
#resizing the image to be at least 224x224 and then cropping from the center
size = (224, 224)
image = ImageOps.fit(image, size, Image.ANTIALIAS)

#turn the image into a numpy array
image_array = np.asarray(image)

# display the resized image
image.show()

# Normalize the image
normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1

# Load the image into the array
data[0] = normalized_image_array

# run the inference
prediction = model.predict(data)
print(prediction)
'''
