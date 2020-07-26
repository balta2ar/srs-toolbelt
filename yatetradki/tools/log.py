import logging


def get_logger(name):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s (%(name)s) %(message)s",
        handlers=[
            logging.FileHandler("/var/log/srs-toolbelt.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(name)
    return logger
