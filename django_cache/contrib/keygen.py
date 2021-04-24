
def keygen(*args, **kwargs) -> str:
    args_string = '#'.join([str(arg) for arg in sorted(args)])
    kwargs_string = '#'.join([
        f'{key}~{kwargs.get(key)}'
        for key in sorted(kwargs.keys())
        if bool(kwargs.get(key))
    ])
    return f"{args_string}@{kwargs_string}"
