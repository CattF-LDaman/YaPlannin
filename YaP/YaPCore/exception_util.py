import traceback

def get_traceback(e):
    return ''.join(traceback.format_exception(e, value=e ,tb=e.__traceback__))