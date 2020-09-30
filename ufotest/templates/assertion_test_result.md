{% if exit_code %}
({{ error_count }}/{{ assertions|length }}) ASSERTIONS FAILED
{% for result, message in assertions %}
{% if detailed || not result %}
{{ message }}
{% endif %}
{% endfor %}
{% else %}
({{ assertions|length }}/{{ assertions|length }}) ASSERTIONS SUCCESSFUL
{% endif %}
