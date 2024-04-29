import os
import time
from datetime import datetime
from enum import Enum
from dotenv import load_dotenv
import tensorflow as tf

from PIL import Image
import numpy as np
import requests
import io
import base64
import gensim.downloader as wv

word_vectors = wv.load("glove-twitter-25")

load_dotenv()

ImageTypes = Enum(
    'ImageTypes',
    'cat dog unknown',
)


class ImageType(str, Enum):
    cat = ImageTypes.cat.name
    dog = ImageTypes.dog.name
    unknown = ImageTypes.unknown.name


class ImageUrlGetter:
    def __init__(self, url):
        self.url = url
        self.max_retries = 3  # Maximum number of retries on failure
        self.timeout = 15

    def get_image(self):
        retries = 0
        while retries < self.max_retries:
            try:
                print("Getting new picture from API")
                response = requests.post(self.url, timeout=self.timeout)
                print(response.status_code)
                response.raise_for_status()
                return response.content
            except requests.exceptions.HTTPError as err:
                print(err)
                retries += 1
                print(f"Retrying... ({retries}/{self.max_retries})")
                time.sleep(1)  # Wait for 1 second before retrying
            except requests.exceptions.Timeout:
                print(f"Request timed out after {self.timeout} seconds")
                retries += 1
                print(f"Retrying... ({retries}/{self.max_retries})")
        print("Maximum retries exceeded. Failed to retrieve image.")
        return None


class Base64ImageDecoder:
    def __init__(self):
        pass

    @staticmethod
    def base64_to_image(base64_string: str):
        try:
            image_data = base64.b64decode(base64_string)
            image = Image.open(io.BytesIO(image_data))
            return image
        except Exception as e:
            print(e)
            return None

    def decode_image(self, base64_string: str):
        image = self.base64_to_image(base64_string)
        return image


class CatsDogsClassifier:
    def __init__(self):
        self.PROB_THRESHOLD = 0.3  # (confidence parameter(how much I am sure it's a cat or a dog))
        self.CONF_THRESHOLD = 0.04  # (how much difference in siilarity will make me sure it is a dog or a cat)
        pass

    @staticmethod
    def get_phrase_vector(phrase: str):
        words = phrase.split("_")
        valid_words = [word for word in words if word in word_vectors]
        if not valid_words:
            return None
        word_vectors_list = [word_vectors[word] for word in valid_words]
        average_vector = np.mean(word_vectors_list, axis=0)
        return average_vector

    def classify_label(self, input_string: str):
        words = input_string.split("_")
        if not isinstance(words, list) or len(words) == 0:
            return ImageType.unknown
        cat_similarity = 0
        dog_similarity = 0
        for word in words:
            try:
                print(word)
                cat_similarity = max(word_vectors.similarity(word, ImageType.cat.value), cat_similarity)
                dog_similarity = max(word_vectors.similarity(word, ImageType.dog.value), dog_similarity)
            except KeyError:
                print("Coudnt find cat or dogness")
                continue

        print(dog_similarity, cat_similarity)

        if cat_similarity < self.PROB_THRESHOLD and dog_similarity < self.PROB_THRESHOLD \
                or abs(cat_similarity - dog_similarity) < self.CONF_THRESHOLD:
            return ImageType.unknown

        if cat_similarity > dog_similarity:
            return ImageType.cat.value
        elif dog_similarity > cat_similarity:
            return ImageType.dog.value
        else:
            return ImageType.unknown.value

    def classify_image(self, image):
        image = image.resize((224, 224))
        image_array = np.array(image) / 255.0
        image_batch = np.expand_dims(image_array, axis=0)
        model = tf.keras.applications.MobileNetV2(weights='imagenet')
        predictions = model.predict(image_batch)
        _, label, prob = tf.keras.applications.mobilenet_v2.decode_predictions(predictions, top=1)[0][0]  # top 1 pred
        print(label, prob)
        return self.classify_label(label)


class ImageProcessor:
    def __init__(self, source_url):
        self.url = source_url
        self.imageGetter = ImageUrlGetter(self.url)
        self.imageDecoder = Base64ImageDecoder()
        self.imageClassifier = CatsDogsClassifier()

    def get_image(self):
        return self.imageGetter.get_image()

    def decode_image(self, image):
        return self.imageDecoder.decode_image(image)

    def process_new_image(self):
        try:
            image = self.get_image()
            if not image:
                return None

            decoded_image = self.decode_image(image)
            if not decoded_image:
                return None

            predicted_class = self.imageClassifier.classify_image(decoded_image)
            print(predicted_class)
            if not predicted_class or predicted_class == ImageType.unknown:
                return None

            timestamp = datetime.now().isoformat()
            return {
                "image": decoded_image,
                "timestamp": timestamp,
                "class": predicted_class
            }
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
