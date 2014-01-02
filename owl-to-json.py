import rdflib
from rdflib import URIRef, Literal
from rdflib import RDFS, OWL
import json

def getName(uriRef):
    return str(uriRef).rpartition("/")[2] # Get last part of the URL (assumes slash based URLs)

# Defaults 
defaultLanguage = 'en'

# Set up the graph
g=rdflib.Graph()
OPDS = rdflib.Namespace('http://joinedupdata.org/ontologies/philanthropy/')
g.namespace_manager.bind('opds', URIRef('http://joinedupdata.org/ontologies/philanthropy/'))

#Load the data
g.load('../Ontologies/DraftOntology0.1.rdf')

# Set up output
output = {}

#Loop through all the available defaultSubjects

for defaultEntity in g.subjects(predicate=OPDS.defaultSubject):
    subjectLabel = str(list(g.preferredLabel(defaultEntity,lang=defaultLanguage,default='root'))[0][1]) 
    subject = getName(defaultEntity)
    
    output[subject] = {}
    
    # Work through all the parent classes
    for subjectOrParent in g.transitive_objects(defaultEntity,RDFS.subClassOf):
        for dataProperty in g.subjects(predicate=RDFS.domain,object=subjectOrParent):
            ## If the range is a literal, then we add a data property placeholder
            if (dataProperty, RDFS.range, RDFS.Literal) in g: 
                output[subject].update({getName(dataProperty):''})
            ## else we assume the range is an object (we may need to handle for more types of range, such as integer here in future)
            else: 
                pass
                

    


print json.dumps(output)

# 1. Look for the defaultSubject
# - Create an object for it
# 2. Look for all it's dataProperties
# 3. Look for all it's objectProperties