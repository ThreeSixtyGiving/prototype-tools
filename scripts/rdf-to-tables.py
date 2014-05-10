# This script generates an intermediate representation of the data model ready for translation into CSV
import json
import xlwt
import operator # Used in sorting
from sets import Set

from genmodel import generateModel


model = generateModel("http://joinedupdata.org/ontologies/philanthropy/Grant",1,{})



## Write it out to a spreadsheet
spreadsheet = xlwt.Workbook(encoding='ascii')

for table in sorted(model):
    sheet = spreadsheet.add_sheet(table)
    c = 0
    cols = []

    #Dictionary sorting work-around
    for col in model[table]:
        if(not(col == '_meta')):
            cols.append((col,model[table][col]["weight"]))
    cols = sorted(cols,key=lambda x: x[1])
    
    for col in cols:
        sheet.write(0,c,label=model[table][col[0]]['title'])
        sheet.write(1,c,label=model[table][col[0]]['name'])
        sheet.write(2,c,label=model[table][col[0]]['weight'])
        try:
            sheet.write(3,c,label=model[table][col[0]]['values'])
        except:
            try:
                #print model[table][col[0]]['values']
                pass
            except:
                pass
        c = c + 1
spreadsheet.save("template.xls")



# 1. Look for the defaultSubject
# - Create an object for it
# 2. Look for all it's dataProperties
# 3. Look for all it's objectProperties