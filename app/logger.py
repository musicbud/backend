import json
import logging

class CustomFormatter(logging.Formatter):
    green = "\x1b[1;32m"
    blue = "\x1b[0;34m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, json_logging=False, node_uuid="") -> None:
        super().__init__()
        self.json_logging = json_logging
        self.node_uuid = node_uuid

    def __get_console_format(self, level) -> list:
        header = f"[{self.node_uuid}:%(levelname)s:%(filename)s-%(lineno)d]"
        body = "*" + ": " + "%(message)s"

        if level == logging.DEBUG:
            return [self.green + header + self.reset + body, len(self.green)]
        elif level == logging.INFO:
            return [self.blue + header + self.reset + body, len(self.blue)]
        elif level == logging.WARNING:
            return [self.yellow + header + self.reset + body, len(self.yellow)]
        elif level == logging.ERROR:
            return [self.red + header + self.reset + body, len(self.red)]
        else:
            return [self.bold_red + header + self.reset + body, len(self.bold_red)]

    def format(self, record) -> str:
        if self.json_logging:
            log_record = {
                "node_uuid": self.node_uuid,
                "level": record.levelname,
                "filename": record.filename,
                "lineno": record.lineno,
            }

            message = record.getMessage()
            try:
                message_obj = json.loads(message)
                log_record.update(message_obj)
            except json.JSONDecodeError:
                log_record["msg"] = message

            return json.dumps(log_record)

        else:
            log_fmt = self.__get_console_format(record.levelno)
            formatter = logging.Formatter(log_fmt[0], datefmt="%Y-%m-%d %H:%M")
            msg = formatter.format(record)
            n = 35 - (len(msg) - len(record.getMessage())) - (10 - log_fmt[1])

            return msg.replace("*", " " * n)
