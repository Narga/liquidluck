#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
PROJDIR = os.path.abspath(os.path.dirname(__file__))
import sys
import logging
from liquidluck.options import g, settings
from liquidluck.utils import import_object, walk_dir

from liquidluck.writers.base import load_jinja, find_theme


def create_settings(filepath):
    if not filepath:
        filetype = raw_input(
            'Select a config format ([yaml], python, json):  '
        ) or 'yaml'

        if filetype not in ['yaml', 'python', 'json']:
            print('format not supported')
            return

        suffix = {'yaml': '.yml', 'python': '.py', 'json': '.json'}
        filepath = 'settings%s' % suffix[filetype]

    content = raw_input('posts folder (content): ') or 'content'
    output = raw_input('output folder (deploy): ') or 'deploy'
    if filepath.endswith('.py'):
        f = open(os.path.join(PROJDIR, 'tools', '_settings.py'))
        text = f.read()
        f.close()
    elif filepath.endswith('.json'):
        f = open(os.path.join(PROJDIR, 'tools', '_settings.json'))
        text = f.read()
        f.close()
    else:
        f = open(os.path.join(PROJDIR, 'tools', '_settings.yml'))
        text = f.read()
        f.close()

    text = text.replace('content', content)
    if content and not content.startswith('.') and not os.path.exists(content):
        os.makedirs(content)
    text = text.replace('deploy', output)
    f = open(filepath, 'w')
    f.write(text)
    f.close()


def get_settings_path(base_path):
    config = [
        'settings.yml', 'settings.json', 'settings.yaml', 'settings.py',
    ]

    for f in config:
        path = os.path.join(base_path, f)
        if os.path.exists(path):
            return path
    return None


def find_settings_path():
    #: find local directory
    path = get_settings_path(os.getcwd())
    if path:
        logging.info("Use local settings: %s" % path)
        return path

    info = os.path.join(g.theme_gallery, 'info')
    if not os.path.exists(info):
        raise OSError("Can't find settings")

    f = open(info)
    theme = os.path.join(g.theme_gallery, f.read())
    f.close()

    if not os.path.exists(theme):
        raise OSError("Can't find settings")

    path = get_settings_path(theme)
    if path:
        logging.info("Use global settings: %s" % path)
        return path
    raise OSError("Can't find settings")


def parse_settings(path, filetype='yaml'):
    if path.endswith('.py'):
        filetype = 'python'
    elif path.endswith('.json'):
        filetype = 'json'

    def parse_py_settings(path):
        config = {}
        execfile(path, {}, config)
        return config

    def parse_yaml_settings(path):
        from yaml import load
        try:
            from yaml import CLoader
            MyLoader = CLoader
        except ImportError:
            from yaml import Loader
            MyLoader = Loader

        config = load(open(path), MyLoader)
        return config

    def parse_json_settings(path):
        try:
            import json
        except ImportError:
            import simplejson
            json = simplejson

        f = open(path)
        content = f.read()
        f.close()
        config = json.loads(content)
        return config

    if filetype == 'python':
        return parse_py_settings(path)
    elif filetype == 'json':
        return parse_json_settings(path)
    return parse_yaml_settings(path)


def load_settings(path):
    if not path:
        path = find_settings_path()

    def update_settings(arg):
        if not arg:
            return
        if isinstance(arg, dict):
            config = arg
        else:
            config = parse_settings(arg)
        for key in config:
            setting = config[key]
            if isinstance(setting, dict) and key in settings:
                settings[key].update(setting)
            else:
                settings[key] = setting

    #: preload default config
    update_settings(os.path.join(PROJDIR, 'tools', '_settings.py'))

    if path.startswith(g.theme_gallery):
        update_settings(path)
    else:
        config = parse_settings(path)
        theme_name = config.get('theme', {}).get('name')
        #: load theme config first
        theme_settings = get_settings_path(find_theme(theme_name))
        update_settings(theme_settings)
        #: load user config
        update_settings(config)

    g.output_directory = os.path.abspath(settings.config.get('output'))
    g.static_directory = os.path.abspath(settings.config.get('static'))
    logging.info('Load Settings Finished')

    sys.path.insert(0, find_theme())
    cwd = os.path.split(os.path.abspath(path))[0]
    sys.path.insert(0, cwd)


def load_posts(path):
    g.source_directory = path
    readers = []
    for name in settings.reader.get('active'):
        readers.append(import_object(name))

    def detect_reader(filepath):
        for Reader in readers:
            reader = Reader(filepath)
            if reader.support():
                return reader.run()
        return None

    for filepath in walk_dir(path):
        post = detect_reader(filepath)
        if not post:
            g.pure_files.append(filepath)
        elif not post.date:
            g.pure_pages.append(post)
        elif post.public:
            g.public_posts.append(post)
        else:
            g.secure_posts.append(post)

    g.public_posts = sorted(g.public_posts, key=lambda o: o.date, reverse=True)
    g.secure_posts = sorted(g.secure_posts, key=lambda o: o.date, reverse=True)

    logging.info('Load Posts Finished')


def write_posts():
    writers = []
    for name in settings.writer.get('active'):
        writers.append(import_object(name)())

    load_jinja()

    for writer in writers:
        writer.run()


def build(config=None):
    load_settings(config)
    load_posts(settings.config.get('source'))
    write_posts()
