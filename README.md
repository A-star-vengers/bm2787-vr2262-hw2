# bm-2787-vr2262-hw2

With Python >= 3.5 and PostgreSQL >= 9.4 available, run these commands to start the web server. Replace `postgres` with your PostgreSQL user name (though `postgres` is usually the default user). Note that this will create a Python virtual environment in the `venv` directory. To activate the virtual environment manually, execute `$ source venv/bin/activate`

```
$ sudo -u postgres psql -c 'create database demo;'
$ ./run_local.sh
```

To run tests (with virtual environment `venv` activated):

- With coverage

  ```
  (venv) $ ./tests/tests_with_coverage.sh
  ```
- Without coverage

  ```
  (venv) $ python -m unittest discover tests
  ```
