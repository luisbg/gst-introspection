#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Very easy to use event-system
@author: Damien Boucard
"""
import logging
import gobject
logger = logging.getLogger('event')

try:
    from easycast.utils.event import EventManager
except ImportError:
    class EventManager:
        """ Manages the event-system.
        This class is instanciated on importing the module,
        so it is not needed to use it directly but via EventLaunch and EventListener.
        @cvar instance: The instance created on importing the module.
        @type instance: C{L{EventManager}}
        @ivar listeners: Dictionnary with keys of type C{str} representing a event type and with values of type C{list} representing a collection of C{EventListener}.
        @type listeners: C{dict<str, list<L{EventListener}>>}
        """
        def __init__(self):
            """ EventManager constructor. """
            EventManager.instance = self
            self.listeners = {}
            
        def addListener(self, obj, event_type):
            """ Add a listener to a specific event.
            @param obj: Listener to add.
            @type obj: C{L{EventListener}}
            @param event_type: Type of the event to listen.
            @type event_type: C{str}
            """
            if event_type in self.listeners:
                if obj not in self.listeners[event_type]:
                    self.listeners[event_type].append(obj)
            else:
                self.listeners[event_type] = [obj]
        
        def removeListener(self, obj, event_type):
            """ Remove a listener from a specific event.
            @param obj: Listener to remove.
            @type obj: C{L{EventListener}}
            @param event_type: Type of the event that was listening.
            @type event_type: C{str}
            """
            if event_type in self.listeners and obj in self.listeners[event_type]:
                self.listeners[event_type].remove(obj)
        
        def dispatchEvent(self, event):
            """ Dispatch a launched event to all affected listeners.
            @param event: Event launched.
            @type event: C{L{Event}}
            """
            if event.type in self.listeners:
                for obj in self.listeners[event.type]:
                    # Try to call event-specific handle method
                    fctname = obj.event_pattern %(event.type)
                    if hasattr(obj, fctname):
                        function = getattr(obj, fctname)
                        if callable(function):
                            gobject.idle_add(function, event)
                            continue
                        else:
                            logger.warning('Event-specific handler found but not callable')
                    # Try to call default handle method
                    if hasattr(obj, obj.event_default):
                        function = getattr(obj, obj.event_default)
                        if callable(function):
                            gobject.idle_add(function, event)
                            continue
                    # No handle method found, raise error ?
                    if not obj.event_silent:
                        raise UnhandledEventError("%s has no method to handle %s", obj, event)
            else:
                logger.error("Pas de event.type %s" % event.type)

EventManager()
    
class EventListener:
    """ Generic class for listening to events.
    
    It is just needed to herite from this class and register to events to listen easily events.
    It is also needed to write handler methods with event-specific and/or C{L{default}} function.
    
    Event-specific functions have name as the concatenation of the C{prefix} parameter + the listened event type + the C{suffix} parameter.
    
    If it does not exist, the default function is called as defined by the C{L{default}} parameter/attribute.
    
    If the event cannot be handled, a C{L{UnhandledEventError}} is raised, except if C{L{silent}} flag is C{True}.
    @ivar event_manager: The event manager instance.
    @type event_manager: C{L{EventManager}}
    @ivar event_pattern: Event-specific handler pattern.
    @type event_pattern: C{str}
    @ivar event_default: Default handler function name.
    @type event_default: C{str}
    @ivar silent: Silent flag. If C{False}, C{L{UnhandledEventError}} is raised if an event cannot be handled. If C{True}, do nothing, listener does not handle the event.
    @type silent: C{str}
    """
    def __init__(self, prefix="evt_", suffix="", default="eventPerformed", silent=False):
        """ EventListener constructor.
        @param prefix: Prefix for all event-specific handler function name.
        @type prefix: C{str}
        @param suffix: Suffix for all event-specific handler function name.
        @type suffix: C{str}
        @param default: Default handler function name.
        @type default: C{str}
        @param silent: Silent flag.
        @type silent: C{bool}
        """
        self.event_manager = EventManager.instance
        self.event_pattern = prefix + "%s" + suffix
        self.event_default = default
        self.event_silent = silent
        
    def registerEvent(self, event_type):
        """ Registers itself to a new event.
        @param event_type: Type of the event to listen.
        @type event_type: C{str}
        """
        self.event_manager.addListener(self, event_type)
        
    def unregisterEvent(self, event_type):
        """ Unregisters itself from a event.
        @param event_type: Type of the event which was listening.
        @type event_type: C{str}
        """
        self.event_manager.removeListener(self, event_type)


class EventLauncher:
    """ Generic class for launching events.
    It is just needed to herite from this class to launch easily events.
    @ivar event_manager: The event manager instance.
    @type event_manager: C{L{EventManager}}
    """
    def __init__(self):
        """ EventLauncher constructor. """
        self.event_manager = EventManager.instance
        
        
    def launchEvent(self, event_type, content=None):
        """ Launches a new event to the listeners.
        @param event_type: Type of the event to launch.
        @type event_type: C{str}
        @param content: Content to attach with the event (Optional).
        @type content: any
        """
        self.event_manager.dispatchEvent(Event(event_type, self, content))
    
    
class Event:
    """ Represents an event entity.
    @ivar type: Type of the event.
    @type type: C{str}
    @ivar source: Instance which launched the event.
    @type source: C{L{EventLauncher}}
    @ivar content: Content attached to the event (C{None} if none).
    @type content: any
    """
    def __init__(self, type, source, content):
        """ Event constructor.
        @param type: Type of the event.
        @type type: C{str}
        @param source: Instance which launched the event.
        @type source: C{L{EventLauncher}}
        @param content: Content attached to the event (C{None} if none).
        @type content: any
        """
        self.type = type
        self.source = source
        self.content = content
    
    def __str__(self):
        """ Converts object itself to string.
        @return: Object converted string.
        @rtype: C{str}
        """
        return "<%s.%s type=%s source=%s content=%s>" %(__name__, self.__class__.__name__, self.type, self.source, self.content)
    
    
class UnhandledEventError(AttributeError):
    """ Error raised when an event cannot be handled, except if C{L{silent<EventListener.silent>}} flag is C{True}. """
    pass
