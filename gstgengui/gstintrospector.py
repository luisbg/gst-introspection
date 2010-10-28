#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
gst-gengui: gstreamer introspector

Scans pipelines for named elements and associated properties
When launched separately, prints all the found elements

Copyright 2009, Florent Thiery, under the terms of LGPL
"""

import gobject
import gst
from config import *

class Property:
    def __init__(self, property, parent_element):
        self.parent_element = parent_element
        self.description = property.blurb
        self.default_value = property.default_value
        self.name = property.name
        self.human_name = property.nick
        self.value_type = property.value_type
        self.update_value()

    def update_value(self):
        value = self.parent_element._gst_element.get_property(self.name)
        #print "Real value of %s is %s (get_property after set_property)" %(self.name, value)
        if value is None:
            if self.default_value is not None:
                value = self.default_value
            else:
                value = "Default"
        self.value = value

class BooleanProperty(Property):
    def __init__(self, property, parent_element):
        Property.__init__(self, property, parent_element)

class StringProperty(Property):
    def __init__(self, property, parent_element):
        Property.__init__(self, property, parent_element)

class NumberProperty(Property):
    def __init__(self, property, parent_element):
        Property.__init__(self, property, parent_element)
        self.minimum = property.minimum
        self.maximum = property.maximum
        self.is_int = (self.value_type == gobject.TYPE_INT64 or self.value_type == gobject.TYPE_INT or self.value_type == gobject.TYPE_ULONG or self.value_type == gobject.TYPE_UINT or self.value_type == gobject.TYPE_UINT64)

class EnumProperty(Property):
    def __init__(self, property, parent_element):
        Property.__init__(self, property, parent_element)
        self.value_type = gobject.TYPE_ENUM
        self.values_list = []
        if property.__gtype__.has_value_table:
            values = property.enum_class.__enum_values__
            for index in values:
                self.values_list.append(values[index].value_name)
                # TODO: regarder dans buzztard comment faire propre
                # Nb: l'index, value_name et value_nick peuvent tous deux etre utilisés pour set_property

class Element:
    def __init__(self, gst_element):
        #print "Getting properties of %s" %gst_element
        self._gst_element = gst_element
        _properties_list = gobject.list_properties(self._gst_element)
        self.name = self._gst_element.get_factory().get_name()
        self.number_properties = number_properties = []
        self.boolean_properties = boolean_properties = []
        self.string_properties = string_properties = []
        self.enum_properties = enum_properties = []

        for property in _properties_list:
            #print "Introspecting property %s, type: %s" %(property.name, property.value_type)
            if property.name in ignore_list:
                print "Property %s is in ignore list, skipping" %property.name

            elif property.value_type == gobject.TYPE_INT64 or \
               property.value_type == gobject.TYPE_INT or \
               property.value_type == gobject.TYPE_UINT or \
               property.value_type == gobject.TYPE_UINT64 or \
               property.value_type == gobject.TYPE_DOUBLE or \
               property.value_type == gobject.TYPE_FLOAT or \
               property.value_type == gobject.TYPE_LONG or \
               property.value_type == gobject.TYPE_ULONG:
                #print "found %s" %(property.value_type)
                number_property = NumberProperty(property, self)
                number_properties.append(number_property)

            elif property.value_type == gobject.TYPE_BOOLEAN:
                #print "Found boolean '%s'" %property.nick
                boolean_property = BooleanProperty(property, self)
                boolean_properties.append(boolean_property)

            elif property.value_type == gobject.TYPE_CHAR or \
                 property.value_type == gobject.TYPE_GSTRING or \
                 property.value_type == gobject.TYPE_STRING or \
                 property.value_type == gobject.TYPE_UCHAR:
                #print "found Char type %s" %property.value_type
                string_property = StringProperty(property, self)
                string_properties.append(string_property)
          
            elif property.value_type.is_a(gobject.TYPE_ENUM):
                #print "Found enum '%s'" %property.name
                enum_property = EnumProperty(property, self)
                enum_properties.append(enum_property)

            else:
                print "Property type %s has no associated known types, skipping" %property.value_type

    def set_property(self, property, value):
        self._gst_element.set_property(property, value)

class PipelineIntrospector:
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.gst_elements = []
        self.elements = []
        self._get_gst_elements()
        self._introspect_elements()

    def _get_gst_elements(self):
        for elt in self.pipeline:
            gst_element = elt
            #print "Real gst object is %s" %elt
            if gst_element:
                self.gst_elements.append(gst_element)
        print "Got %s gst elements" %len(self.gst_elements)

    def _introspect_elements(self):
        for gst_element in self.gst_elements:
            element = Element(gst_element)
            self.elements.append(element)

    def print_all(self):
        print "Printing all of them"
        for element in self.elements:
            print element
            if True:
                print "\nElement: %s" %element.name
                for property in element.number_properties:
                    print property.name

