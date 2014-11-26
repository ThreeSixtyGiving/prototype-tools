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
g.load('../ontology/360Giving.v0.2.rdf')

## Get top class
def getTopClassFromPropery(dataProperty):
    for entity in g.objects(subject=dataProperty,predicate=RDFS.range):
        for subjectOrParent in g.transitive_objects(entity,RDFS.subClassOf):
            if(subjectOrParent == OWL.Thing): # Updated to OWL.Thing in updated model (was ODPS.Thing)
                break #When we get to 'Thing' we want to go no further.
            tableName = g.preferredLabel(subjectOrParent,defaultLanguage)
            tableEntity = subjectOrParent
    if(tableName):
        tableName = str(tableName[0][1]) # [0][1] syntax needed to fetch value from list and tuple container
        return (tableEntity, tableName)
    else:
        return "Not_Sure_What_Is_Going_On_Here"

## Check fieldType
def fieldType(dataProperty):
    fieldType = {}

    if ((dataProperty, RDFS.range, RDFS.Literal)) in g:
        fieldType = 'string'##
    elif ((dataProperty, RDFS.range, XSD.dateTime)) in g:
        fieldType = 'string'
    elif ((dataProperty, RDFS.range, XSD.float)) in g:
        fieldType = 'number'
    elif ((dataProperty, RDFS.range, XSD.integer)) in g:
        fieldType = 'integer'
    elif ((dataProperty, RDFS.range, XSD.boolean)) in g:
        fieldType = 'boolean'
    else:
        fieldType = 'object'
    return fieldType

#Loop through all the available defaultSubjects
def generateModel(subjectEntity, depth, parent = ""):
    
    output = {}
    # Check if subject exists
    # subjectLabel = str(list(g.preferredLabel(defaultEntity,lang=defaultLanguage,default='root'))[0][1]) 
    subject = getName(subjectEntity)

    output['properties'] = {}
    output['definitions'] = {}
    
    if(depth > 1):
        output['type'] = 'object'
    
    # Work through all the parent classes
    for subjectOrParent in g.transitive_objects(subjectEntity,RDFS.subClassOf):
   
        for dataProperty in g.subjects(predicate=RDFS.domain,object=subjectOrParent):
            ## If the range is a literal, then we add a data property placeholder
            if ((dataProperty, RDFS.range, RDFS.Literal)) in g:
                output['properties'].update({getName(dataProperty):{
                    "title":str(g.preferredLabel(dataProperty,defaultLanguage)[0][1]),
                    "description":str(g.value(dataProperty,RDFS.comment,default="-")),
                    "type":fieldType(dataProperty),
                    "weight":float(g.value(dataProperty,OPDS.fieldWeight,default=5))
                    }})
           ## If the range is a dateTime handle that here
            elif ((dataProperty, RDFS.range, XSD.dateTime)) in g:
                output['properties'].update({getName(dataProperty):{
                    "title":str(g.preferredLabel(dataProperty,defaultLanguage)[0][1]),
                    "description":str(g.value(dataProperty,RDFS.comment,default="-")),
                    "type":fieldType(dataProperty),
                    "weight":float(g.value(dataProperty,OPDS.fieldWeight,default=5)),
                    "format":"date-time"
                    }})
            ## else we assume the range is an object (we may need to handle for more types of range, such as integer here in future)
            else: 
                for subObject in g.objects(subject=dataProperty,predicate=RDFS.range):  
                    # We want to avoid deep nesting, so whenever we get more levels deep we should use an indentifier 
                    if depth < 2:
                        output['properties'].update({getName(dataProperty):{
                            "title":str(g.preferredLabel(dataProperty,defaultLanguage)[0][1]),
                            "description":str(g.value(dataProperty,RDFS.comment,default="-")),
                            "type":"array",
                            "weight":float(g.value(dataProperty,OPDS.fieldWeight,default=5)),
                            "items": {
                                "$ref":"#/definitions/"+getTopClassFromPropery(dataProperty)[1]
                            }
                            }})
                        output['definitions'].update({getTopClassFromPropery(dataProperty)[1]: generateModel(subObject,depth+1,subject)})
                    else:
                        ## Let's assume that everything that can be a ref one level down, has already been set-up by a higher level... 
                        ## this may not be a great assumption - but we'll run with it for now

                        output['properties'].update({getName(dataProperty):{
                            "title":str(g.preferredLabel(dataProperty,defaultLanguage)[0][1]),
                            "description":str(g.value(dataProperty,RDFS.comment,default="-")),
                            "type":"array",
                            "weight":float(g.value(dataProperty,OPDS.fieldWeight,default=5)),
                            "items": {
                                "$ref":"#/definitions/"+getTopClassFromPropery(dataProperty)[1]
                            }
                            }})
                    pass
    if(depth > 1):
        return output
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