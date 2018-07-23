class Console:
    def colorize(self, text, color):
        if type(text) == bytes:
            text = text.decode()
        return "\033[{0}m{1}\033[{2}m".format(color[0], text, color[1])

    def green(self, text):
        return self.colorize(text, (92, 0))

    def red(self, text):
        return self.colorize(text, (91, 0))

    def yellow(self, text):
        return self.colorize(text, (93, 0))

    def white(self, text):
        return self.colorize(text, (97, 0))
