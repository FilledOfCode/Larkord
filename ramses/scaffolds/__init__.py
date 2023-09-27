import os
import subprocess

from six import moves
from pyramid.scaffolds import PyramidTemplate


class RamsesStarterTemplate(PyramidTemplate):
    _template_dir = 'ramses_starter