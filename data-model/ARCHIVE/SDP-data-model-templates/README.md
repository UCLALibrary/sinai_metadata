# Data Model Templates for the Sinai Data portal

The files in this directory represent the data model for the Sinai Data Portal in a semi-abstract way. Thse JSON documents show the available keys and their corresponding data types and value restrictions for each entity (authority file or object) in the Sinai Data Portal. Moreover, the inclusion of the "entity", "authority-file", and "object" templates demonstrates the inheritance hierarchies and shared fields among the different record types. Below is a summary of the inheritance relationships:

## Inheritance Relationships in the Sinai Data Portal

- `entity`
  - `authority-file`
    - `person`
    - `place`
    - `work`
  - `object`
    - `manuscript-object`
    - `codicological-unit`
    - `textual-artifact`

The fields available at higher levels in the inheritance are also available to the 'child' record types; however, these 'children' have additional fields available to them based on their more specialized needs.
