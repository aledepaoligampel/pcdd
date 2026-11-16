# pcdd

Progressive Change-Driven Development for AI coding agents: each change gets just enough process.

PCDD is a Python package on [PyPI](https://pypi.org/project/pcdd/). This npm package is a small launcher that runs it through [uv](https://docs.astral.sh/uv/):

```sh
npx pcdd init        # same as: uvx pcdd@<this package's version> init
```

Each npm release runs the PyPI release with the same version, so `npx pcdd@0.4.0` always runs PCDD 0.4.0. Arguments and the exit code are passed through unchanged. uv must be installed; if it is missing, the launcher explains how to install it.

To install PCDD permanently instead:

```sh
curl -fsSL https://pcdd.dev/install.sh | sh
```

Documentation: [pcdd.dev](https://pcdd.dev) · Source: [github.com/aledepaoligampel/pcdd](https://github.com/aledepaoligampel/pcdd) · License: MIT
