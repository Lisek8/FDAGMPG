# SRC: https://becominghuman.ai/lets-build-an-atari-ai-part-1-dqn-df57e8ff3b26
# SRC: https://becominghuman.ai/beat-atari-with-deep-reinforcement-learning-part-2-dqn-improvements-d3563f665a2c
# Import the gym module
import gym
import numpy as np
import keras

def to_grayscale(img):
  return np.mean(img, axis=2).astype(np.uint8)

def downsample(img):
  return img[::2, ::2]

def preprocess(img):
  return to_grayscale(downsample(img))

def transform_reward(reward):
  return np.sign(reward)

def fit_batch(model, target_model, gamma, start_states, actions, rewards, next_states, is_terminal):
  """Do one deep Q learning iteration.
  
  Params:
  - model: The DQN
  - target_model: The target DQN
  - gamma: Discount factor (should be 0.99)
  - start_states: numpy array of starting states
  - actions: numpy array of one-hot encoded actions corresponding to the start states
  - rewards: numpy array of rewards corresponding to the start states and actions
  - next_states: numpy array of the resulting states corresponding to the start states and actions
  - is_terminal: numpy boolean array of whether the resulting state is terminal
  
  """
  # First, predict the Q values of the next states. Note how we are passing ones as the mask.
  next_Q_values = target_model.predict([next_states, np.ones(actions.shape)])
  # The Q values of the terminal states is 0 by definition, so override them
  next_Q_values[is_terminal] = 0
  # The Q values of each start state is the reward + gamma * the max next state Q value
  Q_values = rewards + gamma * np.max(next_Q_values, axis=1)
  # Fit the keras model. Note how we are passing the actions as the mask and multiplying
  # the targets by the actions.
  model.fit(
      [start_states, actions], actions * Q_values[:, None],
      nb_epoch=1, batch_size=len(start_states), verbose=0
  )

def atari_model(n_actions):
  # We assume a theano backend here, so the "channels" are first.
  ATARI_SHAPE = (4, 105, 80)

  # With the functional API we need to define the inputs.
  frames_input = keras.layers.Input(ATARI_SHAPE, name='frames')
  actions_input = keras.layers.Input((self.n_actions,), name='filter')

  conv_1 = keras.layers.convolutional.Convolution2D(2, 8, 8, subsample=(4, 4), activation='relu')(keras.layers.Lambda(lambda x: x / 255.0)(frames_input))
  conv_2 = keras.layers.convolutional.Convolution2D(64, 4, 4, subsample=(2, 2), activation='relu' )(conv_1)
  conv_3 = keras.layers.convolutional.Convolution2D(64, 3, 3, subsample=(1, 1), activation='relu')(conv_2)
  conv_flattened = keras.layers.core.Flatten()(conv_3)
  hidden = keras.layers.Dense(512, activation='relu')(conv_flattened)
  output = keras.layers.Dense(self.n_actions)(hidden)
  filtered_output = keras.layers.merge([output, actions_input], mode='mul')

  self.model = keras.models.Model(input=[frames_input, actions_input], output=filtered_output)
  optimizer = optimizer=keras.optimizers.RMSprop(lr=0.00025, rho=0.95, epsilon=0.01)
  self.model.compile(optimizer, loss=huber_loss)

from keras import backend as K
# Note: pass in_keras=False to use this function with raw numbers of numpy arrays for testing
def huber_loss(a, b, in_keras=True):
  error = a - b
  quadratic_term = error*error / 2
  linear_term = abs(error) - 1/2
  use_linear_term = (abs(error) > 1.0)
  if in_keras:
      # Keras won't let us multiply floats by booleans, so we explicitly cast the booleans to floats
      use_linear_term = K.cast(use_linear_term, 'float32')
  return use_linear_term * linear_term + (1-use_linear_term) * quadratic_term

class RingBuf:
  def __init__(self, size):
    # Pro-tip: when implementing a ring buffer, always allocate one extra element,
    # this way, self.start == self.end always means the buffer is EMPTY, whereas
    # if you allocate exactly the right number of elements, it could also mean
    # the buffer is full. This greatly simplifies the rest of the code.
    self.data = [None] * (size + 1)
    self.start = 0
    self.end = 0
      
  def append(self, element):
    self.data[self.end] = element
    self.end = (self.end + 1) % len(self.data)
    # end == start and yet we just added one element. This means the buffer has one
    # too many element. Remove the first element by incrementing start.
    if self.end == self.start:
        self.start = (self.start + 1) % len(self.data)
      
  def __getitem__(self, idx):
    return self.data[(self.start + idx) % len(self.data)]
  
  def __len__(self):
    if self.end < self.start:
        return self.end + len(self.data) - self.start
    else:
        return self.end - self.start
      
  def __iter__(self):
    for i in range(len(self)):
        yield self[i]

def q_iteration(env, model, state, iteration, memory):
  # Choose epsilon based on the iteration
  epsilon = get_epsilon_for_iteration(iteration)

  # Choose the action 
  if random.random() < epsilon:
      action = env.action_space.sample()
  else:
      action = choose_best_action(model, state)

  # Play one game iteration (note: according to the next paper, you should actually play 4 times here)
  new_frame, reward, is_done, _ = env.step(action)
  memory.add(state, action, new_frame, reward, is_done)

  # Sample and fit
  batch = memory.sample_batch(32)
  fit_batch(model, batch)

def copy_model(model):
  """Returns a copy of a keras model."""
  model.save('tmp_model')
  return keras.models.load_model('tmp_model')

# Create a breakout environment
env = gym.make('BreakoutDeterministic-v4')
# Reset it, returns the starting frame
frame = env.reset()
# Render
env.render()

is_done = False
while not is_done:
  # Perform a random action, returns the new frame, reward and whether the game is over
  frame, reward, is_done, _ = env.step(env.action_space.sample())
  # Render
  env.render()