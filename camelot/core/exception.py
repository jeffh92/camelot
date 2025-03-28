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

"""Camelot specific subclasses of Exception
"""

from camelot.core.utils import ugettext_lazy as _

   
class UserException(Exception):
    """
    Raise this exception to inform the user he did something wrong, without
    showing a stack trace or other internals.  Raising this exception won't
    log stack traces either, as the occurance of this exception is considered
    a non-event for the developer::
    
        from camelot.core.exception import UserException
        from camelot.core.utils import ugettext
        
        if not dvd.empty:
            raise UserException( ugettext('Could not burn movie to non empty DVD'),
                                 resolution = ugettext('Insert an empty DVD and retry') )

    Will popup a gentle dialog for the user :

    .. image:: /_static/controls/user_exception.png

    """
    
    def __init__(self, text, title=_('Could not proceed'), icon=None, resolution=None, detail=None):
        """
        :param title: the title of the dialog box that informs the user
        :param text: the top text in the dialog
        :param resolution: what the user should do to solve the issue
        :param detail: a detailed description of what went wrong
        """
        super(UserException, self).__init__(text)
        self.title = title
        self.text = text
        self.icon = icon
        self.resolution = resolution
        self.detail = detail

class GuiException(Exception):
    """
    This exception is raised by the Action mechanism when the action requested
    something from the GUI but an unexpected event occured.  The action can
    choose to ignore it or handle it.
    """
    pass

class CancelRequest(Exception):
    """
    This exception is raised by the GUI when the user wants to cancel an action,
    this exception is then past to the *model thread*
    """
    pass



