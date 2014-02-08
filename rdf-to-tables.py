# This script generates an intermediate representation of the data model ready for translation into CSV
#



import rdflib
from rdflib import URIRef, Literal
from rdflib import RDFS, OWL, XSD
import json
import xlwt

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
def generateModel(subjectEntity, depth, output = {}):
 
    output = {}
    subject = getName(subjectEntity)
    
    
    #1. Find the top parent class
    for subjectOrParent in g.transitive_objects(subjectEntity,RDFS.subClassOf):
        if(subjectOrParent == OPDS.Thing):
            break #When we get to 'Thing' we want to go no further.
        tableName = g.preferredLabel(subjectOrParent,"en")
        table = getName(subjectOrParent)
    tableName = str(tableName[0][1]) # [0][1] syntax needed to fetch value from list and tuple container

    ## Set up a new table for us
    if tableName in output.keys():
        pass
    else:
        output[tableName] = list()

    # Work through all the parent classes
    for subjectOrParent in g.transitive_objects(subjectEntity,RDFS.subClassOf): 
        for dataProperty in g.subjects(predicate=RDFS.domain,object=subjectOrParent):
            ## If the range is a literal, then we add a data property placeholder
            fieldSpec = {}
            fieldSpec['name'] = getName(dataProperty)
            try:
                fieldSpec['title'] = str(g.preferredLabel(dataProperty,"en")[0][1])
            except:
                fieldSpec['title'] = "LABEL MISSING"
            
            fieldSpec['weight'] = float(g.value(dataProperty,OPDS.fieldWeight,default=5))
            
            
            if ((dataProperty, RDFS.range, RDFS.Literal)) in g:
                fieldSpec['values'] = 'Text'
                # print g.value(dataProperty,RDFS.label)
                #   output[subject].update({getName(dataProperty):''})
           ## If the range is a dateTime handle that here
            elif ((dataProperty, RDFS.range, XSD.dateTime)) in g:
                fieldSpec['values'] = 'DataTime'
            elif ((dataProperty, RDFS.range, XSD.float)) in g:
                fieldSpec['values'] = 'Number (float)'
            elif ((dataProperty, RDFS.range, XSD.integer)) in g:
                fieldSpec['values'] = 'Number (integer)'
            ## else we assume the range is an object (we may need to handle for more types of range, such as integer here in future)
            else: 
                
                for subObject in g.objects(subject=dataProperty,predicate=RDFS.range):  
                    if depth < 2:
                        subObject = generateModel(subObject,depth+1)
                        subObjectType = subObject.keys()[0]
                        
                        # ToDo: Consider adding code here to find out all the possible types which this could take. 
                        subObject[subObjectType].insert(1,{"name":subObjectType.lower()+"Type","title":subObjectType +" Type","weight":float(0)})
                        
                        output.update(subObject)
                        
                        fieldSpec['values'] ="Entity: " + subObjectType
                    else:
                        pass
                    
            output[tableName].append(fieldSpec)
    # Sort        
    output[tableName].sort(key=lambda field: field['weight'])
    if(depth > 1):
        return output
    else:
        return output          



for defaultEntity in g.subjects(predicate=OPDS.defaultSubject):
    model = generateModel(defaultEntity,1)


## Write it out to a spreadsheet
spreadsheet = xlwt.Workbook(encoding='ascii')

for table in model:
    sheet = spreadsheet.add_sheet(table)
    c = 0
    for col in model[table]:
        sheet.write(0,c,label=col['title'])
        sheet.write(1,c,label=col['name'])
        c = c + 1

spreadsheet.save("template.xls")
# output = {}
# output = generateModel(URIRef('http://joinedupdata.org/ontologies/philanthropy/Organization'))

print json.dumps(model)

# 1. Look for the defaultSubject
# - Create an object for it
# 2. Look for all it's dataProperties
# 3. Look for all it's objectProperties