import math
import os.path as path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from keras.utils.np_utils import to_categorical
from keras.models import Sequential, Model
from keras.callbacks import EarlyStopping
from keras.layers import Conv2D, BatchNormalization, Dropout, MaxPooling2D, Dense, Flatten, Activation, LeakyReLU, GlobalMaxPooling2D, AveragePooling2D
from keras.preprocessing.image import ImageDataGenerator
from keras.regularizers import l2
from keras.layers import average, Input, Concatenate, GlobalAveragePooling2D, Reshape, Dense, multiply, Permute
from augmentation_methods import *
from keras import layers
from keras import backend as K
from keras.optimizers import Adam

################################################ Define Helper Functions ########################################################

""" Reads in data. """
def load_and_format(in_path):
    out_df = pd.read_json(in_path)
    out_images = out_df.apply(lambda c_row: [np.stack([c_row['band_1'],c_row['band_2']], -1).reshape((75,75,2))],1)
    out_images = np.stack(out_images).squeeze()
    return out_df, out_images


""" Constructs a residual building block. The block contains two convolution layers, with the identity skip connection added to       the output of the second conv layer. """
def residual_block(cnn, nb_channels, _strides=(1, 1), _project_shortcut=False):
    #Store our input features -- we will want to add it to the output to form the identity skip connection
    shortcut = cnn

    # down-sampling is performed with a stride of 2
    cnn = BatchNormalization()(cnn)
    cnn = Activation('relu')(cnn)
    cnn = Conv2D(nb_channels, kernel_size=(3, 3), strides=_strides, padding='same', use_bias=False)(cnn)

    cnn = BatchNormalization()(cnn)
    cnn = Activation('relu')(cnn)
    cnn = Conv2D(nb_channels, kernel_size=(3, 3), strides=(1, 1), padding='same', use_bias=False)(cnn)

    # Utilize if the input and output are of different dimensions
    if _project_shortcut or _strides != (1, 1):
        # when the dimensions increase projection shortcut is used to match dimensions (done by 1×1 convolutions)
        # when the shortcuts go across feature maps of two sizes, they are performed with a stride of 2
        shortcut = Conv2D(nb_channels, kernel_size=(1, 1), strides=_strides, padding='same', use_bias=False)(shortcut)
    

    ratio = 8
    channel_axis = 1 if K.image_data_format() == "channels_first" else -1
    se_shape = (1, 1, nb_channels)

    se = GlobalAveragePooling2D()(cnn)
    se = Reshape(se_shape)(se)
    se = Dense(nb_channels // ratio, activation='relu', use_bias=False)(se)
    se = Dense(nb_channels, activation='sigmoid', use_bias=False)(se)

    if K.image_data_format() == 'channels_first':
        se = Permute((3, 1, 2))(se)

    cnn = multiply([cnn, se])
    
    #Add identity skip connection to our output
    cnn = layers.add([shortcut, cnn])
    return cnn

##################################################### Set up data ###############################################################

#obtain locations of the data
dir_path = path.abspath(path.join('__file__',"../.."))
train_path = dir_path + "/train.json"
test_path = dir_path + "/test.json"

#read in data
train_df, train_images = load_and_format(train_path)
test_df, test_images = load_and_format(test_path)
train_df.inc_angle = train_df.inc_angle.replace('na', 0)
x_angle_train = np.array(train_df.inc_angle)
x_angle_test = np.array(test_df.inc_angle)   
y_train = to_categorical(train_df["is_iceberg"])

#Split train data into train set and validation set
x_train, x_val, x_angle_train, x_angle_val, y_train, y_val = train_test_split(train_images, x_angle_train, y_train, train_size=0.7)

print('Train', x_train.shape, y_train.shape)
print('Validation', x_val.shape, y_val.shape) 

################################################ Construct network architecture #################################################

image_input = Input(shape=(75, 75, 2), name="image")
angle_input = Input(shape=[1], name='angle')

cnn = BatchNormalization()(image_input)

cnn = Conv2D(32, kernel_size=(3,3), padding = 'same', use_bias=False)(cnn)
cnn = Activation('relu')(cnn)


cnn = residual_block(cnn, 32)
cnn = residual_block(cnn, 32)
cnn = AveragePooling2D((2,2))(cnn)

cnn = residual_block(cnn, 32)
cnn = residual_block(cnn, 32)
cnn = AveragePooling2D((2,2))(cnn)

cnn = residual_block(cnn, 32)
cnn = residual_block(cnn, 32)
cnn = AveragePooling2D((2,2))(cnn)

cnn = residual_block(cnn, 32)
cnn = residual_block(cnn, 32)
cnn = AveragePooling2D((2,2))(cnn)

cnn = residual_block(cnn, 32)
cnn = residual_block(cnn, 32)
cnn = AveragePooling2D((2,2))(cnn)


cnn = Flatten()(cnn)
#Concatenate the incidence angle features
cnn = Concatenate()([cnn, BatchNormalization()(angle_input)])

#Fully-connected layer allows network to learn relationship between image features and incidence angle
cnn = Dense(50, activation='relu', use_bias=False)(cnn)

output = Dense(2, activation='softmax', use_bias=False)(cnn)

####################################################### Train Network ###########################################################

model = Model(inputs=[image_input, angle_input], outputs=output)
model.compile(optimizer='adam', loss = 'binary_crossentropy', metrics = ['accuracy', 'binary_crossentropy'])
model.summary()
early_stopping = EarlyStopping(monitor = 'val_binary_crossentropy', patience = 7)
model.fit([x_train, x_angle_train], y_train, batch_size = 64, validation_data = ([x_val, x_angle_val], y_val), 
          epochs = 100, shuffle = True, callbacks=[early_stopping])

######################################################## Predict ################################################################

print("predicting")
test_predictions = model.predict([test_images, x_angle_test])

pred_df = test_df[['id']].copy()
pred_df['is_iceberg'] = test_predictions[:,1]
print("creating csv")
pred_df.to_csv('predictions_3.csv', index = False)