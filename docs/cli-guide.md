# Licomp Toolkit - Command Line Guide

Before you start using `licomp-toolkit` we suggest you read:
* [Licomp reply format](https://github.com/hesa/licomp/#licomp-basic-concepts)
* [Licomp reply format](https://github.com/hesa/licomp/#licomp-reply-format)

# Defaults

`licomp-toolkit` by default uses:
* usecase `library`- i.e. the licenses component is used as a library (e.g. linking to it)
* provisioning `binary-distribution`
* modification is not yet implemented

You can change this using corresponding options (see below).

# Commands

## supported-licenses

List of the supported licenses. This list contains all the supported licenses from each Licomp resource.

_Note: A license is listed even if it is not supported in both compatiblity directions with another license._

## supported-usecases

Lists the usecases from the available Licomp resources. This may not be the complete list of usecases as found in [Licomp](https://github.com/hesa/licomp#licomp-concepts-usecase).

Example:

```
$ licomp-toolkit supported-usecases
['snippet', 'library']
```

## supported-provisionings

Lists the provisionings from the available Licomp resources. This may not be the complete list of provisionings as found in [Licomp](https://github.com/hesa/licomp#licomp-concepts-provisioning).

Example:
```
$ licomp-toolkit supported-provisionings
['binary-distribution', 'local-use', 'source-code-distribution']
```

## supported-resources

Lists the available Licomp resources, including version seprated with a comma, (i.e. the compatibility resources used to provide answers to your questions). 

Example:
```
$ licomp-toolkit supported-resources
['licomp_reclicense:0.3.0', 'licomp_osadl:0.3.0', 'licomp_hermione:0.3.0', 'licomp_proprietary:0.3.0', 'licomp_dwheeler:0.3.1']
```


### Verify

Returns the compatibility status for the supplied outbound and inbound license. The reply, by default, is in the format as specified in [Licomp Toolkit - Reply Format](reply-format.md).

Syntax:
```
licomp-toolkit verify [-h] [--outbound-license OUT_LICENSE] [--inbound-license IN_LICENSE]
```

Example (omitting the reply):
```
$ licomp-toolkit verify -ol GPL-2.0-or-later -il BSD-3-Clause
```

`