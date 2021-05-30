# -*- coding: utf-8 -*-
#
# This file is part of UNCode. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

# init language management

import gettext
import os

import inginious.input
import builtins


def get_lang_dir_path():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dir_path, "__lang")


def init():
    """ Install gettext with the default parameters """
    if "_" not in builtins.__dict__:  # avoid installing lang two times
        try:
            os.environ["LANGUAGE"] = inginious.input.get_lang()
        except Exception:
            os.environ["LANGUAGE"] = "en"
        gettext.install("messages", get_lang_dir_path())
