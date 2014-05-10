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
g.load('ontology/360Giving.v0.2.rdf')

def getName(uriRef):
    return str(uriRef).rpartition("/")[2] # Get last part of the URL (assumes slash based URLs)

# Put together the basics of a field specification
def createFieldSpec(dataProperty):
    fieldSpec = {}
    fieldSpec['name'] = getName(dataProperty)
    try:
        fieldSpec['title'] = str(g.preferredLabel(dataProperty,defaultLanguage)[0][1])
    except:
        fieldSpec['title'] = "LABEL MISSING"
    
    fieldSpec['description'] = str(g.value(dataProperty,RDFS.comment,default="-"))
    
    fieldSpec['weight'] = float(g.value(dataProperty,OPDS.fieldWeight,default=5))
    
    if ((dataProperty, RDFS.range, RDFS.Literal)) in g:
        fieldSpec['values'] = 'Text'
    elif ((dataProperty, RDFS.range, XSD.dateTime)) in g:
        fieldSpec['values'] = 'DateTime'
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
        if(subjectOrParent == OWL.Thing): # Updated to OWL.Thing in updated model (was ODPS.Thing)
            break #When we get to 'Thing' we want to go no further.
        tableName = g.preferredLabel(subjectOrParent,defaultLanguage)
        tableEntity = subjectOrParent
    tableName = str(tableName[0][1]) # [0][1] syntax needed to fetch value from list and tuple container
    
    return (tableEntity, tableName)

#Loop through all the available defaultSubjects
# 

def generateModel(subjectEntity, depth, output = {},rollUps = True):
    subjectEntity = URIRef(subjectEntity) 

    topTable = getTopClass(subjectEntity)
    tableName = topTable[1]

    ## 2. Set up a new table for us
    if tableName in output.keys():
        pass
    else:
        output[tableName] = {}
        output[tableName]['_meta'] = {"description":g.value(topTable[0],RDFS.comment,default=""),"types":[],"relationships":[],"related":{}}

    ## Add the current subject entity to the types this table can take
    if getName(subjectEntity) not in output[tableName]['_meta']['types']:
        output[tableName]['_meta']['types'].append(getName(subjectEntity))
    
    ## Identify any relationships this table can stand in
    for relationship in g.subjects(predicate=RDFS.range,object=subjectEntity):
        if getName(relationship) not in output[tableName]['_meta']['relationships']:
            output[tableName]['_meta']['relationships'].append(getName(relationship))
            
    # 3. Work through all the classes up the tree to be sure we're able to express all the properties we need to
    for subjectOrParent in g.transitive_objects(subjectEntity,RDFS.subClassOf): 
        if(depth > 1):
            for relationship in g.subjects(predicate=RDFS.range,object=subjectOrParent):   
                for domain in g.objects(relationship,RDFS.domain):                  
                    topTable = getTopClass(domain)[1]
                    if(not(topTable == tableName)): # Handle for recursive relationships (e.g. Related Activity)
                        fieldSpec = {}
                        fieldSpec['name'] = topTable + ".id"
                        fieldSpec['title'] = topTable + " ID"
                        fieldSpec['values'] = "Reference"
                        fieldSpec['description'] = "The identifier of a related " + topTable + " (optional)"
                        fieldSpec['weight'] = 0.5
                        output[tableName][fieldSpec['name']] = fieldSpec
                
                        fieldSpec = {}
                        # fieldSpec['name'] = tableName.lower()+"Type"
                        # fieldSpec['title'] = tableName +" Type"
                        fieldSpec['name'] = "relationshipType"
                        fieldSpec['title'] = "Relationship Type"
                        fieldSpec['values'] = "Reference"
                        fieldSpec['description'] = "One of: " + ", ".join(output[tableName]['_meta']['relationships'])
                        fieldSpec['weight'] = float(0.55)
                        output[tableName][tableName.lower()+"Type"] = fieldSpec
                
                        output[tableName][tableName.lower()+"Type"] = fieldSpec
            
        for dataProperty in g.subjects(predicate=RDFS.domain,object=subjectOrParent):
            #Set up the field specification
            fieldSpec = createFieldSpec(dataProperty)
                
            #If we're dealing with an entity process that here:
            if(not(fieldSpec['values'] == 'Entity')):
                output[tableName][fieldSpec['name']] = fieldSpec
            else:         
                
                # Roll Ups
                if(rollUps == True):
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
                    
                    
                    #Add some extra information for the documentation output
                    output[tableName]['_meta']['related'][getName(dataProperty)] = {"relationshipName":getName(dataProperty), "objectName":getName(subObject), "topObject":getTopClass(subObject)[1], "description":g.value(dataProperty,RDFS.comment,default="-"), "title":g.value(dataProperty,RDFS.label,default="-")}
                    
                    if depth < 2:                            
                        subObjectModel = generateModel(subObject,depth+1,output,rollUps)
                        subObjectType = subObjectModel.keys()[0]
                        
                    else:
                        pass
                   
                    

    # Sort        
    #output[tableName].sort(key=lambda field: field['weight'])
    return output