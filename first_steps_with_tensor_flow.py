# -*- coding: utf-8 -*-
"""
Created on Wed Mar 14 09:29:45 2018

@author: admin
"""

# SETUP
import math

from IPython import display
from matplotlib import cm
from matplotlib import gridspec
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from sklearn import metrics
import tensorflow as tf
from tensorflow.python.data import Dataset

tf.logging.set_verbosity(tf.logging.ERROR)
pd.options.display.max_rows = 10
pd.options.display.float_format = '{:.1f}'.format

# Load data
california_housing_dataframe = pd.read_csv("https://storage.googleapis.com/mledu-datasets/california_housing_train.csv", sep=",")

# Randomize input
california_housing_dataframe = california_housing_dataframe.reindex(
        np.random.permutation(california_housing_dataframe.index))
california_housing_dataframe["median_house_value"] /= 1000.0
print(california_housing_dataframe)

# Brief description
california_housing_dataframe.describe()

# CREATING_THE_MODEL
# Define the input feature
my_feature = california_housing_dataframe[["total_rooms"]]

# Configure a numeric feature
feature_columns = [tf.feature_column.numeric_column("total_rooms")]
# NOTE: why doesn't tf.feature_column.numeric_column() take in my_feature
# as the parameter? Why does it take in a string instead?
# is it just saying that we have a feature column called "total_rooms" that 
# holds numeric data?

# Define the target/ label
targets = california_housing_dataframe["median_house_value"]

# Configure the linear regressor
# Use Gradient Descent as the model's optimizer
my_optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.0000001)
# Clip gradients
my_optimizer = tf.contrib.estimator.clip_gradients_by_norm(my_optimizer, 5.0)

# Configure the linear regressor model with our feature columns and optimizer
# Set a learning rate of 0.0000001 for Gradient Descent.
linear_regressor = tf.estimator.LinearRegressor(
        feature_columns=feature_columns,
        optimizer=my_optimizer
        )

# DEBUG:
print("pandas data: ")
print(my_feature)
test = {key:np.array(value) for key, value in dict(my_feature).items()}
print("numpy dict data : ")
print(test)

# PRE-PROCESSING THE DATA
# Create an input_function that prepares dataset for training
def my_input_fn(features, targets, batch_size=1, shuffle=True, num_epochs=None):
    """ Trains a linear regression model of one feature.
    
    Args:
        features: pandas DataFrame of features
        targets: pandas DataFrame of targets
        batch_size: Size of batches to be passed to model
        shuffle: True or False. Whether to shuffle data
        num_epochs: Number of epochs for which data should be repeated. None = repeat indefinitely
    Returns:
        Tuple of (features, label) for next data batch
    """
    
    # Convert pandas data into a dict of np arrays.
    features = {key:np.array(value) for key, value in dict(features).items()}

    # Construct a dataset, and configure batching/ repeating
    ds = Dataset.from_tensor_slices((features, targets))    # 2GB limit
    ds = ds.batch(batch_size).repeat(num_epochs)
    # if num_epochs is set to NONE, how many batches will be in the dataset?
    
    # Shuffle the data, if specified
    if shuffle:
        ds = ds.shuffle(buffer_size=10000)
        
    # Return the next batch of data
    features, labels = ds.make_one_shot_iterator().get_next()
    return features, labels

# TRAINING THE MODEL
_ = linear_regressor.train(
        input_fn = lambda:my_input_fn(my_feature, targets),
        steps = 100
    )

# EVALUATING THE MODEL
# Note: Evaluate how our model fits our training data, not necessarily
# how well our Model will perform when making generalizations
# Create an input function for predictions.
# Note: since only one prediction is made per example, there is no 
# need to repeat or shuffle the data here.
prediction_input_fn =lambda: my_input_fn(my_feature, targets, num_epochs=1, shuffle=False)

# Call predict() on the linear_regresor tomake predictions
predictions = linear_regressor.predict(input_fn=prediction_input_fn)

# Format predictions as a NumPy array, so we can calculate error metrics.
predictions = np.array([item['predictions'][0] for item in predictions])

# Print Mean Squared Error and Root Mean Squared Error.
mean_squared_error = metrics.mean_squared_error(predictions, targets)  
root_mean_squared_error = math.sqrt(mean_squared_error)
print ("Mean Squared Error (on training data): %0.3f" % mean_squared_error)
print ("Root Mean Squared Error (on training data): %0.3f" % root_mean_squared_error)  

min_house_value = california_housing_dataframe["median_house_value"].min()
max_house_value = california_housing_dataframe["median_house_value"].max()
min_max_difference = max_house_value - min_house_value

print ("Min. Median House Value: %0.3f" % min_house_value)
print ("Max. Median House Value: %0.3f" % max_house_value)
print ("Difference between Min. and Max.: %0.3f" % min_max_difference)
print ("Root Mean Squared Error: %0.3f" % root_mean_squared_error)

# IMPROVING OUR MODEL
calibration_data = pd.DataFrame()
calibration_data["predictions"] = pd.Series(predictions)
calibration_data["targets"] = pd.Series(targets)
calibration_data.describe()
# Adding the RMSE to the prediction's average gives roughly the 
# target's average...

# Graph our results 
# get uniform random sample of our data
sample = california_housing_dataframe.sample(n=300)

# Get the min and max total_rooms values.
x_0 = sample["total_rooms"].min()
x_1 = sample["total_rooms"].max()

# Retreive the final weight and bias generated during training
weight = linear_regressor.get_variable_value('linear/linear_model/total_rooms/weights')[0]
bias = linear_regressor.get_variable_value('linear/linear_model/bias_weights')

# Get the predicted median_house_values for the min and max total_rooms values.
y_0 = weight * x_0 + bias
y_1 = weight * x_1 + bias

# Plot our regression line from (x_0, y_0) to (x_1, y_1). Set up bounds?
plt.plot([x_0, x_1], [y_0, y_1], c='r')

# Label the graph axes
plt.ylabel("median_house_values")
plt.xlabel("total_rooms")

# Plot a scatter plot from our data sample.
plt.scatter(sample["total_rooms"], sample["median_house_value"])

# Display graph
plt.show()
# the line we get shows us that our model is totally off and suggests that we 
# can find a much better line to fit our data.
# also, the total rooms has such high numbers because we are looking at 
# city blocks, not just individual houses

def train_model(learning_rate, steps, batch_size, input_feature="population"):
    """Trains a linear regression model of one feature.
    
    Args:
        learning_rate: A `float`, the learning rate.
        steps: A non-zero `int`, the total number of training steps. A training 
            step consists of a forward and a backward pass using a single batch
        batch_size: a non-zero `int`, the batch size
        input_feature: A `string` specifying a column from the `california_housing_dataframe`
            to use as an input feature
    """
    
    periods = 10
    steps_per_period = steps/periods
    
    my_feature = input_feature
    my_feature_data = california_housing_dataframe[[my_feature]]
    my_label = "median_house_value"
    targets = california_housing_dataframe[my_label]

    # Create feature columns
    feature_columns = [tf.feature_column.numeric_column(my_feature)]
    
    # Create input functions
    training_input_fn = lambda:my_input_fn(my_feature_data, targets, batch_size=batch_size)
    prediction_input_fn = lambda: my_input_fn(my_feature_data, targets, num_epochs=1, shuffle=False)
    
    # Create a linear regressor object
    my_optimizer = tf.train.GradientDescentOptimizer(learning_rate=learning_rate)
    my_optimizer = tf.contrib.estimator.clip_gradients_by_norm(my_optimizer, 5.0)
    linear_regressor = tf.estimator.LinearRegressor(
            feature_columns=feature_columns,
            optimizer=my_optimizer
            )
    
    # Set up to plt the state of our model's line each period
    plt.figure(figsize=(15,6))
    plt.subplot(1,2,1)
    plt.title("Learned Line by Period")
    plt.ylabel(my_label)
    plt.xlabel(my_feature)
    sample = california_housing_dataframe.sample(n=300)
    plt.scatter(sample[my_feature], sample[my_label])
    colors = [cm.coolwarm(x) for x in np.linspace(-1, 1, periods)]
    
    # Train the model, but do so inside a loop that we can periodically assess
    # loss metrics.
    print ("Training model...")
    print ("RMSE (on training data): ")
    root_mean_squared_errors = []
    for period in range(0, periods):
        # Train the model, starting from the prior state.
        linear_regressor.train(
                input_fn=training_input_fn,
                steps=steps_per_period
                )
        # Take a break and compute predictions.
        predictions = linear_regressor.predict(input_fn=prediction_input_fn)
        predictions = np.array([item['predictions'][0] for item in predictions])
        
        # Compute loss.
        root_mean_squared_error = math.sqrt(
                metrics.mean_squared_error(predictions, targets))
        # Occasionally print the current loss
        print ("period %0.2d : %0.2f" % (period, root_mean_squared_error))
        # Add th eloss metrics from the period to our list.
        root_mean_squared_errors.append(root_mean_squared_error)
        # Finally, track the weights and biases over time.
        # Apply some math to ensure that the data and line are plotted neatly.
        y_extents = np.array([0, sample[my_label].max()])
        
        weight = linear_regressor.get_variable_value('linear/linear_model/%s/weights' %input_feature)[0]
        bias = linear_regressor.get_variable_value('linear/linear_model/bias_weights')
        
        x_extents = (y_extents - bias) / weight
        x_extents = np.maximum(np.minimum(x_extents,
                                          sample[my_feature].max()),
                                sample[my_feature].min())
        y_extents = weight * x_extents + bias
        plt.plot(x_extents, y_extents, color=colors[period])
    print ("Model training finished.")
    
    # Output a graph of loss metrics over periods.
    plt.subplot(1,2,2)
    plt.ylabel('RMSE')
    plt.xlabel('Periods')
    plt.title("Root Mean Squared Error vs. Periods")
    plt.tight_layout()
    plt.plot(root_mean_squared_errors)
    
    # Output a table with calibration data.
    calibration_data = pd.DataFrame()
    calibration_data["predictions"] = pd.Series(predictions)
    calibration_data["targets"] = pd.Series(targets)
    display.display(calibration_data.describe())
    
    print ("Final RMSE (on training data): %0.2f" % root_mean_squared_error)


# TASK 1: ACHIEVE AN RMSE OF 180 OR BELOW
#train_model(
#    learning_rate=0.0001,
#    steps=100,
#    batch_size=1,
#    input_feature="total_rooms"
#    )

# TASK 2: USE POPULATION INSTEAD OF TOTAL ROOMS
train_model(
        learning_rate=0.0002,
        steps=200,
        batch_size=100,
        input_feature="population"
        )







