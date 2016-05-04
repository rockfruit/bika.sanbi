from Products.ATContentTypes.content import schemata
from Products.Archetypes import atapi
from bika.sanbi.config import PROJECTNAME
from plone.app.folder.folder import ATFolder, ATFolderSchema
from zope.interface.declarations import implements
from bika.sanbi.interfaces import IProjects

schema = ATFolderSchema.copy()


class Projects(ATFolder):
    implements(IProjects)
    displayContentsTab = False
    schema = schema

schemata.finalizeATCTSchema(schema, folderish=True, moveDiscussion=False)
atapi.registerType(Projects, PROJECTNAME)