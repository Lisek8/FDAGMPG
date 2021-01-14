import numpy as np

# SRC: https://becominghuman.ai/lets-build-an-atari-ai-part-1-dqn-df57e8ff3b26

class Preprocessing:

  @staticmethod
  def toGrayscale(img):
    return np.mean(img, axis=2).astype(np.uint8)

  @staticmethod
  def downsample(img, downsamplingFactor: int = 2):
    return img[::downsamplingFactor, ::downsamplingFactor]