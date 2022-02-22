from importlib import import_module

from django.utils.functional import SimpleLazyObject

settings = SimpleLazyObject(lambda: import_module("worf.settings"))
