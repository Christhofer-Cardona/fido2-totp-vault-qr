# Contributing

Issues and pull requests for offline QR import are welcome. Please include
the platform, Python version, expected result, and actual result. Use only
synthetic test QR codes; never attach real enrollment images or seeds. Send
security concerns through the private route in [SECURITY.md](SECURITY.md).

Install the project in a virtual environment with `python -m pip install -e .`
and run `python -m unittest discover -s tests -v` before a pull request.
