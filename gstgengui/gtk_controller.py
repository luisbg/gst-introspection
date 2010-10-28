#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import gobject

# TODOs
# * refresh is unstable
# * auto video embed is unstable (black contours ? lag ?) 

class VideoWidget(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.imagesink = None
        self.unset_flags(gtk.DOUBLE_BUFFERED)

    def do_expose_event(self, event):
        if self.imagesink:
            self.imagesink.expose()
            return False
        else:
            return True

    def set_sink(self, sink):
        assert self.window.xid
        self.imagesink = sink
        self.imagesink.set_xwindow_id(self.window.xid)

class GtkGstController:

    def delete_event(self, widget, event, data=None):
        print "delete event occurred"
        self.pipeline_launcher.stop()
        return False

    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        gtk.main_quit()

    def __init__(self, pipeline_launcher):
        self.pipeline_launcher = pipeline_launcher
        self.pipeline_launcher.bus.enable_sync_message_emission()
        self.pipeline_launcher.bus.connect('sync-message::element', self.on_sync_message)

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("gst-gengui")
        self.window.set_size_request(800, 600)
        # Sets the border width of the window.
        self.window.set_border_width(6)

        #self.main_container = gtk.VBox(False, 0)
        self.main_container = gtk.VPaned()
        self.properties_container = gtk.VBox(False, 0)

        # graphical pipeline output
        self.preview_container = gtk.HBox(False, 0)
        self.preview_container.set_size_request(800,200)

        # parameter area
        self.scrolled_window = scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_border_width(0)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        scrolled_window.add_with_viewport(self.properties_container)

        # play/stop/pause controls
        pipeline_controls = self._create_pipeline_controls(pipeline_launcher)

        #self.main_container.pack_start(self.preview_container, True, True, 3)
        #self.main_container.pack_start(pipeline_controls, False, False, 3)
        #self.main_container.pack_end(scrolled_window, True, True, 3)
        #self.main_container.add1(self.preview_container)
        self.main_container.add1(self.preview_container)
        self.main_container.add2(pipeline_controls)

        self.window.add(self.main_container)

        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)

        self.window.show_all()

    def on_sync_message(self, bus, message):
        if message.structure is None:
            return
        if message.structure.get_name() == 'prepare-xwindow-id':
            print "prepare-xwindow-id, %s" %message
            self._create_videowidget(message)

    def _create_videowidget(self, message):
        videowidget = None
        videowidget = VideoWidget()
        videowidget.show()
        self.preview_container.pack_start(videowidget, True, True, 0)

        # Sync with the X server before giving the X-id to the sink
        # gtk.gdk.display_get_default().sync()
        # gobject.idle_add(videowidget.set_sink, message.src)
        videowidget.set_sink(message.src)
        message.src.set_property('force-aspect-ratio', True)

    def _create_pipeline_controls(self, pipeline_launcher):
        container = gtk.VBox(False,3)


        label = gtk.Label("Pipeline description")
        entry = gtk.TextView()
        entry.set_size_request(400,50)
        entry.set_wrap_mode(gtk.WRAP_CHAR)
        self.textbuffer = textbuffer = entry.get_buffer()
        textbuffer.set_text(pipeline_launcher.pipeline_desc)
        textbuffer.set_modified(False)

        container.add(label)
        container.add(entry)

        container_btns = gtk.HBox()
        container.add(container_btns)

        self.refresh_button = refresh_btn = self._create_button(label="Refresh", callback=self._refresh)
        refresh_btn.set_sensitive(False)
        container_btns.add(refresh_btn)

        state_label = gtk.Label("State")
        container_btns.add(state_label)

        position_label = gtk.Label("Position")
        container_btns.add(position_label)

        start_btn = self._create_button(label="Play", callback=pipeline_launcher.run)
        container_btns.add(start_btn)

        stop_btn = self._create_button(label="Stop", callback=self.stop)
        container_btns.add(stop_btn)

        pause_btn = self._create_button(label="Pause", callback=pipeline_launcher.pause)
        container_btns.add(pause_btn)

        eos_btn = self._create_button(label="Send EOS", callback=pipeline_launcher.send_eos)
        container_btns.add(eos_btn)

        container.add(self.scrolled_window)

        # Polling for changes
        gobject.timeout_add(500, self._check_for_pipeline_changes, textbuffer)
        gobject.timeout_add(500, self._check_for_pipeline_position, position_label)
        gobject.timeout_add(500, self._check_for_pipeline_state, state_label)

        return container

    def main(self):
        gobject.idle_add(self.pipeline_launcher.run)
        gtk.main()

    def stop(self, *args):
        self.pipeline_launcher.stop(*args)
        self._clean_previews()

    def _clean_previews(self):
        for video in self.preview_container:
            self.preview_container.remove(video)
            del(video)

    def _check_for_pipeline_state(self, state_label):
        state = self.pipeline_launcher.get_state()
        state_label.set_text(state)
        return True

    def _check_for_pipeline_position(self, position_label):
        duration = str(self.pipeline_launcher.get_duration())
        position = str(self.pipeline_launcher.get_position())
        position_label.set_text("Position: %s s / %s s" %(position, duration))
        return True

    def _check_for_pipeline_changes(self, textbuffer):
        if textbuffer.get_modified():
            #print "Change detected"
            self.new_description = textbuffer.get_text(*textbuffer.get_bounds())
            self.refresh_button.set_sensitive(True)
        return True

    def _get_latest_description(self):
        return self.new_description

    def _reset_property(self, widget, args):
        print "Resetting property value to default value"
        property = args[0]
        adj = args[1]
        property.parent_element.set_property(property.name, property.default_value)
        adj.set_value(property.default_value)

    def _refresh(self, *args):
        self._clean_controls()
        self.stop(*args)

        print "Refreshing pipeline with description: %s" %self.new_description
        self.pipeline_launcher.redefine_pipeline(new_string=self._get_latest_description())
        self.pipeline_launcher.bus.connect('message::element', self.on_sync_message)
        self.pipeline_launcher.run()
        self.textbuffer.set_modified(False)
        self.rebuild_callback(self.pipeline_launcher.pipeline, self)

    def _clean_controls(self):
        print "Removing all controls"
        for item in self.properties_container:
            self.properties_container.remove(item)

    def _create_button(self, label="Hello", callback=None, callback_args=None):
        button = gtk.Button(label)
        button.show()
        if callback is not None:
            button.connect("clicked", callback, callback_args)
        return button

    def _create_element_widget(self, element):
        mcontainer = gtk.Expander(element.name) 
        container = gtk.VBox()
        mcontainer.add(container)
        print element.name
        if len(element.number_properties) > 0:
            for number_property in element.number_properties:
                spinner = self._create_spinner(number_property)
                container.pack_start(spinner, False, False, 6)
        if len(element.boolean_properties) > 0:
            for boolean_property in element.boolean_properties:
                check_btn = self._create_check_btn(boolean_property)
                container.pack_start(check_btn, False, False, 6)
        if len(element.string_properties) > 0:
            for string_property in element.string_properties:
                if string_property.name == "location":
                    entry = self._create_filebrowser(string_property)
                else:
                    entry = self._create_entry(string_property)
                container.pack_start(entry, False, False, 6)
        if len(element.enum_properties) > 0:
            for enum_property in element.enum_properties:
                enum = self._create_enum_combobox(enum_property)
                container.pack_start(enum, False, False, 6)
        container.show()
        mcontainer.show()
        return mcontainer

    def _create_spinner(self, property):
        if property.is_int:
            step_incr=1
            num_digits = 0
        else:
            step_incr=0.1
            num_digits=1

        adj = gtk.Adjustment(value=property.value, lower=property.minimum, upper=property.maximum, step_incr=step_incr, page_incr=0, page_size=0)

        container = gtk.HBox()
        label = gtk.Label(property.human_name)
        spinner = gtk.SpinButton(adj, 0.1, num_digits)

        slider = gtk.HScale(adj)
        # showing the value uses space, its shown in the entry next to it anyway
        slider.set_draw_value(False)
        #slider.set_digits(num_digits)
        #slider.set_size_request(300, 20)
        slider.show()

        reset_btn = self._create_button("Reset", callback=self._reset_property, callback_args=[property, adj])

        container.pack_start(label, False, True, 20)
        container.pack_end(reset_btn, False, True, 20)
        container.pack_end(spinner, False, True, 20)
        container.pack_end(slider, True, True, 20)

        if property.is_int:
            state_getter = spinner.get_value_as_int
        else:
            state_getter = spinner.get_value

        adj.connect("value_changed", self.apply_changes, state_getter, property)

        label.show()
        spinner.show()
        container.show()

        return container

    def _create_check_btn(self, property):
        button = gtk.CheckButton(property.human_name)
        button.set_active(property.value)
        button.connect("toggled", self.apply_changes, button.get_active, property)
        button.show()
        return button

    def _create_enum_combobox(self, property):
        combobox = gtk.combo_box_new_text()
        for value in property.values_list:
            combobox.append_text(value)
        combobox.set_active(property.value)
        combobox.connect("changed", self.apply_changes, combobox.get_active, property)
        combobox.show()
        return combobox

    def _create_entry(self, property):
        print "Creating entry for property %s" %property.name
        container = gtk.HBox()
        label = gtk.Label(property.human_name)
        label.show()
        entry = gtk.Entry()
        entry.set_text(property.value)
        entry.connect("activate", self.apply_changes, entry.get_text, property)
        entry.show()
        container.pack_start(label, False, True, 20)
        container.pack_end(entry, False, True, 20)
        container.show()
        return container

    def _create_filebrowser(self, property):
        container = gtk.HBox()
        container.show()

        label = gtk.Label(property.name)
        label.show()
        container.add(label)

        open_btn = self._create_button(label="Choose file", callback=self._display_fileselector, callback_args=property)
        open_btn.show()
        container.add(open_btn)

        return container

    def _display_fileselector(self, widget, property):
        chooser = gtk.FileChooserDialog(title="Choose file",action=gtk.FILE_CHOOSER_ACTION_OPEN,\
                      buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        chooser.show()
        chooser.set_default_response(gtk.RESPONSE_OK)

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            self.apply_changes(chooser, chooser.get_filename, property)
            widget.set_label(chooser.get_filename())
            print chooser.get_filename(), 'selected'
        elif response == gtk.RESPONSE_CANCEL:
            print 'Closed, no files selected'
        chooser.destroy()

    def add_controller(self, widget):
        self.properties_container.add(widget)

    def add_element_widget(self, element):
        print "Adding widgets for element %s" %element.name
        widget = self._create_element_widget(element)
        self.add_controller(widget)
       
    def add_video_texture(self, pipeline, elt_name):
        print "Will embed video when implemented"

    def apply_changes(self, widget, state_getter, property):
        print "Applying value %s to property '%s' of element %s" %(state_getter(), property.name, property.parent_element.name)
        # Dirty hack for non-live-changeable parameters
        if property.name == "bitrate" and property.parent_element.name == "theoraenc":
            self.stop()
        property.parent_element.set_property(property.name, state_getter())
        if property.name == "bitrate" and property.parent_element.name == "theoraenc":
            self.pipeline_launcher.run()
        gobject.idle_add(property.update_value)
        #gobject.timeout_add(500, property.update_value)
