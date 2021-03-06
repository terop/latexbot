# latexbot

The latexbot is small Web application which renders the provided LaTeX source to
an image. Support for "one-line" and longer input is available. The output is
either the image itself or a link to the image containing rendered LaTeX source.
The output type can be specified in two ways:

* `OUTPUT_MODE` in `latexbot.cfg`, default value: image
* `mode` request argument, values: link or image
If `mode` is not provided, the value from `latexbot.cfg` is used.

Rendered images are written to `/tmp` and can be downloaded until `/tmp` is
flushed.

In cases where exceptions are caught, an entry of them is printed to `stderr`.

## Running
There are (at least) two ways to run this application:

* Using a Docker container. This way is not recommended as the image is big,
approximately 1.1 GB. The only benefit is that a LaTeX (Tex Live) distribution is
included in the image.
* Using a WSGI server. This is the preferred alternative. Basically any WSGI
compatible is okay. An example with the Gunicorn WSGI server:
`gunicorn --bind 0.0.0.0:5001 -w 2 latexbot:app`.
_Important_ note about _dependencies_: a LaTeX distribution with the `preview`
package needs to be available. On Debian this needs to be installed separately
from the `preview-latex-style` package. Regarding LaTeX distributions: Tex Live
2014 and later are known to work.

## License

See the MIT license in the LICENSE file.

Copyright © 2016 Tero Paloheimo
