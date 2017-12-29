class Listener:
    listeners = {"on_message": [],
                 "on_ready": [],
                 "on_loop": [],
		}

    @classmethod
    def update(cls, event, *args):
        for listener in cls.listeners[event]:
            listener(*args)

    @classmethod
    def register(cls, f, event):
        cls.listeners[event].append(f)
