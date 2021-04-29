if __name__ == "__main__":
    from setuptools import setup, find_packages

    pkj_name = 'django_cache'

    setup(
        name='django-ib-cache',
        version='0.0.3',
        long_description_content_type='text/x-rst',
        packages=[pkj_name] + [pkj_name + '.' + x for x in find_packages(pkj_name)],
        include_package_data=True,
    )
