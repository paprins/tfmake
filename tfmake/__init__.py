try:
   # Python 3x
   import importlib.metadata as importlib_metadata
except ModuleNotFoundError:
   # Python 2.x
   import importlib_metadata

try:
   __version__ = importlib_metadata.version(__name__)

except importlib_metadata.PackageNotFoundError:
   __version__ = None