try:
   try:
      # When Python >= 3.8
      from importlib import metadata as importlib_metadata

   except ImportError:
      # When Python < 3.8
      import importlib_metadata

   __version__ = importlib_metadata.version(__package__)

except ImportError:
   __version__ = 'unknown'