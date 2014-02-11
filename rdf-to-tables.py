# This script generates an intermediate representation of the data model ready for translation into CSV
import rdflib
from rdflib import URIRef, Literal
from rdflib import RDFS, OWL, XSD
import json
import xlwt
import operator # Used in sorting

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
                fieldSpec = {}
                fieldSpec['name'] = topTable + ".id"
                fieldSpec['title'] = topTable + " ID"
                fieldSpec['value'] = "Reference"
                fieldSpec['weight'] = 0.5
                output[tableName][fieldSpec['name']] = fieldSpec
                
                fieldSpec = {}
                fieldSpec['name'] = tableName.lower()+"Type"
                fieldSpec['title'] = tableName +" Type"
                fieldSpec['weight'] = float(0)
                try:
                    #ToDo - fix the way this works
                    fieldSpec['values'] = output[tableName][fieldSpec['name']]['values'] + ", " + getName(relationship)
                except:
                    fieldSpec['values'] = getName(relationship)
                output[tableName][fieldSpec['name']] = fieldSpec
            
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
                    fieldSpec['weight'] = float(str(fieldSpec['weight']) + str(g.value(rollUp,OPDS.fieldWeight,default=5)).replace('.',''))
                    output[tableName][fieldSpec['name']] = fieldSpec
                
                # Total Ups
                for totalUp in g.objects(subject=dataProperty,predicate=OPDS.totalUp):  
                    fieldSpec = createFieldSpec(dataProperty) # Set up a field specification, then overwrite what we need to
                    fieldSpec['name'] = "sum("+fieldSpec['name']+ ")"
                    fieldSpec['title'] = "Total " + fieldSpec['title'] #Needs I8LN
                    fieldSpec['weight'] = float(str(fieldSpec['weight']) + str(g.value(totalUp,OPDS.fieldWeight,default=5)).replace('.',''))
                        
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



for defaultEntity in g.subjects(predicate=OPDS.defaultSubject):
    model = generateModel(defaultEntity,1,{})



## Write it out to a spreadsheet
spreadsheet = xlwt.Workbook(encoding='ascii')

for table in sorted(model):
    sheet = spreadsheet.add_sheet(table)
    c = 0
    cols = []

    #Dictionary sorting work-around
    for col in model[table]:
        cols.append((col,model[table][col]["weight"]))
    cols = sorted(cols,key=lambda x: x[1])
    
    for col in cols:
        sheet.write(0,c,label=model[table][col[0]]['title'])
        sheet.write(1,c,label=model[table][col[0]]['name'])
        sheet.write(2,c,label=model[table][col[0]]['weight'])
        c = c + 1
spreadsheet.save("template.xls")



# 1. Look for the defaultSubject
# - Create an object for it
# 2. Look for all it's dataProperties
# 3. Look for all it's objectProperties