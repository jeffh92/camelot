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
import functools
import logging

import six

from sqlalchemy import orm, sql, exc

from .list_proxy import ListModelProxy, TwoWayDict, SortingRowMapper

LOGGER = logging.getLogger(__name__)

class QueryModelProxy(ListModelProxy):
    """
    A concrete model proxy for displaying objects in sqlalchemy query objects
    """

    def __init__(self, query):
        """
        :param query: a sqlalchemy query
        """
        super(QueryModelProxy, self).__init__([])
        self._query = query
        self._length = None
        self._filters = dict()
        self._sort_decorator = self._get_sort_decorator()

    def __len__(self):
        if self._length is None:
            # manipulate the query to circumvent the use of subselects and order by
            # clauses
            query = self.get_query(order_clause=False)
            mapper = query._mapper_zero()
            select = query.order_by(None).as_scalar()
            columns = [sql.func.count(mapper.primary_key[0])]
            select = select.with_only_columns(columns)
            self._length = query.session.execute(select, mapper=mapper).scalar()
        return self._length + len(self._objects)

    def copy(self):
        new = super(QueryModelProxy, self).copy()
        new._query = self._query
        new._length = self._length
        new._filters = self._filters.copy()
        new._sort_decorator = self._sort_decorator
        return new

    def sort(self, key=None, reverse=False):
        self._indexed_objects = TwoWayDict()
        self._sort_decorator = self._get_sort_decorator(key, reverse)

    def append(self, obj):
        if obj in self._objects:
            return
        # a new object cannot be in the query, so no need to check it
        if obj in self._query.session.new:
            self._objects.append(obj)
            return
        # if the object is indexed, no need either to check it

        # check if the object is in the query
        mapper = self._query._mapper_zero()
        primary_key = mapper.primary_key_from_instance(obj)
        if self.get_query(order_clause=False).get(primary_key) is not None:
            return
        self._objects.append(obj)

    def index(self, obj):
        try:
            return self._indexed_objects[obj]
        except KeyError:
            i = self._objects.index(obj)
            self._indexed_objects[i+self._length] = obj
            return i+self._length

    def remove(self, obj):
        if obj in self._objects:
            self._objects.remove(obj)
        elif self._length is not None:
            self._length = self._length - 1
        # clear sort and filter, this could probably happen more efficient
        self._indexed_objects = TwoWayDict()
        self._sort_and_filter = SortingRowMapper()

    def get_query(self, order_clause=True):
        """
        :return: the query used to fetch the data, this is not the same as the
            one set in the constructor, as sorting and filters will modify it.
        """
        query = self._query
        # filters might be changed in the gui thread while being iterated
        for filter_, value in six.iteritems(self._filters.copy()):
            query = filter_.decorate_query(query, value)
        if order_clause:
            query = self._sort_decorator(query)
        return query

    def _extend_indexed_objects(self, offset, limit):
        LOGGER.debug('extend cache from {0} with limit {1}'.format(offset, limit))
        if limit > 0:
            query = self.get_query().offset(offset).limit(limit)
            free_index = offset
            for obj in query.all():
                # find a free index for the object
                while self._indexed_objects.get(free_index) not in (None, obj):
                    free_index += 1
                # check if the object is not present with another index,
                # if the object is at the free index, nothing needs to happen
                if self._indexed_objects.get(obj) is None:
                    self._indexed_objects[free_index] = obj
                # if the object is in _objects, remove it from there, since
                # it is in the query as well, while keeping the total length
                # of the collection invariant
                if obj in self._objects:
                    self._objects.remove(obj)
                    if self._length is not None:
                        self._length = self._length + 1
            row_count = len(self)
            rows_in_query = row_count - len(self._objects)
            # Verify if rows not in the query have been requested
            if offset+limit >= rows_in_query:
                for row in range(max(rows_in_query, offset), min(offset+limit, row_count)):
                    obj = self._objects[row - rows_in_query]
                    self._indexed_objects[row] = obj

    def _get_sort_decorator( self, key=None, reverse=None ):
        """
        When no arguments are given, use the default sorting, which is according to
        the primary keys of the model.  This to impose a strict ordening of
        the rows in the model.
        """

        order_by, join = [], None

        mapper = self._query._mapper_zero()
        #
        # First sort according the requested column
        #
        if None not in (key, reverse):
            property = None
            class_attribute = getattr(mapper.class_, key)

            #
            # The class attribute of a hybrid property can be an sql clause
            #

            if isinstance(class_attribute, sql.ClauseElement):
                order_by.append((class_attribute, reverse))

            try:
                property = mapper.get_property(
                    key,
                )
            except exc.InvalidRequestError:
                pass
            
            # If the field is a relation: 
            #  If it specifies an order_by option we have to join the related table, 
            #  else we use the foreign key as sort field, without joining
            if property and isinstance(property, orm.properties.RelationshipProperty):
                target = property.mapper
                if target:
                    if target.order_by:
                        join = key
                        class_attribute = target.order_by[0]
                    else:
                        class_attribute = list(property._calculated_foreign_keys)[0]
            if property:
                order_by.append((class_attribute, reverse))
                                
        def sort_decorator(order_by, join, query):
            order_by = list(order_by)
            if join:
                query = query.outerjoin(join)
            # remove existing order clauses, because they might interfer
            # with the requested order from the user, as the existing order
            # clause is first in the list, and put them at the end of the list
            if query._order_by:
                for order_by_column in query._order_by:
                    order_by.append((order_by_column, False))
            #
            # Next sort according to default sort column if any
            #
            if mapper.order_by:
                for mapper_order_by in mapper.order_by:
                    order_by.append((mapper_order_by, False))
            #
            # In the end, sort according to the primary keys of the model, to enforce
            # a unique order in any case
            #
            for primary_key_column in mapper.primary_key:
                order_by.append((primary_key_column, False))
            query = query.order_by(None)
            order_by_columns = set()
            for order_by_column, order in order_by:
                if order_by_column not in order_by_columns:
                    if order == False:
                        query = query.order_by(order_by_column)
                    else:
                        query = query.order_by(sql.desc(order_by_column))
                    order_by_columns.add(order_by_column)
            return query
        
        return functools.partial(sort_decorator,
                                 order_by,
                                 join)


