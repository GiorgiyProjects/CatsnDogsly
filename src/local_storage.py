import base64
import datetime
import json
import os
from src.constants import COUNT_IMAGES


class LocalStorage:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.CLEANUP_AGE = 60

    @staticmethod
    def generate_file_id(image_data):
        img_id = f"{str(image_data['class'])}_{image_data['timestamp']}.jpg"
        return img_id

    def save_img(self, image_data):
        try:
            img_id = self.generate_file_id(image_data)
            image_data["id"] = img_id

            output_path = f"{os.getenv('DATA_PATH')}{str(img_id)}"
            decoded_image = image_data["image"]
            decoded_image.save(output_path, "JPEG")
            print(f"Image saved as {output_path}")
            image_data["path"] = output_path
            del image_data["image"]

            # output_path = f"{os.getenv('DATA_PATH')}/{str(predicted_class)}{file_id}.jpg"
            json_file_path = os.getenv('DATA_PATH') + "metadata.json"
            if not os.path.isfile(json_file_path):
                with open(json_file_path, 'w') as new_file:
                    json.dump({
                        "counter": 0,
                        "images": []
                    }, new_file)

            # Add metadata to the existing JSON file
            with open(json_file_path, 'r+') as file:
                # Load existing JSON data
                json_data = json.load(file)
                json_data['counter'] += 1
                json_data.setdefault('images', []).append(image_data)

                # delete the earliest pushed if length of images exceeds the max_count
                if len(json_data.get('images', [])) > COUNT_IMAGES:
                    # Delete the oldest item from the "images" list
                    del json_data['images'][0]

                file.seek(0)
                json.dump(json_data, file, indent=4)
            return
        except Exception as err:
            raise SystemExit(err)

    def delete_old_files(self):
        json_file_path = os.path.join(os.getenv('DATA_PATH'), "metadata.json")
        protected_paths = [json_file_path]
        with open(json_file_path, 'r+') as file:
            json_data = json.load(file)
            images = json_data.get("images", [])

            for img in images:
                image_path = img.get("path", "")
                protected_paths.append(image_path)

        for file in os.listdir(self.data_path):
            file_path = os.path.join(self.data_path, file)
            if file_path not in protected_paths:
                file_time = os.path.getmtime(file_path)
                if datetime.datetime.now().timestamp() - file_time > self.CLEANUP_AGE:
                    os.remove(file_path)
                    print(f"Deleted {file_path}")

    @staticmethod
    def get_images():
        json_file_path = os.path.join(os.getenv('DATA_PATH'), "metadata.json")
        if not os.path.isfile(json_file_path):
            return []

        print(f"Reading JSON file from: {json_file_path}")

        with open(json_file_path, 'r') as file:
            try:
                json_data = json.load(file)
                images = json_data.get("images", [])

                result = []
                for img in images:
                    image_path = img.get("path", "")
                    if os.path.isfile(image_path):
                        with open(image_path, 'rb') as img_file:
                            base64_string = base64.b64encode(img_file.read()).decode('utf-8')
                            img_ext = {**img, "image": base64_string}
                            del img_ext["path"]
                            result.append(img_ext)
                    else:
                        print(f"Image file not found: {image_path}")

                return result
            except json.JSONDecodeError as e:
                print(f"Error reading JSON file: {e}")

        return []
