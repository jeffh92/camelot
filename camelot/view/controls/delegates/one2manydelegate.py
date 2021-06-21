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

import six

from ....core.item_model import FieldAttributesRole, ActionStatesRole
from ....core.qt import variant_to_py, Qt, QtWidgets, py_to_variant
from camelot.view.controls import editors
from .customdelegate import CustomDelegate, DocumentationMetaclass
from ..action_widget import ActionAction, ActionToolbutton, ActionPushButton

import logging
logger = logging.getLogger( 'camelot.view.controls.delegates.one2manydelegate' )

@six.add_metaclass(DocumentationMetaclass)
class One2ManyDelegate(CustomDelegate):
    """Custom delegate for many 2 one relations
  
  .. image:: /_static/onetomany.png
  """

    def __init__( self, parent = None, **kwargs ):
        super( One2ManyDelegate, self ).__init__( parent=parent, **kwargs )
        logger.debug( 'create one2manycolumn delegate' )
        self.kwargs = kwargs

    @classmethod
    def get_standard_item(cls, locale, model_context):
        item = super(One2ManyDelegate, cls).get_standard_item(locale, model_context)
        if model_context.value is not None:
            admin = model_context.field_attributes['admin']
            item.setData(py_to_variant(admin.get_proxy(model_context.value)), Qt.EditRole)
        return item

    def createEditor( self, parent, option, index ):
        logger.debug( 'create a one2many editor' )
        editor = editors.One2ManyEditor( parent = parent, **self.kwargs )
        self.setEditorData( editor, index )
        editor.editingFinished.connect( self.commitAndCloseEditor )
        return editor

    def setEditorData( self, editor, index ):
        logger.debug( 'set one2many editor data' )
        model = variant_to_py( index.data( Qt.EditRole ) )
        editor.set_value( model )
        field_attributes = variant_to_py(index.data(FieldAttributesRole)) or dict()
        editor.set_field_attributes(**field_attributes)

        # update actions
        toolbar = editor.findChild(QtWidgets.QToolBar)
        if toolbar:
            action_states = index.model().data(index, ActionStatesRole)
            if not action_states:
                return
            for action_widget in toolbar.actions() + toolbar.findChildren(ActionToolbutton) + toolbar.findChildren(ActionPushButton):
                if isinstance(action_widget, (ActionAction, ActionToolbutton, ActionPushButton)):
                    state = action_states[action_widget.action_route]
                    action_widget.set_state_v2(state)

    def setModelData( self, editor, model, index ):
        pass
