import numpy as np
import pandas as pd
import cv2
import os
import datetime
import pickle
from sklearn import svm


class MinesTimeDigitTraining:
    def __init__(self):
        cwd = os.getcwd()
        self.train_path = os.path.join(cwd, "training")
        self.digits_path = os.path.join(self.train_path, "digits")

    def make_training_set(self):
        # get all images in \training\digits directory, and manually assign correct values to each.
        # csv of img_path, value will be saved to \training
        response_vector = []
        image_path_vector = []
        cwd = os.getcwd()
        dir_list = os.listdir(self.digits_path)
        print(f"Files detected: {len(dir_list)}")
        for file in dir_list:
            if file.endswith('.png'):
                path = self.digits_path
                path = os.path.join(path, file)
                file_image = cv2.imread(path)
                if file_image is None:
                    print("Error: Failed to read file")
                    continue
                cv2.imshow("image", file_image)
                key = cv2.waitKey(0)

                if 48 <= key <= 57:  # Assign digit to image (0 through 9)
                    print(f"Assigned image: {chr(key)}")
                    image_path_vector.append(path)
                    response_vector.append(chr(key))

                elif key == 27:  # (escape to quit)
                    break

                else:  # This image is incorrectly cropped
                    print("Deleting invalid image")
                    os.remove(path)
                    continue
        save_loc = os.path.join(cwd, "training")
        path_digit_matrix = pd.DataFrame(list(zip(image_path_vector, response_vector)),
                                         columns=['Path', 'Value'])
        save_loc = os.path.join(save_loc, "training_dataset" + str(datetime.datetime.now().timestamp()))
        save_loc += ".csv"
        path_digit_matrix.to_csv(save_loc, index=False)

    @staticmethod
    def read_and_serialize_image(image_path: str) -> np.array:

        # Read image path into image (2D np array)
        # Turn an image in a 2D numpy array into a one dimensional vector.
        file_image = None
        if image_path.endswith('.png'):
            file_image = cv2.imread(image_path)
        file_image_gray = cv2.cvtColor(file_image, cv2.COLOR_BGR2GRAY)
        testy = file_image_gray.flatten()
        return testy

    def train_model(self):
        # Train model from a training dataset csv.
        # Load dataset from file and train SVM
        # Save model to pickle to be loaded in main program.
        dir_list = os.listdir(self.train_path)
        training_data_file = None

        for f in dir_list:
            if "training_dataset" in f:
                training_data_file = os.path.join(self.train_path, f)
        if not training_data_file:
            print(f"ERROR: No training dataset found in {self.train_path}, you may need to create one if you have not.")
        training_data = pd.read_csv(training_data_file)

        training_vectors = [self.read_and_serialize_image(training_data.iloc[x, 0]) for x in range(len(training_data))]
        target_vector = [training_data.iloc[x, 1] for x in range(len(training_data))]

        svm_classifier = svm.SVC(gamma=0.001)
        svm_classifier.fit(training_vectors, target_vector)

        # Save to pickle
        filename = 'MinesTime_SVM_model.sav'
        file_path = os.path.join(os.getcwd(), filename)
        pickle.dump(svm_classifier, open(filename, 'wb'))

if __name__ == "__main__":
    # This will train the model and save a pickle for use in running the main program.
    trainer = MinesTimeDigitTraining()
    # trainer.make_training_set()
    trainer.train_model()
