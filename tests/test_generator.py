#!/usr/bin/env python

import os.path
from liquidluck.generator import load_settings, load_posts
from liquidluck.generator import parse_settings

ROOT = os.path.abspath(os.path.dirname(__file__))


def test_load_settings():
    path = os.path.join(ROOT, 'source/settings.py')
    load_settings(path)

    from liquidluck.options import settings
    assert settings.author['default'] == 'lepture'


def test_load_posts():
    load_posts(os.path.join(ROOT, 'source/post'))
    from liquidluck.options import g
    assert len(g.public_posts) > 0


def test_parse_settings():
    path = os.path.join(ROOT, 'source/settings.py')
    config = parse_settings(path)
    assert config['author'] == {'default': 'lepture'}

    path = os.path.join(ROOT, 'source/package.json')
    config = parse_settings(path)
    assert config['name'] == 'json'

    path = os.path.join(ROOT, 'source/package.yml')
    config = parse_settings(path)
    assert config['name'] == 'yaml'
