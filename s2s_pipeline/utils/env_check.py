#util to chehck the environment, if hugging face we will use different code.
import os

def running_on_huggingface():
    return os.environ.get("SPACE_ID") is not None
