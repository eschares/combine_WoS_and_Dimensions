# combine_WoS_and_Dimensions
This script takes in a Web of Science export and a Dimensions export file, then combines them

# Problem
Analyzing metadata on scholarly outputs often requires a data export from one or more bibliographic databases. 

Each has their own pros and cons.

### Web of Science
Includes a critical data point (Corresponding Author, or in Web of Science terms, Reprint Author), but excludes entire journals through its indexing criteria.

Good data, but by definition, incomplete

### Dimensions
Indexes much more widely and includes records from many more journals than Web of Science, but does not provide the critical Corresponding Author data in each record

More records, but each record has less data

# This Project

This project attempts to combine the strengths of both these databases and arrive at a more complete picture of output (typically from an institution and/or with a specific publisher)

## Export

From Web of Science, select

From Dimensions, select

Flow is:
- Read in Web of Science export
