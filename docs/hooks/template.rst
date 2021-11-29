``example_example`` - Action
----------------------------------------

------------

Keyword Arguments
~~~~~~~~~~~~~~~~~

template_environment
    The jinja Environment object used to render all templates for ufotest


Description
~~~~~~~~~~~

This hook gets executed right at the end of the "prepare" method of the config singleton, which also initializes the
script manager and the plugin manager. The single argument is a reference to the template_environment which is used
to render all the HTML and other templates.

This hook is especially useful for two things:

- Adding global variables, which can be accessed from within any jinja template by adding entries to the
  ``template_environment.globals`` dict.
- Adding custom template filter by adding entries to the ``template_environment.filters`` dict

Example
~~~~~~~

.. code-block:: python

    import copy
    import random
    from ufotest.hooks import Action

    # Function implementing a custom filter which will randomly shuffle a string
    def shuffle(value):
        new_value = copy.deepcopy(value)
        random.shuffle(new_value)
        return new_value

    @Action('modify_template_environment')
    def modify_template_environment(template_environment):
        # Adding a custom global variable
        template_environment.globals['string'] = 'Hello World!'
        # Adding a custom filter
        template_environment.filters['shuffle'] = shuffle


.. code-block:: html

    {% block custom %}
        <!-- Will insert a shuffled "Hello World!" string -->
        <div>
            {{ string | shuffle }}
        </div>
    {% endblock %}
