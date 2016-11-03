#!/usr/bin/env python3
"""A program (bot) for rendering short snippets of LaTeX code as an image.
A LaTeX distribution needs to be installed on the machine where this code
is ran."""

import sys
from io import BytesIO
from tempfile import NamedTemporaryFile
from os.path import basename
import re

from sympy import preview
from flask import Flask, request, abort, send_file, make_response

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
    if 'mode' in request.args:
        mode = request.args['mode']
    else:
        mode = app.config['OUTPUT_MODE']

    if 'render' not in request.args:
        return make_response('The input to render was not provided. Use the '
                             '"render" query argument.', 404)

    # Hack to generate a temporary filename
    with NamedTemporaryFile(dir='/tmp', prefix='latexbot_', suffix='.png', delete=True) as tmpfile:
        tmpfile_name = tmpfile.name

    if mode == 'link':
        if not render(request.args['render'], mode, image_name=tmpfile_name):
            return make_response('Internal server error, please check input validity', 500)

        return '{}{}image/{}'.format(request.url_root,
                                     '{}/'.format(app.config['EXTRA_URL_PATH'])
                                     if app.config['EXTRA_URL_PATH'] != '' else '',
                                     re.search(r'latexbot_(\w+)\.png',
                                               basename(tmpfile_name)).group(1))
    else:
        out_buffer = BytesIO()
        if not render(request.args['render'], mode, output_buffer=out_buffer):
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


if __name__ == '__main__':
    app.run(host='0.0.0.0')
