def split_args(splitter: str):
    def _split(items):
        return splitter.join(items)
    return _split


arguments_splitter = split_args("#")
arguments_group_splitter = split_args("@")
key_value_splitter = split_args("~")
value_splitter = split_args("|")


def kwargs_items(kwargs):
    for key in sorted(kwargs.keys()):
        if bool(kwargs.get(key)):
            value = kwargs.get(key)
            if isinstance(value, (list, tuple)):
                value = value_splitter(
                    (str(item) for item in sorted(value))
                )
            yield key_value_splitter((key, str(value)))


def keygen(*args, **kwargs) -> str:
    args_string = arguments_splitter((str(arg) for arg in sorted(args)))
    kwargs_string = arguments_splitter(kwargs_items(kwargs))
    return arguments_group_splitter((args_string, kwargs_string))
