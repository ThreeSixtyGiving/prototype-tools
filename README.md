# Open Philanthropy Standard Tools

This folder will contain tools for generating the various Open Philanthropy standard templates and validators, and converting between Open Philanthropy serialisations. 

## One standard, multiple representations

The Open Philanthropy RDF Schema will authoritatively define the data model.

This will be used to generate:

* A JSON-LD Schema
* A set of CSV templates

It will also provide all the details required for translation of:

* CSV to JSON data
* JSON to CSV
* JSON to Linked Data

## The theory

### Restrictions on the ontology

There should be a one-to-one relationship between ObjectProperties and a specific SubClass. 

For example, the property recipientOrganization should point to a class of RecipientOrganization as a subclass of Organization

## Work so far

### rdf-to-tables.py

This will take the Draft Ontology and generate an Excel spreadsheet consisting of a number of sheets: one sheet for each top-level class in the ontology (in practice, those under the ontologies own 'Thing' class) related to the primary subject of the dataset. 

Essentially this is one sheet for each kind of thing the dataset can describe. By default, each sheet will contain:

* All the data properties of that thing
* A 'type' column for determining what subClass of the class is being described. 
** E.g. an ActivityType column into which might be recorded 'Grant', 'Loan' or 'Social Investment'
* A column for the ids of each class of thing that rows on the sheet may relate to
** E.g. A classification can be applied to Activities (grants etc.), Transactions, and Organizations, and so the Classifications sheet will include a Activity ID, Organization ID and Transaction ID columns, to be used selectively as appropriate.

By default, an object property (e.g. fundingOrganization) would be represented in the table by providing an entry in the Organization table, entering the related Activity ID, and setting the Organization type as 'Funding Organization'. 

However: there are two special properties of ObjectProperty relationships designed to make entering data more intuitive for users, and to make it possible for one-to-one relationships to be recorded on a single sheet.

#### RollUp

The 'rollUp' property is used to include in a sheet selected DataProperties of a related Class (related by an ObjectProperty). 

For example, in our data model, address information for a Funding or Recipient Organization would normally be provided in the 'Organizations' sheet, rather than the 'Activities' sheet. However, this requires a user to flip between different sheets, and maintain the integrity of references, which isn't very intuitive for a user wanting to enter a simple record about their grantmaking. 

So: we allow fields from Organization to be included in the 'Activities' sheet.

This has the limitation of only allowing a one-to-one relationship to be expressed, but this serves many use-cases, and users can switch to entering more details in the other sheets if they need to. 

**ToDo**: Provide a much clearer explanation of this

#### TotalUp

The 'totalUp' property is used to allow expression of aggregate financial figures, which might be otherwise specified in the transactions sheet.

A logic concerning the use of currency needs to be written up for this.
