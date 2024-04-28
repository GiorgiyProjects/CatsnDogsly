import tensorflow as tf
from PIL import Image
import numpy as np
import base64
import requests
import io
import base64
import gensim.downloader as wv
from sklearn.metrics.pairwise import cosine_similarity

word_vectors = wv.load("word2vec-google-news-300")

def base64_to_image(base64_string):
    image_data = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(image_data))
    return image


def classify_string(input_string):
    # Define words related to dogs and cats
    dog_words = ["dog", "puppy", "hound", "beagle", "labrador", "golden_retriever"]
    cat_words = ["cat", "kitten", "feline", "tabby", "persian", "siamese"]

    # Calculate average vector representation for each category
    dog_vector = np.mean([word_vectors[word] for word in dog_words if word in word_vectors], axis=0)
    cat_vector = np.mean([word_vectors[word] for word in cat_words if word in word_vectors], axis=0)

    # Calculate cosine similarity between input string and dog/cat vectors
    input_vector = np.mean([word_vectors[word] for word in input_string.split() if word in word_vectors], axis=0)
    dog_similarity = cosine_similarity([input_vector], [dog_vector])[0][0]
    cat_similarity = cosine_similarity([input_vector], [cat_vector])[0][0]

    return "dog" if dog_similarity > cat_similarity else "cat"


def classify_image(image):
    # Resize the image to match the input size expected by the model
    image = image.resize((224, 224))

    # Convert the image to a numpy array
    image_array = np.array(image) / 255.0  # Normalize pixel values

    # Expand dimensions to create a batch of 1 image
    image_batch = np.expand_dims(image_array, axis=0)

    # Load the pre-trained MobileNet model
    model = tf.keras.applications.MobileNetV2(weights='imagenet')

    # Perform inference to classify the image
    predictions = model.predict(image_batch)

    # Decode the predictions
    #predicted_class = tf.keras.applications.mobilenet_v2.decode_predictions(predictions, top=1)[0][0]
    decoded_predictions = tf.keras.applications.mobilenet_v2.decode_predictions(predictions, top=5)[0]

    cat_prob = 0.0
    dog_prob = 0.0
    for _, label, prob in decoded_predictions:
        if "cat" in label.lower():
            cat_prob = max(cat_prob, prob)
        elif "dog" in label.lower():
            dog_prob = max(dog_prob, prob)
        else:
            print("does not contain cat or dog")
            res = classify_string(label)
            print(res)

    return cat_prob, dog_prob

    return predicted_class

url = "https://api.exactly.ai/v0/careers/cat-or-dog/82a27017-f316-46ca-bbd1-3cc4a2c742f9/"
response = requests.post(url)
base64_string = response.json()
if type(base64_string) is dict:
    print(base64_string)
image = base64_to_image(base64_string)
output_file = "image.jpg"
image.save(output_file, "JPEG")
print(f"Image saved as {output_file}")

predicted_class = classify_image(image)
print("Predicted class:", predicted_class)