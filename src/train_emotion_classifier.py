"""
File: train_emotion_classifier.py
Author: Octavio Arriaga
Email: arriaga.camargo@gmail.com
Github: https://github.com/oarriaga
Description: Train emotion classification model
"""

from keras.callbacks import CSVLogger, ModelCheckpoint, EarlyStopping
from keras.callbacks import ReduceLROnPlateau
from keras.preprocessing.image import ImageDataGenerator

from models.cnn import mini_XCEPTION
from utils.datasets import DataManager
from utils.datasets import split_data
from utils.preprocessor import preprocess_input
import wandb
from wandb.wandb_keras import WandbKerasCallback

run = wandb.init()
config = run.config

# hyperparameters
config.patience = 50
config.rotation_range = 10
config.width_shift_range = 0.1
config.height_shift_range = 0.1
config.zoom_range = 0.1
config.batch_size = 32
config.num_epochs = 10000

input_shape = (64, 64, 1)
validation_split = .2
verbose = 1
num_classes = 7

base_path = '../trained_models/emotion_models/'



# data generator
data_generator = ImageDataGenerator(
                        featurewise_center=False,
                        featurewise_std_normalization=False,
                        rotation_range=config.rotation_range,
                        width_shift_range=config.width_shift_range,
                        height_shift_range=config.height_shift_range,
                        zoom_range=config.zoom_range,
                        horizontal_flip=True)

# model parameters/compilation
model = mini_XCEPTION(input_shape, num_classes)
model.compile(optimizer='adam', loss='categorical_crossentropy',
              metrics=['accuracy'])
model.summary()


datasets = ['fer2013']
for dataset_name in datasets:
    print('Training dataset:', dataset_name)

    # callbacks
    log_file_path = base_path + dataset_name + '_emotion_training.log'
    csv_logger = CSVLogger(log_file_path, append=False)
    early_stop = EarlyStopping('val_loss', patience=config.patience)
    reduce_lr = ReduceLROnPlateau('val_loss', factor=0.1,
                                  patience=int(config.patience/4), verbose=1)
    trained_models_path = base_path + dataset_name + '_mini_XCEPTION'
    model_names = trained_models_path + '.{epoch:02d}-{val_acc:.2f}.hdf5'
    model_checkpoint = ModelCheckpoint(model_names, 'val_loss', verbose=1,
                                                    save_best_only=True)
    wandb_callback = WandbKerasCallback()
    callbacks = [model_checkpoint, csv_logger, early_stop, reduce_lr, wandb_callback]

    # loading dataset
    data_loader = DataManager(dataset_name, image_size=input_shape[:2])
    faces, emotions = data_loader.get_data()
    faces = preprocess_input(faces)
    num_samples, num_classes = emotions.shape
    train_data, val_data = split_data(faces, emotions, validation_split)
    train_faces, train_emotions = train_data
    model.fit_generator(data_generator.flow(train_faces, train_emotions,
                                            config.batch_size),
                        steps_per_epoch=len(train_faces) / config.batch_size,
                        epochs=config.num_epochs, verbose=1, callbacks=callbacks,
                        validation_data=val_data)
