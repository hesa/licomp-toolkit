# Licomp Toolkit

Licomp toolkit is a license compatiblity tool using miscellaneous
available compatibility resources and provides replies based on all
resources.

Licomp toolkit uses the following compatibility resources using the [Licomp](https://github.com/hesa/licomp) api:
* [licomp-hermione](https://github.com/hesa/licomp-hermione)
* [licomp-osadl](https://github.com/hesa/licomp-osadl)
* [licomp-proprietary](https://github.com/hesa/licomp-proprietary)
* [licomp-reclicense](https://github.com/hesa/licomp-reclicense)
* [licomp-toolkit](https://github.com/hesa/licomp-toolkit)

# Using Licomp Toolkit

## Command line interface

If you want to check if the following is compatible:
* outbound license "MIT"
* inbound license "LGPL-2.0-or-later"

```
$ licomp-toolkit verify -il MIT -ol LGPL-2.0-or-later | jq .summary.results
{
  "nr_valid": "1",
  "yes": {
    "count": 1,
    "percent": 100.0
  }
}
```

## Python module

If you want to check if the following is compatible:
* outbound license "MIT"
* inbound license "LGPL-2.0-or-later"

```
>>> from licomp_toolkit.toolkit import LicompToolkit
>>> licomp_toolkit = LicompToolkit()
>>> compatibilities = licomp_toolkit.outbound_inbound_compatibility("MIT", "LGPL-2.0-or-later", "library", "binary-distribution")
>>> print(str(compatibilities['summary']['results']))
{'nr_valid': '1', 'yes': {'count': 1, 'percent': 100.0}}
```
