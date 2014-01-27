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
g.load('DraftOntology0.1.rdf')

#Loop through all the available defaultSubjects
def generateModel(subjectEntity):
    output = {}
    # Check if subject exists
    # subjectLabel = str(list(g.preferredLabel(defaultEntity,lang=defaultLanguage,default='root'))[0][1]) 
    subject = getName(subjectEntity)

    output[subject] = {}

    # Work through all the parent classes
    for subjectOrParent in g.transitive_objects(subjectEntity,RDFS.subClassOf):
   
        for dataProperty in g.subjects(predicate=RDFS.domain,object=subjectOrParent):
            ## If the range is a literal, then we add a data property placeholder
            if (dataProperty, RDFS.range, RDFS.Literal) in g: 
                output[subject].update({getName(dataProperty):''})
            ## else we assume the range is an object (we may need to handle for more types of range, such as integer here in future)
            else: 
                for subObject in g.objects(subject=dataProperty,predicate=RDFS.range):  
                    # In the long-run we want to alter the output we get here
                    # Removing the intermediate Objects, and turning objects into arrays
                    output[subject].update({getName(dataProperty): generateModel(subObject)})
                    pass

    return output          

for defaultEntity in g.subjects(predicate=OPDS.defaultSubject):
    model = generateModel(defaultEntity)
    
# output = {}
# output = generateModel(URIRef('http://joinedupdata.org/ontologies/philanthropy/Organization'))

print json.dumps(model)

# 1. Look for the defaultSubject
# - Create an object for it
# 2. Look for all it's dataProperties
# 3. Look for all it's objectProperties