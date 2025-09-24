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

""":class:`QtGui.QValidator` subclasses to be used in the
editors or other widgets.
"""
import dataclasses
import re
import stdnum.util
from typing import Optional

from camelot.core.exception import UserException
from camelot.core.serializable import DataclassSerializable
from camelot.core.utils import ugettext

from dataclasses import dataclass, InitVar
from sqlalchemy.ext import hybrid
from stdnum.exceptions import InvalidFormat


@dataclass(frozen=True)
class ValidatorState(DataclassSerializable):

    value: Optional[str] = None
    formatted_value: Optional[str] = None
    valid: bool = True
    error_msg: Optional[str] = None

    # Fields that influence how values are sanitized.
    deletechars: str = ''
    to_upper: bool = False

    # Info dictionary allowing user-defined metadata to be associated.
    # This data is meant for server-side validation usecases and therefor should not be serialized.
    info: InitVar(dict) = None

    def __post_init__(self, info):
        object.__setattr__(self, "info", info or dict())

    @hybrid.hybrid_method
    def sanitize(self, value):
        """
        Hybrid method to sanitizes the given value by stripping chars and conditionally
        converting the result to uppercase based on this state.
        If the stripped form becomes the empty string, None will be returned.
        The hybrid behaviour will result in the field defaults for deletechars and to_upper being used
        if called on the class level, and the initialized field values if called on the instance level.
        """
        if isinstance(value, str):
            value = stdnum.util.clean(value, self.deletechars).strip()
            if self.to_upper == True:
                value = value.upper()
            return value or None

    @classmethod
    def for_value(cls, value, **kwargs):
        # Use initialized state to sanitize value so that possible provided
        # sanitization kwargs are correctly accounted for.
        state = cls(**kwargs)
        value = state.sanitize(value)
        return dataclasses.replace(
            state,
            value=value,
            formatted_value=value,
        )

    @classmethod
    def for_setting(cls, key, **kwargs):
        def for_setting_proxy(proxy):
            return cls.for_value(value=getattr(proxy, key), **kwargs)
        return for_setting_proxy

    def valid_or_raise(self, message=None):
        """
        Check whether this state is valid and raise a UserException if not.
        The exception message will be this state's error message.

        :param message: optional custom message for the UserException that
        will be raised. The provided message will be formatted with this state's
        error message as the first format value.
        """
        for error_msg in self.valid_or_yield(message):
            raise UserException(error_msg)

    def valid_or_yield(self, message=None):
        """
        Check whether this state is valid and yield this state's error message if not.

        :param message: optional custom message to be yielded.
        The provided message will be formatted with this state's error message as the first format value.
        """
        if not self.valid:
            error_msg = ugettext(self.error_msg)
            if message is None:
                yield error_msg
            else:
                yield message.format(error_msg)

class AbstractValidator:
    """
    Validators must be default constructable.
    Validators can have a state which is set by set_state.
    """

    validators = dict()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.validators[cls.__name__] = cls


class DateValidator(AbstractValidator):
    pass


@dataclass(frozen=True)
class RegexValidatorState(ValidatorState):

    regex: str = None
    format_repl: str = None
    compact_repl: str = None
    example: str = None

    ignore_case: bool = False

    def __post_init__(self, info):
        super().__post_init__(info)

    @classmethod
    def for_value(cls, value, **kwargs):
        # Use inherited ValidatorState behaviour, which will sanitize the value.
        state = super().for_value(value, **kwargs)

        # Check if the value matches the regex.
        if (state.value is not None) and (state.regex is not None):
            if not re.fullmatch(state.regex, state.value, flags=re.IGNORECASE if state.ignore_case else 0):
                state = dataclasses.replace(
                    state,
                    valid=False,
                    error_msg=InvalidFormat.message,
                )
            else:
                # If corresponding replacement patterns are defined, use them to construct
                # the compact as the formatted value:
                value = state.value
                if state.compact_repl:
                    state = dataclasses.replace(state, value=re.sub(state.regex, cls.replace(state.compact_repl), value))
                if state.format_repl:
                    state = dataclasses.replace(state, formatted_value=re.sub(state.regex, cls.replace(state.format_repl), value))

        return state

    @classmethod
    def for_attribute(cls, attribute, **kwargs):
        def for_obj(obj):
            if obj is not None:
                return cls.for_value(attribute.__get__(obj, None), **kwargs)
            return cls()
        return for_obj

    @staticmethod
    def replace(regex_repl):
        if regex_repl is not None and '|' in regex_repl:
            def multi_repl(m):
                for i, repl in enumerate(regex_repl.split('|'), start=1):
                    if m.group(i) is not None:
                        return re.sub(m.re, repl, m.string)
            return multi_repl
        return regex_repl

class RegexValidator(AbstractValidator):
    pass
