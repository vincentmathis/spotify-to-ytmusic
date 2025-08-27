class TransferSession:
    def __init__(self, gen):
        self.gen = gen
        self.stopped = False

    def step(self, choice=None):
        """Advance generator, optionally sending a choice back."""
        try:
            if choice is None:
                return next(self.gen)
            else:
                return self.gen.send(choice)
        except StopIteration:
            self.stopped = True
            return None

    async def run(self, callback):
        """Run generator, calling callback for each event."""
        event = self.step()
        while event and not self.stopped:
            await callback(event)
            if event.event == "choice_required":
                # pause: UI must call .step(choice) later
                return
            event = self.step()
