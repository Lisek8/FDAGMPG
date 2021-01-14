# Source: https://www.youtube.com/watch?v=cO5g5qLrLSo
# Import required libs
import gym
import random
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.optimizers import Adam
from rl.agents import DQNAgent
from rl.policy import BoltzmannQPolicy
from rl.memory import SequentialMemory

config = tf.compat.v1.ConfigProto(gpu_options = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction=0.8))
config.gpu_options.allow_growth = True
session = tf.compat.v1.Session(config=config)
tf.compat.v1.keras.backend.set_session(session)

def build_model(states, actions):
  # Sequential model
  model = Sequential()
  model.add(Flatten(input_shape=(1, states)))
  model.add(Dense(24, activation='relu'))
  model.add(Dense(24, activation='relu'))
  model.add(Dense(actions, activation='linear'))
  return model

def build_agent(model, actions):
  policy = BoltzmannQPolicy()
  memory = SequentialMemory(limit=50000, window_length=1)
  dqn = DQNAgent(model=model, memory=memory, policy=policy, nb_actions=actions, nb_steps_warmup=10, target_model_update=1e-2)
  return dqn

# Prepare training environment
env = gym.make('CartPole-v0')
# 4
states = env.observation_space.shape[0]
# 2
actions = env.action_space.n

model = build_model(states, actions)
# Info about model
# model.summary()
dqn = build_agent(model, actions)
dqn.compile(Adam(lr=1e-3), metrics=['mae'])
dqn.fit(env, nb_steps=50000, visualize=False, verbose=1)

# Test model
# scores = dqn.test(env, nb_episodes=10, visualize=False)
# print(np.mean(scores.history['episode_reward']))

# Save training result to file
dqn.save_weights('dqn_weights.h5f', overwrite=True)

# Load training result from file
dqn.load_weights('dqn_weights.h5f')

# Test it
dqn.test(env, nb_episodes=5, visualize=True)