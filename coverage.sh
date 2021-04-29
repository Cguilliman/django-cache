#coverage erase
coverage run -m django test --settings=django_cache.tests.settings django_cache.tests
coverage combine
coverage report
#coverage xml
coverage html