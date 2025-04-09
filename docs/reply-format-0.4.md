# Licomp Toolkit - Reply Format

The previous format (0.3) was for checking a license against a
license, e.g. can I use outbound license when using a component under
inbound license given a specific context.

This format extends to looking at expressions (e.g. `MIT OR BSD-3-Clause`) instead. This new format will be much more complex so we will define sub formats, which will be used by the top format.

## Licomp Toolkit - Request Information Format

This is only a compilation of the request as received from the user.

{
  "outbound": "GPL-2.0-only",
  "inbound": "MIT",
  "usecase": "library",
  "provisioning": "binary-distribution",
  "modification": "unmodified"
}

## Licomp Toolkit - License -> Expression Format

## Licomp Toolkit - Expression -> Expression Format

## Licomp Toolkit - Summary Format

# Example output (version 0.4)

