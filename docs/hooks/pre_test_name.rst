``pre_test_{test_name}`` - Action
----------------------------------

------------

Keyword Arguments
~~~~~~~~~~~~~~~~~

test_runner: TestRunner
    A reference to the TestRunner object which is about to execute the test

name: str
    The unique string name of the test case

Description
~~~~~~~~~~~

This hook is executed right before the execution of the test case :code:`name` is *attempted*. This means that
if a test case of that name does not exist for example, the hook is still invoked!

Note that this is a dynamic hook which is only triggered for the test case with the specific :code:`{test_name}`

Example
~~~~~~~

Tbd

