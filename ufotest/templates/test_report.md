# Test Report {{ report.start }}

This is an automatically configured test report generated by the `UfoTest CLI`. The Tests were
started **{{ report.start }}**.

For further information on the `UfoTest CLI` visit the
[Github Repository](https://fuzzy.fzk.de/gogs/jonas.teufel/ufotest)
or the
[Documentation](https://ufotest.readthedocs.io/en/latest/)!

## Summary

Number of executed tests: **{{ report.test_count }}** <br>
Number of passing tests: **{{ report.successful_count }}** <br>
Number of errors: **{{ report.error_count }}**

Success Ratio: **{{ report.success_ratio * 100 }}**%

The following listing will provide an overview over which tests were passing and which have
failed. The symbol **O** denotes a success and the symbol **X** an error. For details about specific
test runs head down to the section *Individual Results*. There you can find the detailed output of every
test case.

{% for key, result in report.results.items() %}
{%- if result.passing -%}
**[O]** {{ key }}<br>
{%- else %}
**[X]** {{ key }}<br>
{% endif -%}
{% endfor %}

## Individual Results
{% for key, result in report.results.items() %}
### {{ key }}
{{ result.to_markdown() }}
{% endfor %}
