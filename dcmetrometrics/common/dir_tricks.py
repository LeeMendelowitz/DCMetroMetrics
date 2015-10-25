import os

def get_dir(f):
  """Get the directory containing a file"""
  f = os.path.abspath(f)
  path = os.path.split(f)[0]
  return path

def up(path, n = 1):
  """Get the directery up n levels. Path should
  be a path to a directory.
  """
  if n <= 0:
    return path
  path = get_dir(path)
  return up(path, n - 1)
