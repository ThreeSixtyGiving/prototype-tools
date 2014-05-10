# This script generates an intermediate representation of the data model ready for translation into CSV
import json
import operator # Used in sorting
from sets import Set
from genmodel import generateModel, getName

# Change final parameter to False / True depending on whether you want roll-ups or not.
model = generateModel("http://joinedupdata.org/ontologies/philanthropy/Grant",1,{},True)

print json.dumps(model)