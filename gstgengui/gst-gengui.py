#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
gst-gengui candies canvas: uses the inspector to generate widgets

Copyright 2009, Florent Thiery, under the terms of LGPL
"""

from gstintrospector import PipelineIntrospector
from gstmanager import PipelineManager
from gtk_controller import GtkGstController

def build_gui(pipeline, controller):
    introspector = None
    introspector = PipelineIntrospector(pipeline)
    # Build widgets for currently supported elements
    for element in introspector.elements:
        controller.add_element_widget(element)

if __name__ == '__main__':

    def parse_argv(args):
        cmd = ""
        for n in range(1, len(args)):
            cmd+="%s " %args[n]
        print "gst-launch pipeline is: %s" %cmd
        return cmd
   
    from sys import argv
    if len(argv) <= 1:
        print "No gst-launch syntax detected, using config file"
        pipeline_launcher = PipelineManager()
    else:
        gst_string = parse_argv (argv)
        pipeline_launcher = PipelineManager(gst_string)
    pipeline = pipeline_launcher.pipeline

    controller = GtkGstController(pipeline_launcher)

    build_gui(pipeline, controller)
    controller.rebuild_callback = build_gui

    controller.main()
