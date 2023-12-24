from yaetos.etl_utils import ETL_Base, Commandliner, Path_Handler
from transformers import AlbertTokenizer, TFAlbertForSequenceClassification
from transformers import InputExample, InputFeatures
from transformers import file_utils
import tensorflow as tf
import numpy as np
import pandas as pd


class Job(ETL_Base):
    MODEL_NAME = 'albert-base-v2' # or other version of ALBERT

    def transform(self, training_set):
        print(file_utils.default_cache_path)

        x_train, y_train = self.get_training_data()
        x_train = self.preprocess(x_train)
        model = self.finetune_model(x_train, y_train)
        path = Path_Handler(self.jargs.output_model['path'], self.jargs.base_path, self.jargs.merged_args.get('root_path')).expand_now(now_dt=self.start_dt)
        self.save_model(model, path)

        # path = self.jargs.output_model['path'].replace('{now}/', '{latest}/')
        # path = Path_Handler(path, self.jargs.base_path, self.jargs.merged_args.get('root_path')).expand_later()
        # model = self.reload(path)

        evaluations = self.evaluate(model)
        return evaluations

    def get_training_data(self):
        # Sample training data (texts and labels)
        texts = ["Sample text 1", "Sample text 2"]
        labels = [0, 1]  # Corresponding labels for the texts
        return texts, labels

    def preprocess(self, texts):
        tokenizer = AlbertTokenizer.from_pretrained(self.MODEL_NAME)
        encoded_inputs = tokenizer(texts, padding=True, truncation=True, max_length=128, return_tensors="tf")
        x = [encoded_inputs['input_ids'], encoded_inputs['attention_mask']]
        return x

    def finetune_model(self, x_train, y_train):
        # Load model
        model = TFAlbertForSequenceClassification.from_pretrained(self.MODEL_NAME)

        # Convert labels to a TensorFlow tensor
        y_train = tf.constant(y_train)

        # Define loss function and optimizer
        loss_function = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        optimizer = tf.keras.optimizers.Adam(learning_rate=5e-5)

        # Compile the model
        model.compile(optimizer=optimizer, loss=loss_function, metrics=['accuracy'])

        # Train the model
        model.fit(x=x_train, y=y_train, batch_size=8, epochs=3)
        return model

    def save_model(self, model, path):
        model.save(path)

    def reload_model(self, path):
        return tf.keras.models.load_model(path)

    def predict(self, model, x):
        predictions = model.predict(x)
        # The predictions are in logits (raw scores), so we apply a softmax to convert them to probabilities
        probabilities = tf.nn.softmax(predictions.logits, axis=-1).numpy()

        # Take the argmax to get the most likely class
        predicted_classes = np.argmax(probabilities, axis=-1)
        return predicted_classes

    def evaluate(self, model):
        tests = ["Sample text 1",
                 "Sample text 2",
                 "other"]
        x = self.preprocess(tests)
        predictions = self.predict(model, x)
        return pd.DataFrame({'tests': tests, 'predictions': predictions})


if __name__ == "__main__":
    args = {'job_param_file': 'conf/jobs_metadata.yml'}
    Commandliner(Job, **args)
