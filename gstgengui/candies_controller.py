#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
gst-gengui candies canvas: uses the inspector to generate widgets

Copyright 2009, Florent Thiery, under the terms of LGPL
"""


import candies
from candies import Stage, Group, Label, Color
from candies.sizer import BoxSizer, Style
from candies.spinner import Gauge
from candies.core import CustomVideoTexture

from gstgengui.gstintrospector import PipelineIntrospector
from gstmanager import PipelineLauncher

class CandiesGstController:
    def __init__(self, pipeline_launcher):
        self.pipeline_launcher = pipeline_launcher
        stage = self.stage = Stage(900,768, title="gst-genGUI controller window")
        stage_sizer = BoxSizer(BoxSizer.HORIZONTAL)
        stage.set_sizer(stage_sizer)
        stage.set_color(Color("LightBlue"))

        controls_sizer=BoxSizer(BoxSizer.VERTICAL)
        controls_group = self.controls_group = Group(sizer=controls_sizer)
        self.controls_group.sizer.force_size(600,768)
        self.stage.add(self.controls_group, Style().border(width=5))
        self.controls_group.show()

        pipeline_label = Label("Current pipeline:\n%s" %pipeline_launcher.pipeline_string)
        pipeline_label.show()
        pipeline_label.set_line_wrap(True)
        controls_group.add(pipeline_label, Style().border(width=5))

        textures_sizer=BoxSizer(BoxSizer.VERTICAL)
        textures_group = self.textures_group = Group(sizer=textures_sizer)
        self.stage.add(self.textures_group, Style().border(width=5))
        self.textures_group.show()

    def add_video_texture(self, pipeline, elt_name):
        print "Adding video texture of %s" %elt_name
        texture = CustomVideoTexture(pipeline, elt_name)
        texture.show()
        texture.set_size(480,384)
        self.textures_group.add(texture, Style().border(width=2))

    def add_number_widget(self, element):
        label = Label('Element %s' %element.name)
        label.show()
        self.controls_group.add(label, Style().border(width=5))
        for property in element.properties:
            self.add_gauge(property, element)

    def add_gauge(self, property, parent_element):
        gauge = Gauge(property.minimum, property.maximum, value=property.default_value, label=property.human_name, is_int=property.is_int)
        gauge.value_change_callback = lambda g: self.apply_changes(gauge, property, parent_element)
        gauge.show()
        self.controls_group.add(gauge, Style(1).expand().border(width=2))

    def apply_changes(self, gauge, property, element):
        element.set_property(property.name, gauge.get_value())

    def main(self):
        self.stage.layout()
        self.stage.show()
        self.pipeline_launcher.run()
        candies.main()

if __name__ == '__main__':

    pipeline_launcher = PipelineLauncher()
    pipeline = pipeline_launcher.pipeline
    introspector = PipelineIntrospector(pipeline)

    # Create Candies canvas
    controller = CandiesGstController(pipeline_launcher)
    # Build widgets for currently supported elements
    for element in introspector.elements:
        if element.name.startswith("candies_sink"):
            controller.add_video_texture(pipeline, element.name)
        else:
            controller.add_number_widget(element)

    controller.main()
