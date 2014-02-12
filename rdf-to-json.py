import rdflib
from rdflib import URIRef, Literal
from rdflib import RDFS, OWL, XSD
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
def generateModel(subjectEntity, depth, parent = ""):
    
    output = {}
    # Check if subject exists
    # subjectLabel = str(list(g.preferredLabel(defaultEntity,lang=defaultLanguage,default='root'))[0][1]) 
    subject = getName(subjectEntity)

    output[subject] = {}

    # Work through all the parent classes
    for subjectOrParent in g.transitive_objects(subjectEntity,RDFS.subClassOf):
   
        for dataProperty in g.subjects(predicate=RDFS.domain,object=subjectOrParent):
            ## If the range is a literal, then we add a data property placeholder
            if ((dataProperty, RDFS.range, RDFS.Literal)) in g:
                output[subject].update({getName(dataProperty):''})
           ## If the range is a dateTime handle that here
            elif ((dataProperty, RDFS.range, XSD.dateTime)) in g:
                output[subject].update({getName(dataProperty):'YYYY-MM-DD'})
            ## else we assume the range is an object (we may need to handle for more types of range, such as integer here in future)
            else: 
                for subObject in g.objects(subject=dataProperty,predicate=RDFS.range):  
                    # We want to avoid deep nesting, so whenever we get more levels deep we should use an indentifier 
                    if depth < 2:
                        output[subject].update({getName(dataProperty): generateModel(subObject,depth+1,subject)})
                    else:
                        output[subject].update({getName(dataProperty): ''})
                    pass
    if(depth > 1):
        return output[subject]
    else:
        return output          

for defaultEntity in g.subjects(predicate=OPDS.defaultSubject):
    model = generateModel(defaultEntity,1)
    
# output = {}
# output = generateModel(URIRef('http://joinedupdata.org/ontologies/philanthropy/Organization'))

print json.dumps(model)

# 1. Look for the defaultSubject
# - Create an object for it
# 2. Look for all it's dataProperties
# 3. Look for all it's objectProperties