from time import strftime

from boardgamegeek import BoardGameGeekAPIError


def retry_if_attribute_error(exception):
    """Return True if we should retry (in this case when it's an IOError), False otherwise"""
    print("             {} - URL timed out, so I'm going to retry."
          .format(strftime('%d %b, %H:%M:%S')))
    if isinstance(exception, AttributeError) or isinstance(exception, BoardGameGeekAPIError):
        return True
    else:
        print("             Encountered a new error: {}".format(exception))
        return False
