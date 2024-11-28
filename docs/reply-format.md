# Licomp Toolkit - Reply Format

# Example output (version 0.3)

_Note: Please note that in the example below only one of the compatibility results from the compatibility resources is listed (`licomp_reclicense`). This is to save space by removing multiple text segments being similar._

```
{
    "compatibilities": {
        "licomp_reclicense": {
            "status": "success",
            "status_details": {
                "provisioning_status": "success",
                "usecase_status": "success",
                "license_supported_status": "success"
            },
            "outbound": "MIT",
            "inbound": "MIT",
            "usecase": "library",
            "provisioning": "binary-distribution",
            "modification": "unmodified",
            "compatibility_status": "yes",
            "explanation": "Inbound and outbound license are the same: MIT",
            "api_version": "0.3",
            "resource_name": "licomp_reclicense",
            "resource_version": "0.3.0",
            "resource_disclaimer": "The data or the output of the tools in this repository come with guarantee"
        },
        // we have removed the output from some of the licomp resources here
    },
    "summary": {
        "resources": [
            "licomp_reclicense:0.3.0",
            "licomp_osadl:0.3.0",
            "licomp_hermione:0.3.0",
            "licomp_proprietary:0.3.0",
            "licomp_dwheeler:0.3.1"
        ],
        "outbound": "MIT",
        "inbound": "MIT",
        "usecase": "library",
        "provisioning": "binary-distribution",
        "statuses": {
            "success": [
                "licomp_reclicense",
                "licomp_hermione",
                "licomp_proprietary"
            ],
            "failure": [
                "licomp_osadl",
                "licomp_dwheeler"
            ]
        },
        "compatibility_statuses": {
            "yes": [
                "licomp_reclicense",
                "licomp_hermione",
                "licomp_proprietary"
            ]
        },
        "results": {
            "nr_valid": "3",
            "yes": {
                "count": 3,
                "percent": 100.0
            }
        }
    },
    "nr_licomp": 5,
    "meta": {
        "disclaimer": "This software and the data come with no gurantee. For more information read the disclaimers from the individual compatibility resources, and contact a lawyer to make sure your software is compliant."
    }
}


# Reply details

## compatibilities

Contains a map of replies from the available licomp resources. Each reply is in the [Licomp reply format](https://github.com/hesa/licomp/blob/main/docs/reply-format.md).

## summary

Contains a summary from the above replies (from the licomp resources).

### resources

A list of the licomp resources.

### Outbound

The supplied outbound license.

### Inbound

The supplied inbound license.

### Usecase

The supplied usecase.

### Provisioning

The supplied provisioning case.

### statuses

A map with the status (as key) and for each such a list of the licomp resources with that status.

* `success`- contains a list of the licomp resources where the request was successfully answered 
* failure- contains a list of the licomp resources where the request was not successfully answered 

### compatibility_statuses

A map with the compatibility status (as key) and for each such a list of the licomp resources with that compatibility status. If there are no licomp resources for a key, the key is not present.

Available compatibility statuses:
* `yes` 
* `no`
* `depends`
* `unknown`
* `unsupported`

_Note: The above compatiblity status depend on the supplied usecase, provisioning, modification (currently not implemeted, and discarded)_

### results

Containsthe number of valid replies (see below) and a map with a summary of the compatibility statuses.

The map with a summary of the compatibility statuses, where the compatibility status is the key, contains

* `count` - the number of such replies
* `percent` - how many percentages the count amounts to

#### nr_valid

Contains the number of successful replies.

### nr_licomp

The number of available licomp resources (regardless of whether the reply was successful or not).

### meta

Contains meta information about the reply.

### disclaimer

A disclaimer from Licomp Toolkit. 