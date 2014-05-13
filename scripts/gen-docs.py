# This script generates an intermediate representation of the data model ready for translation into CSV
import json
import operator # Used in sorting
from sets import Set
from genmodel import generateModel, getName

# Change final parameter to False / True depending on whether you want roll-ups or not.
# Note to self: Use python gen-docs.py > ../website/standard/_includes/buildingblocks.html with rollups false for keeping documentation updated.
model = generateModel("http://joinedupdata.org/ontologies/philanthropy/Grant",1,{},False)

print "<ul>"
for table in sorted(model):
    print "<li><a href='#"+table+"'>"+table +"</a></li>"
print "</ul>"

print "<p>Details on each of these building blocks can be found below.</p>"

for table in sorted(model):
    
    print "<h4 class='activity' id='" + table + "'><span class='glyphicon glyphicon-th'></span> "+table+"</h4>"
    print "<p>"+model[table]["_meta"]['description']+"</p>"
    print "<p><strong>Types:</strong> "+ ", ".join(model[table]["_meta"]['types']) + "</p>"
    print """
      <div class="panel panel-primary">
        <div class="panel-heading">
          <h4 class="panel-title">
            <a data-toggle="collapse" data-target="#%s">
              Data properties
            </a>
          </h4>
        </div>
        <div id="%s" class="panel-collapse collapse out">
          <div class="panel-body"> 
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title (en)</th>
                <th>Description</th>
                <th>Values</th>
              </tr>
            </thead><tbody>
""" % ("table-"+table,"table-"+table)

    c = 0
    cols = []
    
    #Dictionary sorting work-around
    for col in model[table]:
        if(not(col == '_meta')):
            cols.append((col,model[table][col]["weight"]))
    cols = sorted(cols,key=lambda x: x[1])
    
    for col in cols:
        print "<tr class='rowtype-"+str(model[table][col[0]]['values']).lower()+"'>"
        print "<td>" + model[table][col[0]]['name'] + "</td>"
        print "<td>" + model[table][col[0]]['title'] + "</td>"
        try:
            print "<td>" + model[table][col[0]]['description'] + "</td>"
        except:
            print "<td> No description </td>"
        try:
            print "<td>" + model[table][col[0]]['values'] + "</td>"
        except:
            print "<td> No values specified </td>"
        print "</tr>"
        c = c + 1

    print """</tbody></table></div>
    </div>
    </div>"""
    
    ## Put together details of all the relationships
    print """
          <div class="panel panel-info">
            <div class="panel-heading">
              <h4 class="panel-title">
                <a data-toggle="collapse" data-target="#%s">
                  Relationship properties
                </a>
              </h4>
            </div>
            <div id="%s" class="panel-collapse collapse out">
              <div class="panel-body"> 
              <table class="table">
                <thead>
                  <tr>
                    <th>Relationship</th>
                    <th>Title</th>
                    <th>Description</th>
                    <th>Related to</th>
                  </tr>
                </thead>
                <tbody>
    """ % ("related-"+table,"related-"+table)
    
    #Dictionary sorting work-around
    rcols = []
    for col in model[table]['_meta']['related']:
        rcols.append((col,model[table]['_meta']['related'][col]["topObject"]))
    rcols = sorted(rcols,key=lambda x: x[1])
    
    for related in rcols:
        relatedItem = model[table]['_meta']['related'][related[0]] 
        print "<tr>"
        print "<td>" + relatedItem['relationshipName'] + "</td>"
        print "<td>" + relatedItem['title'] + "</td>"
        print "<td>" + relatedItem['description'] + "</td>"
        print "<td> <a href='#" + relatedItem['topObject'] + "'>" + relatedItem['objectName'] + " (" + relatedItem['topObject'] +")</a></td>"
        print "</tr>"

    print """</tbody></table></div>
       </div>
       </div>"""