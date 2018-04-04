from .logging import Log


class EventConnector(Log):
    """ Abstract class which connects Qt event handlers to specifically named methods """

    def __init__(self):
        # initiate logging on events
        Log.trace(self)

    def connect(self) -> None:
        """ Automatically connect event handlers named as [attr/obj name]*__[event name]
            eg. window__save_btn__click"""

        events = [attribute for attribute in dir(self) if attribute.endswith('__event') and not attribute.startswith('_x_')]
        for event in events:
            parts = event.split('__')
            event_name = parts[-2].replace('_', ' ').title().replace(' ', '')
            py_event_name = parts[-2]
            qt_event_name = (event_name[0].lower() + event_name[1:])
            path = parts[:-2]

            # loop through path so we can have event handlers for child elements
            attr = self
            flag = False
            while path and not flag:
                try:
                    attr = getattr(attr, path[0])
                except AttributeError:
                    break
                path.pop(0)

            if flag:
                self._logger.error('event connector attribute not found - {0} of {1}'.format(path[0], event))
                continue

            try:
                qt_signal = getattr(attr, qt_event_name)
            except AttributeError:
                self._logger.error('event connector signal not found {0}, trying {1}'.format(qt_event_name, py_event_name))
                try:
                    qt_signal = getattr(attr, py_event_name)
                except AttributeError:
                    self._logger.error('event connector signal not found {0}'.format(py_event_name))
                    continue

            qt_signal.connect(getattr(self, event))

            self._logger.debug('connected {0} event to {1}'.format(qt_event_name, event))

