import rdflib
from rdflib import URIRef, Literal
from rdflib import RDFS, OWL, XSD
import operator # Used in sorting
from sets import Set


# Defaults 
defaultLanguage = 'en'

# Set up the graph
g=rdflib.Graph()
OPDS = rdflib.Namespace('http://joinedupdata.org/ontologies/philanthropy/')
g.namespace_manager.bind('opds', URIRef('http://joinedupdata.org/ontologies/philanthropy/'))

#Load the data
g.load('DraftOntology0.1.rdf')

def getName(uriRef):
    return str(uriRef).rpartition("/")[2] # Get last part of the URL (assumes slash based URLs)

# Put together the basics of a field specification
def createFieldSpec(dataProperty):
    fieldSpec = {}
    fieldSpec['name'] = getName(dataProperty)
    try:
        fieldSpec['title'] = str(g.preferredLabel(dataProperty,"en")[0][1])
    except:
        fieldSpec['title'] = "LABEL MISSING"
    
    fieldSpec['weight'] = float(g.value(dataProperty,OPDS.fieldWeight,default=5))
    
    if ((dataProperty, RDFS.range, RDFS.Literal)) in g:
        fieldSpec['values'] = 'Text'
    elif ((dataProperty, RDFS.range, XSD.dateTime)) in g:
        fieldSpec['values'] = 'DataTime'
    elif ((dataProperty, RDFS.range, XSD.float)) in g:
        fieldSpec['values'] = 'Number (float)'
    elif ((dataProperty, RDFS.range, XSD.integer)) in g:
        fieldSpec['values'] = 'Number (integer)'
    elif ((dataProperty, RDFS.range, XSD.boolean)) in g:
        fieldSpec['values'] = 'Yes/No'
    else:
        fieldSpec['entity'] = g.value(dataProperty, RDFS.range)
        fieldSpec['values'] = 'Entity'

    
    return fieldSpec
    

def getTopClass(entity):
    for subjectOrParent in g.transitive_objects(entity,RDFS.subClassOf):
        if(subjectOrParent == OPDS.Thing):
            break #When we get to 'Thing' we want to go no further.
        tableName = g.preferredLabel(subjectOrParent,"en")
    tableName = str(tableName[0][1]) # [0][1] syntax needed to fetch value from list and tuple container
    
    return tableName

#Loop through all the available defaultSubjects
def generateModel(subjectEntity, depth, output = {}):
    subjectEntity = URIRef(subjectEntity) 
    print subjectEntity
    tableName = getTopClass(subjectEntity)

    ## 2. Set up a new table for us
    if tableName in output.keys():
        pass
    else:
        output[tableName] = {}

    # 3. Work through all the classes up the tree to be sure we're able to express all the properties we need to
    for subjectOrParent in g.transitive_objects(subjectEntity,RDFS.subClassOf): 
        if(depth > 1):
            for relationship in g.subjects(predicate=RDFS.range,object=subjectOrParent):   
                topTable = getTopClass(g.value(relationship,RDFS.domain))
                if(not(topTable == tableName)): # Handle for recursive relationships (e.g. Related Activity)
                    fieldSpec = {}
                    fieldSpec['name'] = topTable + ".id"
                    fieldSpec['title'] = topTable + " ID"
                    fieldSpec['values'] = "Reference"
                    fieldSpec['weight'] = 0.5
                    output[tableName][fieldSpec['name']] = fieldSpec
                
                
                
                    fieldSpec = {}
                    fieldSpec['name'] = tableName.lower()+"Type"
                    fieldSpec['title'] = tableName +" Type"
                    fieldSpec['weight'] = float(0)
                    output[tableName][tableName.lower()+"Type"] = fieldSpec

                    # ToDo: Fix this - not working right now (should help us generate a list of valid values for each Type column)
                    try:
                        output[tableName][tableName.lower()+"Type"]['values'].update([getName(relationship)])
                    except Exception as e:
                        output[tableName][tableName.lower()+"Type"]['values'] = Set([getName(relationship)])
                        pass
                
                    output[tableName][tableName.lower()+"Type"] = fieldSpec
            
        for dataProperty in g.subjects(predicate=RDFS.domain,object=subjectOrParent):
            #Set up the field specification
            fieldSpec = createFieldSpec(dataProperty)
                
            #If we're dealing with an entity process that here:
            if(not(fieldSpec['values'] == 'Entity')):
                output[tableName][fieldSpec['name']] = fieldSpec
            else:         
                
                # Roll Ups
                for rollUp in g.objects(subject=dataProperty,predicate=OPDS.rollUp):  
                    fieldSpec = createFieldSpec(rollUp) # Set up a field specification, then overwrite what we need to
                    fieldSpec['name'] = getName(dataProperty) + "." + fieldSpec['name']
                    fieldSpec['title'] = str(g.preferredLabel(dataProperty,"en")[0][1]) + ":" + fieldSpec['title']
                    fieldSpec['weight'] = float(str(float(g.value(dataProperty,OPDS.fieldWeight,default=0.0))) + str(fieldSpec['weight']).replace('.',''))
                    output[tableName][fieldSpec['name']] = fieldSpec
                
                # Total Ups
                for totalUp in g.objects(subject=dataProperty,predicate=OPDS.totalUp):  
                    fieldSpec = createFieldSpec(dataProperty) # Set up a field specification, then overwrite what we need to
                    fieldSpec['name'] = "sum("+fieldSpec['name']+ ")"
                    fieldSpec['title'] = "Total " + fieldSpec['title'] #Needs I8LN
                    fieldSpec['weight'] = float(str(float(g.value(dataProperty,OPDS.fieldWeight,default=0.0))) + str(fieldSpec['weight']).replace('.',''))
                        
                    output[tableName][fieldSpec['name']] = fieldSpec
                
                # For related objects
                for subObject in g.objects(subject=dataProperty,predicate=RDFS.range):  
                    if depth < 2:
                        subObjectModel = generateModel(subObject,depth+1,output)
                        subObjectType = subObjectModel.keys()[0]
                    else:
                        pass
                    

    # Sort        
    #output[tableName].sort(key=lambda field: field['weight'])
    return output