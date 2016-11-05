#!/usr/bin/env python3
"""A program (bot) for rendering short snippets of LaTeX code as an image.
A LaTeX distribution needs to be installed on the machine where this code
is ran."""

import sys
from io import BytesIO
from tempfile import NamedTemporaryFile
from os.path import basename
from os import remove
from shlex import split
from glob import glob
import re

import subprocess

from sympy import preview
from jinja2 import Environment, PackageLoader
from flask import Flask, request, abort, send_file, make_response, render_template

# pylint: disable=invalid-name
app = Flask(__name__)
app.config.from_pyfile('latexbot.cfg')


def render(latex_source, mode, image_name=None, output_buffer=None):
    """Renders the given LaTeX source and outputs it in a PNG image
    with the given name. Returns True on success and False otherwise."""
    try:
        if mode == 'link':
            preview(latex_source, euler=False, viewer='file', filename=image_name)
        else:
            preview(latex_source, euler=False, output='png', viewer='BytesIO',
                    outputbuffer=output_buffer)
    except RuntimeError as err:
        print('Got a Latex error: {}'.format(err), file=sys.stderr)
        return False
    return True


# Routes
@app.route('/', methods=['GET'])
def index():
    """Index route."""
    return render_template('index.html')


@app.route('/render/<latex_input>', methods=['GET'])
def render_url_input(latex_input):
    """Render the provided LaTeX input."""
    if 'mode' in request.args:
        mode = request.args['mode']
    else:
        mode = app.config['OUTPUT_MODE']

    # Hack to generate a temporary filename
    with NamedTemporaryFile(dir='/tmp', prefix='latexbot_', suffix='.png', delete=True) as tmpfile:
        tmpfile_name = tmpfile.name

    if mode == 'link':
        if not render(latex_input, mode, image_name=tmpfile_name):
            return make_response('Internal server error, please check input validity', 500)

        return '{}{}image/{}'.format(request.url_root,
                                     '{}/'.format(app.config['EXTRA_URL_PATH'])
                                     if app.config['EXTRA_URL_PATH'] != '' else '',
                                     re.search(r'latexbot_(\w+)\.png',
                                               basename(tmpfile_name)).group(1))
    else:
        out_buffer = BytesIO()
        if not render(latex_input, mode, output_buffer=out_buffer):
            return make_response('Internal server error, please check input validity', 500)

        out_buffer.seek(0)
        return send_file(out_buffer, mimetype='image/png')


@app.route('/image/<image_id>', methods=['GET'])
def get_image(image_id):
    """Returns the image referred by the given ID."""
    try:
        image = open('/tmp/latexbot_{}.png'.format(image_id), 'rb')
    except FileNotFoundError:
        print('Tried to access non-existent image: {}'.format(image_id),
              file=sys.stderr)
        abort(404)
    return send_file(image, mimetype='image/png')


@app.route('/input', methods=['GET'])
def input_form():
    """Render an input form."""
    return render_template('input.html')


@app.route('/input', methods=['POST'])
def render_from_form():
    """Render LaTeX from the input form."""
    env = Environment(loader=PackageLoader('latexbot', 'templates'))
    template = env.get_template('template.tex')
    #  pylint: disable=no-member
    rendered_template = template.render(latex_input=request.form['latex-input'])

    with NamedTemporaryFile(dir='/tmp', prefix='latexbot_', suffix='.tex',
                            delete=True) as tmpfile:
        tmpfile_name = tmpfile.name

    with open(tmpfile_name, 'w') as tmpfile:
        tmpfile.write(rendered_template)

    rc = subprocess.call(['latex', '-interaction=nonstopmode', '-output-directory=/tmp',
                          tmpfile_name])
    if rc != 0:
        # Render failed
        for f in glob(tmpfile_name.replace('tex', '*')):
            remove(f)
        return make_response('Internal server error: LaTeX rendering failed. '
                             'Please check input validity.', 500)

    rc = subprocess.call(split('dvipng -T tight -D 150 -z 9 {} -o {}'.
                               format(tmpfile_name.replace('.tex', '.dvi'),
                                      tmpfile_name.replace('.tex', '.png'))))
    if rc != 0:
        # DVI to PNG conversion failed
        for f in glob(tmpfile_name.replace('tex', '*')):
            remove(f)
        return make_response('Internal server error: image conversion failed.', 500)

    # Remove auxiliary files generated during render
    for f in glob(tmpfile_name.replace('tex', '*')):
        if not f.endswith('png'):
            remove(f)

    if request.form['output'] == 'link':
        return '{}{}image/{}'.format(request.url_root,
                                     '{}/'.format(app.config['EXTRA_URL_PATH'])
                                     if app.config['EXTRA_URL_PATH'] != '' else '',
                                     re.search(r'latexbot_(\w+)\.tex',
                                               basename(tmpfile_name)).group(1))
    else:
        return send_file(open(tmpfile_name.replace('.tex', '.png'), 'rb'),
                         mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
