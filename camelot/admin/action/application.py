#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================
import logging

from ...core.sql import metadata
from ...core.qt import QtCore
from ...core.utils import ugettext as _
from ..application_admin import ApplicationAdmin
from .base import Action

logger = logging.getLogger('camelot.admin.action.application')

class Application( Action ):
    """An action to be used as the entry point of the application.  This
    action will pop up a splash window, set the application attributes, 
    initialize the database, install translators and construct a main window.
    
    Subclass this class and overwrite the :meth:`model_run` method to customize
    the application initialization process
    
    :param application_admin: a subclass of camelot.admin.application_admin.ApplicationAdmin
        customized to your app.  If no application_admin is passed, a default one is
        created (this is not recommended)
    """

    def __init__(self, application_admin=None):
        super(Application, self).__init__()
        if application_admin is None:
            application_admin = ApplicationAdmin()
        self.application_admin = application_admin

    def set_application_attributes(self):
        """Sets the attributes of the QApplication object
        :param application: the QApplication object"""
        application = QtCore.QCoreApplication.instance()
        application.setOrganizationName(self.application_admin.get_organization_name())
        application.setOrganizationDomain(self.application_admin.get_organization_domain())
        application.setApplicationName(self.application_admin.get_name())
        application.setWindowIcon(self.application_admin.get_icon())

    def model_run( self, model_context, mode ):
        """
        Overwrite this generator method to customize the startup process of
        your application.
        
        :param model_context: a :class:`camelot.admin.action.base.ModelContext` object
        """
        from ...core.conf import settings
        from ...core.utils import load_translations
        from ...view import action_steps
        yield action_steps.MainWindow(self.application_admin)
        yield action_steps.UpdateProgress( 1, 5, _('Setup database') )
        settings.setup_model()
        yield action_steps.UpdateProgress( 2, 5, _('Load translations') )
        connection = metadata.bind.connect()
        load_translations(connection)
        yield action_steps.UpdateProgress( 3, 5, _('Install translator') )
        language = QtCore.QLocale.languageToCode(QtCore.QLocale().language())
        yield action_steps.InstallTranslator( language )
        yield action_steps.UpdateProgress( 4, 5, _('Create main window') )
        yield action_steps.NavigationPanel(
            self.application_admin.get_navigation_menu(), model_context=model_context
        )
        yield action_steps.MainMenu(
            self.application_admin.get_main_menu(), model_context=model_context
        )
