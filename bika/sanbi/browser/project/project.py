from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.lib import constraintypes
from bika.sanbi import bikaMessageFactory as _
from bika.sanbi.controlpanel.bika_labanalyses import LabAnalysesView
from bika.sanbi.controlpanel.bika_biospecimens import BioSpecimensView
from bika.lims.browser import BrowserView
import json


class ProjectEdit(BrowserView):
    template = ViewPageTemplateFile('templates/project_edit.pt')
    title = _("Project Registration")

    def __init__(self, context, request):
        self.context = context
        self.request = request

        super(ProjectEdit, self).__init__(context, request)
        self.icon = self.portal_url + "/++resource++bika.sanbi.images/project_big.png"

    def __call__(self):
        portal = self.portal
        request = self.request
        context = self.context
        form = self.request.form
        if 'submit' in request:
            context.setConstrainTypesMode(constraintypes.DISABLED)
            portal_factory = getToolByName(context, 'portal_factory')
            context = portal_factory.doCreate(context, context.id)
            context.processForm()

            p_catalog = getToolByName(context, 'portal_catalog')
            brains = p_catalog.searchResults(portal_type='Client', ClientID=form['ClientID'])
            client = brains[0].getObject()
            context.setClientID(client)

            analyses_uids = form.get('Analyses', [])
            context.setAnalyses(analyses_uids)

            obj_url = context.absolute_url_path()
            request.response.redirect(obj_url)
            return

        return self.template()

    def get_fields_with_visibility(self, visibility, mode=None):
        mode = mode if mode else 'edit'
        schema = self.context.Schema()
        fields = []
        for field in schema.fields():
            isVisible = field.widget.isVisible
            v = isVisible(self.context, mode, default='invisible', field=field)
            if v == visibility:
                fields.append(field)
        return fields


class ProjectAnalysesView(LabAnalysesView):
    def __init__(self, context, request, uids):
        self.context = context
        self.request = request
        self.uids = uids

        super(ProjectAnalysesView, self).__init__(context, request)

    def folderitems(self):
        items = LabAnalysesView.folderitems(self)
        out_items = []
        catalog = getToolByName(self.context, 'bika_setup_catalog')
        for x in range(len(items)):
            if not items[x].has_key('obj'): continue
            obj = items[x]['obj']

            if obj.UID() in self.uids:
                items[x]['Description'] = obj.Description()
                biospecs = []
                for uid in obj.getBiospecimens():
                    biospec = catalog({'portal_type': 'BioSpecimen', 'UID': uid})
                    if biospec:
                        biospecs.append(biospec[0].title)

                if biospecs:
                    items[x]['Biospecimens'] = ', '.join(biospecs)
                items[x]['replace']['Title'] = "<a href='%s'>%s</a>" % \
                                               (items[x]['url'], items[x]['Title'])
                out_items.append(items[x])

        return out_items

    def __call__(self):
        return super(ProjectAnalysesView, self).__call__()


class ProjectBiospecView(BioSpecimensView):
    def __init__(self, context, request, uids):
        self.context = context
        self.request = request
        self.uids = uids

        super(ProjectBiospecView, self).__init__(context, request)

    def folderitems(self):
        items = BioSpecimensView.folderitems(self)
        out_items = []
        for x in range(len(items)):
            if not items[x].has_key('obj'): continue
            obj = items[x]['obj']

            if obj.UID() in self.uids:
                items[x]['Description'] = obj.Description()
                items[x]['replace']['Title'] = "<a href='%s'>%s</a>" % \
                                               (items[x]['url'], items[x]['Title'])
                out_items.append(items[x])

        return out_items

    def __call__(self):
        return super(ProjectBiospecView, self).__call__()

class ProjectView(BrowserView):
    """
    """
    template = ViewPageTemplateFile("templates/project_view.pt")
    title = _("Project Registration")

    def __call__(self):
        context = self.context
        request = self.request
        portal = self.portal
        self.absolute_url = context.absolute_url()
        setup = portal.bika_setup

        # __Disable the add new menu item__ #
        context.setLocallyAllowedTypes(())

        # __Collect general data__ #
        self.id = context.getId()
        self.title = context.Title()
        self.client = context.getClientID().Title()
        self.study_type = context.getStudyType()
        self.participants = context.getNumParticipants()
        self.age_interval = str(context.getAgeLow()) + ' - ' + str(context.getAgeHigh())

        biospecimens = ProjectBiospecView(context, request, context.getBiospecimens())
        biospecimens()
        biospecimens.show_column_toggles = False
        biospecimens.allow_edit = False
        #biospecimens.show_workflow_action_buttons = False

        self.bio_table = biospecimens.contents_table()

        analyses = ProjectAnalysesView(context, request, context.getAnalyses())
        analyses()
        analyses.show_column_toggles = False
        #analyses.show_workflow_action_buttons = False
        self.analyses_table = analyses.contents_table()

        return self.template()



class AjaxGetAnalyses:
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.errors = {}

    def __call__(self):
        form = self.request.form
        uids = 'biospecs[]' in form and form['biospecs[]'] or ''
        uids = uids.split() if not isinstance(uids, list) else uids
        biospecimens = []
        bs_catalog = getToolByName(self.context, 'bika_setup_catalog')
        if uids:
            for uid in uids:
                brains = bs_catalog.searchResults({'portal_type':'BioSpecimen',
                                                'UID':uid})
                bio_title = brains[0].title
                brains = bs_catalog.searchResults({'portal_type':'LabAnalysis'})
                for brain in brains:
                    if uid in brain.getObject().getBiospecimens():
                        if not any(d['uid'] == brain.UID for d in biospecimens):
                            biospecimens.append({'uid': brain.UID,
                                                 'title': brain.title,
                                                 'bio_title': bio_title})
                        else:
                            for d in biospecimens:
                                if d['uid'] == brain.UID:
                                    d['bio_title'] = d['bio_title'] + ', ' + bio_title
        else:
            analyses = self.context.getAnalyses()
            b_selected = self.context.getBiospecimens()
            for a in analyses:
                brains_a = bs_catalog.searchResults(portal_type='LabAnalysis',
                                                    UID=a)
                biospecs = brains_a[0].getObject().getBiospecimens()
                bio_title = ''
                for b in biospecs:
                    if b in b_selected:
                        brains_b = bs_catalog.searchResults(portal_type='BioSpecimen',
                                                            UID=b)
                        if bio_title:
                            bio_title = bio_title + ', ' + brains_b[0].title
                        else:
                            bio_title = brains_b[0].title

                biospecimens.append({'uid': brains_a[0].UID,
                                     'title': brains_a[0].title,
                                     'bio_title': bio_title})

        #TODO: MAYBE IS BETTER TO SHOW THE ANALYSIS AS A TABLE LIKE IN ANALYSISREQUEST
        #TODO: INSTEAD OF SHOWING THEM AS CHECKBOXES.
        return json.dumps(biospecimens)