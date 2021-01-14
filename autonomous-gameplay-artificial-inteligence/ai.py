# BASE: https://keras.io/examples/rl/deep_q_network_breakout

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import os
from environment import Environment

# Config GPU usage for tensorFlow
configproto = tf.compat.v1.ConfigProto() 
configproto.gpu_options.allow_growth = True
sess = tf.compat.v1.Session(config=configproto)
tf.compat.v1.keras.backend.set_session(sess)

# Disable GPU usage
# os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

if tf.test.gpu_device_name():
    print('GPU found')
else:
    print("No GPU found")

# Configuration paramaters for the whole setup
discountFactor = 0.99  # Discount factor for past rewards
epsilon = 1.0  # Epsilon greedy parameter
epsilon_min = 0.1  # Minimum epsilon greedy parameter
epsilon_max = 1.0  # Maximum epsilon greedy parameter
epsilon_interval = (
    epsilon_max - epsilon_min
)  # Rate at which to reduce chance of random action being taken
batch_size = 32  # Size of batch taken from replay buffer

# In the Deepmind paper they use RMSProp however then Adam optimizer
# improves training time
optimizer = keras.optimizers.Adam(learning_rate=0.00025, clipnorm=1.0)

# Experience replay buffers
action_history = []
state_history = []
state_next_history = []
rewards_history = []
done_history = []
episode_reward_history = []
running_reward = 0
episode_count = 0
frame_count = 0
# Number of frames to take random action and observe output
epsilon_random_frames = 50000
# Number of frames for exploration
epsilon_greedy_frames = 1000000.0
# Maximum replay length
# Experience replay objects size in bytes: 1000332
# 10000 ~ 10GB
max_memory_length = 10000
# Train the model every 4th action
update_after_actions = 4
# Environemnt downsample factor
downsample_factor = 4
# Frame stack size
frame_stack_size = 4
# Game window size
game_window_width = 600
game_window_height = 432
# How often to update the target network
update_target_network = 10000
# Using huber loss for stability
loss_function = keras.losses.Huber()

# Reward settings
coin_weight = 200
penalty_per_time_unit = 0
# Starting time value for game DO NOT MODIFY
game_time_limit = 400
# Initial weighted random choice probability
# Environment.py: self.actions = ['w', 'a', 'd', 'w|a', 'w|d', 'w|a|shift', 'w|d|shift', 'w|shift', 'd|shift', 'a|shift']
# Order and quantity must match actions for environemnt
weighted_probability = [0.075, 0.025, 0.3, 0.025, 0.075, 0.025, 0.075, 0.075, 0.3, 0.025]

# Backup settings
save_weights_episode_interval = 10
backup_folder_path = "weights"
backup_name_scheme = "weightsE{}.h5f"

def saveWeights(model: keras.Model, episode: int):
    try:
        path = os.path.join(backup_folder_path, str(episode))
        if not os.path.exists(path):
            os.makedirs(path)
        model.save_weights(os.path.join(path, backup_name_scheme.format(episode)))
    except:
        print("Failed to save weights for episode {}".format(episode))

def loadWeights(model: keras.Model, episode: int):
    path = os.path.join(backup_folder_path, str(episode))
    if os.path.exists(path):
        model.load_weights(os.path.join(path, backup_name_scheme.format(episode)))

def createQModel():
    # Network defined by the Deepmind paper
    inputs = layers.Input(shape=(int(game_window_height / downsample_factor), int(game_window_width / downsample_factor), frame_stack_size,))

    # Convolutions on the frames on the screen
    layer1 = layers.Conv2D(32, 8, strides=4, activation="relu")(inputs)
    layer2 = layers.Conv2D(64, 4, strides=2, activation="relu")(layer1)
    layer3 = layers.Conv2D(64, 3, strides=1, activation="relu")(layer2)

    layer4 = layers.Flatten()(layer3)

    layer5 = layers.Dense(512, activation="relu")(layer4)
    action = layers.Dense(num_actions, activation="softmax")(layer5)

    return keras.Model(inputs=inputs, outputs=action)

# Create Mario environment with visualization
env = Environment(game_window_width, game_window_height, True, downsample_factor, frame_stack_size)
env.open()
num_actions = len(env.actions)

# The first model makes the predictions for Q-values which are used to
# make a action.
model = createQModel()
# Build a target model for the prediction of future rewards.
# The weights of a target model get updated every 10000 steps thus when the
# loss between the Q-values is calculated the target Q-value is stable.
model_target = createQModel()

# Restore weights from backup
# episode_count = 10
# loadWeights(model, episode_count)
# loadWeights(model_target, episode_count)
# episode_count += 1

while True:  # Run until solved
    state = env.reset()
    episode_reward = 0
    coins = 0
    game_time = game_time_limit
    while True:
        frame_count += 1

        # Use epsilon-greedy for exploration
        if frame_count < epsilon_random_frames or epsilon > np.random.rand(1)[0]:
            # Take random action
            action = np.random.choice(num_actions, p=weighted_probability)
        else:
            # Predict action Q-values
            # From environment state
            state_tensor = tf.convert_to_tensor(state)
            state_tensor = tf.expand_dims(state_tensor, 0)
            action_probs = model(state_tensor, training=False)
            # Take best action
            action = tf.argmax(action_probs[0]).numpy()

        # Decay probability of taking random action
        epsilon -= epsilon_interval / epsilon_greedy_frames
        epsilon = max(epsilon, epsilon_min)

        # Apply the sampled action in our environment
        done, current_state = env.step(env.actions[action])
        state_next = np.array(current_state['image'])

        # Save actions and states in replay buffer
        action_history.append(action)
        state_history.append(state)
        state_next_history.append(state_next)
        done_history.append(done)
        rewards_history.append((current_state['score'] - episode_reward) + ((current_state['coins'] - coins) * coin_weight) - ((game_time - current_state['time']) * penalty_per_time_unit))
        state = state_next
        coins = current_state['coins']

        episode_reward = current_state['score'] + (current_state['coins'] * coin_weight) - ((game_time_limit - current_state['time']) * penalty_per_time_unit)

        # Update every 4th action and once batch size is over 32
        if frame_count % update_after_actions == 0 and len(done_history) > batch_size:

            # Get indices of samples for replay buffers
            indices = np.random.choice(range(len(done_history)), size=batch_size)

            # Using list comprehension to sample from replay buffer
            state_sample = np.array([state_history[i] for i in indices])
            state_next_sample = np.array([state_next_history[i] for i in indices])
            rewards_sample = [rewards_history[i] for i in indices]
            action_sample = [action_history[i] for i in indices]
            done_sample = tf.convert_to_tensor(
                [float(done_history[i]) for i in indices]
            )

            # Build the updated Q-values for the sampled future states
            # Use the target model for stability
            future_rewards = model_target.predict(state_next_sample)
            # Q value = reward + discount factor * expected future reward
            updated_q_values = rewards_sample + discountFactor * tf.reduce_max(
                future_rewards, axis=1
            )

            # If final frame set the last value to -1
            updated_q_values = updated_q_values * (1 - done_sample) - done_sample

            # Create a mask so we only calculate loss on the updated Q-values
            masks = tf.one_hot(action_sample, num_actions)

            with tf.GradientTape() as tape:
                # Train the model on the states and updated Q-values
                q_values = model(state_sample)

                # Apply the masks to the Q-values to get the Q-value for action taken
                q_action = tf.reduce_sum(tf.multiply(q_values, masks), axis=1)
                # Calculate loss between new Q-value and old Q-value
                loss = loss_function(updated_q_values, q_action)

            # Backpropagation
            grads = tape.gradient(loss, model.trainable_variables)
            optimizer.apply_gradients(zip(grads, model.trainable_variables))

        if frame_count % update_target_network == 0:
            # update the the target network with new weights
            model_target.set_weights(model.get_weights())
            # Log details
            template = "running reward: {:.2f} at episode {}, frame count {}"
            print(template.format(running_reward, episode_count, frame_count))

        # Limit the state and reward history
        if len(rewards_history) > max_memory_length:
            del rewards_history[:1]
            del state_history[:1]
            del state_next_history[:1]
            del action_history[:1]
            del done_history[:1]

        if done:
            break
    print('Episode {} reward: {}'.format(episode_count, episode_reward))
    # Update running reward to check condition for solving
    episode_reward_history.append(episode_reward)
    if len(episode_reward_history) > 100:
        del episode_reward_history[:1]
    running_reward = np.sum(episode_reward_history)

    if episode_count % save_weights_episode_interval == 0:
        saveWeights(model, episode_count)

    episode_count += 1

    if running_reward > 500000:  # Condition to consider the task solved
        print("Solved at episode {}!".format(episode_count))
        break
