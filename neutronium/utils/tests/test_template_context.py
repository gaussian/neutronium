
import pytest

from neutron.utils.template_context import (
    extract_template_variables_full,
    generate_fake_value,
    build_nested_context,
    TEMPLATE_BUILTINS,
    FRAMEWORK_VARS,
)


class TestExtractTemplateVariablesFull:
    """Tests for extract_template_variables_full function."""

    def test_simple_variable(self):
        template = "Hello {{ name }}"
        result = extract_template_variables_full(template)
        assert "name" in result
        assert result["name"] is None  # scalar

    def test_dotted_variable(self):
        template = "Hello {{ user.email }}"
        result = extract_template_variables_full(template)
        assert "user.email" in result
        assert result["user.email"] is None

    def test_multiple_variables(self):
        template = "{{ user.name }} - {{ order.total }}"
        result = extract_template_variables_full(template)
        assert "user.name" in result
        assert "order.total" in result

    def test_array_index(self):
        template = "First item: {{ items.0.name }}"
        result = extract_template_variables_full(template)
        assert "items.0.name" in result

    def test_deeply_nested(self):
        template = "{{ order.customer.address.city }}"
        result = extract_template_variables_full(template)
        assert "order.customer.address.city" in result

    def test_filters_out_builtins(self):
        template = "{% if condition %}{{ name }}{% endif %}"
        result = extract_template_variables_full(template)
        assert "if" not in result
        assert "endif" not in result
        assert "name" in result

    def test_filters_out_forloop(self):
        template = "{% for item in items %}{{ forloop.counter }}{% endfor %}"
        result = extract_template_variables_full(template)
        assert "forloop" not in result
        assert "forloop.counter" not in result

    def test_for_loop_variable(self):
        template = "{% for item in items %}{{ item.name }}{% endfor %}"
        result = extract_template_variables_full(template)
        assert "items" in result
        assert result["items"] == "list"  # list iteration
        # Loop variable is resolved to its source path
        assert "items.0.name" in result

    def test_for_loop_nested_variable(self):
        template = "{% for record in section_data.records %}{{ record.name }}{% endfor %}"
        result = extract_template_variables_full(template)
        assert "section_data.records" in result
        assert result["section_data.records"] == "list"
        # Loop variable is resolved to its source path
        assert "section_data.records.0.name" in result

    def test_for_loop_dict_items(self):
        """For loops using .items() - capture the dict path with 'items' iteration type."""
        template = "{% for group_name, records in section_data.groupings.items %}{{ group_name }}{% endfor %}"
        result = extract_template_variables_full(template)
        assert "section_data.groupings" in result
        assert result["section_data.groupings"] == "items"
        # Should NOT have the .items suffix as a separate key
        assert "section_data.groupings.items" not in result

    def test_for_loop_dict_values(self):
        template = "{% for value in data.values %}{{ value }}{% endfor %}"
        result = extract_template_variables_full(template)
        assert "data" in result
        assert result["data"] == "values"

    def test_for_loop_dict_keys(self):
        template = "{% for key in config.keys %}{{ key }}{% endfor %}"
        result = extract_template_variables_full(template)
        assert "config" in result
        assert result["config"] == "keys"

    def test_with_whitespace(self):
        template = "{{   user.email   }}"
        result = extract_template_variables_full(template)
        assert "user.email" in result

    def test_empty_template(self):
        template = "No variables here"
        result = extract_template_variables_full(template)
        assert result == {}

    def test_mixed_content(self):
        template = """
        {% extends "base.html" %}
        {% block content %}
        Hello {{ user.name }}, your order {{ order.id }} is ready.
        Items: {% for item in items %}{{ item.name }}{% endfor %}
        {% endblock %}
        """
        result = extract_template_variables_full(template)
        assert "user.name" in result
        assert "order.id" in result
        # Loop variable is resolved to its source path
        assert "items.0.name" in result
        assert "items" in result
        assert result["items"] == "list"
        # Builtins should not be in result
        assert "block" not in result
        assert "for" not in result


class TestGenerateFakeValue:
    """Tests for generate_fake_value function."""

    def test_url_pattern(self):
        assert "https://" in generate_fake_value("password_reset_url")
        assert "https://" in generate_fake_value("activate_url")
        assert "https://" in generate_fake_value("order.confirmation_url")

    def test_email_patterns(self):
        assert "@" in generate_fake_value("user.email")
        assert generate_fake_value("deleted_email") == "deleted@example.com"
        assert generate_fake_value("from_email") == "old@example.com"
        assert generate_fake_value("to_email") == "new@example.com"

    def test_code_pattern(self):
        assert generate_fake_value("code") == "123456"
        assert generate_fake_value("verification.code") == "123456"

    def test_name_pattern(self):
        assert "Name" in generate_fake_value("product.name")
        assert generate_fake_value("user_display") == "Test User"

    def test_domain_pattern(self):
        assert generate_fake_value("site_domain") == "example.com"
        assert generate_fake_value("domain") == "example.com"

    def test_content_patterns(self):
        assert generate_fake_value("subject") == "Test Subject"
        assert "body" in generate_fake_value("body").lower()
        assert generate_fake_value("custom_body") == "Custom message content here."

    def test_id_pattern(self):
        assert generate_fake_value("order_id") == "12345"
        assert generate_fake_value("user.id") == "12345"

    def test_default_pattern(self):
        result = generate_fake_value("some_random_field")
        assert result == "sample_some_random_field"

    def test_items_iteration_type(self):
        """Test that 'items' iteration type generates a dict structure."""
        result = generate_fake_value("groupings", iteration_type="items")
        assert isinstance(result, dict)
        assert "Sample Group" in result

    def test_list_iteration_type(self):
        """Test that 'list' iteration type generates a list structure."""
        result = generate_fake_value("records", iteration_type="list")
        assert isinstance(result, list)


class TestBuildNestedContext:
    """Tests for build_nested_context function."""

    def test_simple_variable(self):
        result = build_nested_context({"simple_var": None})
        assert result == {"simple_var": "sample_simple_var"}

    def test_dotted_path(self):
        result = build_nested_context({"referral.code": None})
        assert result == {"referral": {"code": "123456"}}

    def test_array_index(self):
        result = build_nested_context({"items.0.name": None})
        assert result == {"items": [{"name": "Sample Name"}]}

    def test_multiple_array_indices(self):
        result = build_nested_context({"items.0.name": None, "items.1.name": None})
        assert result == {"items": [{"name": "Sample Name"}, {"name": "Sample Name"}]}

    def test_deeply_nested(self):
        result = build_nested_context({"order.customer.address.city": None})
        assert result == {"order": {"customer": {"address": {"city": "sample_city"}}}}

    def test_skips_framework_vars(self):
        result = build_nested_context(
            {"user.email": None, "username": None, "email": None, "other_var": None}
        )
        # Framework vars should be skipped
        assert "user" not in result
        assert "username" not in result
        assert "email" not in result
        # Other vars should be present
        assert "other_var" in result

    def test_mixed_paths(self):
        result = build_nested_context(
            {
                "simple": None,
                "nested.value": None,
                "array.0.item": None,
                "deep.nested.path.value": None,
            }
        )
        assert "simple" in result
        assert result["nested"] == {"value": "sample_value"}
        assert result["array"] == [{"item": "sample_item"}]
        assert result["deep"]["nested"]["path"]["value"] == "sample_value"

    def test_empty_dict(self):
        result = build_nested_context({})
        assert result == {}

    def test_only_framework_vars(self):
        result = build_nested_context(
            {"user": None, "username": None, "email": None, "user.name": None}
        )
        assert result == {}

    def test_deterministic_output(self):
        """Output should be the same regardless of dict iteration order."""
        paths = {"z_var": None, "a_var": None, "m_var": None}
        result1 = build_nested_context(paths)
        result2 = build_nested_context(paths)
        assert result1 == result2

    def test_array_at_root(self):
        """Test array index directly at value position."""
        result = build_nested_context({"codes.0": None})
        assert "codes" in result
        assert isinstance(result["codes"], list)
        assert len(result["codes"]) == 1
        assert isinstance(result["codes"][0], str)

    def test_nested_arrays(self):
        """Test nested array structures."""
        result = build_nested_context({"matrix.0.0": None})
        assert "matrix" in result
        assert isinstance(result["matrix"], list)

    def test_dict_iteration_type(self):
        """Test that 'items' iteration type creates dict structure."""
        result = build_nested_context({"section_data.groupings": "items"})
        assert "section_data" in result
        assert "groupings" in result["section_data"]
        assert isinstance(result["section_data"]["groupings"], dict)

    def test_list_iteration_type(self):
        """Test that 'list' iteration type creates list structure."""
        result = build_nested_context({"records": "list"})
        assert "records" in result
        assert isinstance(result["records"], list)


class TestTemplateContextIntegration:
    """Integration tests combining multiple functions."""

    def test_extract_and_build(self):
        template = """
        Hello {{ customer.name }},
        Your order #{{ order.id }} contains:
        {% for item in order.items %}
        - {{ item.name }}: ${{ item.price }}
        {% endfor %}
        Total: ${{ order.total }}
        """
        variables = extract_template_variables_full(template)
        context = build_nested_context(variables)

        # Should have nested structures
        assert "customer" in context
        assert "name" in context["customer"]
        assert "order" in context
        assert "id" in context["order"]
        assert "total" in context["order"]
        # order.items should be a list (for loop iteration on property named "items")
        assert "items" in context["order"]
        assert isinstance(context["order"]["items"], list)
        # item is a loop variable - it gets resolved to order.items.0, NOT to top-level "item"
        assert "item" not in context
        # The item's properties should be in the list
        assert "name" in context["order"]["items"][0]
        assert "price" in context["order"]["items"][0]

    def test_real_world_email_template(self):
        template = """
        {% extends "emails/base.html" %}
        {% block content %}
        Hi {{ user.first_name }},

        Your password reset code is: {{ code }}

        Or click here: {{ password_reset_url }}

        Thanks,
        {{ site_domain }}
        {% endblock %}
        """
        variables = extract_template_variables_full(template)
        context = build_nested_context(variables)

        # user.first_name should be skipped (user is framework var)
        assert "user" not in context
        # code should have a fake value
        assert context.get("code") == "123456"
        # password_reset_url should have a URL
        assert "https://" in context.get("password_reset_url", "")
        # site_domain should be skipped (framework var)
        assert "site_domain" not in context

    def test_dict_items_iteration(self):
        """Test template with dict .items() iteration."""
        template = """
        {% for group_name, records in section_data.groupings.items %}
            <li><strong>{{ group_name }}</strong></li>
            {% for record in records %}
                <li>{{ record.name }}</li>
            {% endfor %}
        {% endfor %}
        """
        variables = extract_template_variables_full(template)
        context = build_nested_context(variables)

        # section_data.groupings should be a dict (items iteration)
        assert "section_data" in context
        assert "groupings" in context["section_data"]
        assert isinstance(context["section_data"]["groupings"], dict)

    def test_nested_dict_items_iteration(self):
        """Test template with nested dict .items() iterations."""
        template = """
        {% for section_type, section_data in record_data.sections.items %}
            {{ section_data.name }}
            {% for group_name, records in section_data.groupings.items %}
                {% for record in records %}
                    {{ record.body }} {{ record.name }}
                {% endfor %}
            {% endfor %}
        {% endfor %}
        """
        variables = extract_template_variables_full(template)

        # Check extraction
        assert "record_data.sections" in variables
        assert variables["record_data.sections"] == "items"
        assert "record_data.sections.0.groupings" in variables
        assert variables["record_data.sections.0.groupings"] == "items"

        context = build_nested_context(variables)

        # Check nested structure
        assert "record_data" in context
        sections = context["record_data"]["sections"]
        assert isinstance(sections, dict)
        assert "Sample Section 1" in sections

        # sections VALUE is a dict (we access .name and .groupings on it)
        section = sections["Sample Section 1"]
        assert isinstance(section, dict), "dict value should be dict when properties are accessed"
        assert "name" in section
        assert "groupings" in section
        assert isinstance(section["groupings"], dict)

        # groupings VALUE is a list (we iterate: {% for record in records %})
        records = section["groupings"]["Sample Grouping 1"]
        assert isinstance(records, list), "groupings value should be list because it's iterated"
        assert "body" in records[0]
        assert "name" in records[0]

    def test_with_variable_resolution(self):
        """Test that {% with %} variables are resolved correctly."""
        template = """
        {% for record in records %}
            {% if record.admin_users %}
            {% with admin=record.admin_users.0.user %}
                {{ admin.first_name }}
            {% endwith %}
            {% endif %}
        {% endfor %}
        """
        variables = extract_template_variables_full(template)
        context = build_nested_context(variables)

        # records should be a list with admin_users structure
        assert "records" in context
        assert isinstance(context["records"], list)

        record = context["records"][0]
        assert "admin_users" in record
        assert isinstance(record["admin_users"], list)
        assert "user" in record["admin_users"][0]
        assert "first_name" in record["admin_users"][0]["user"]

    def test_deep_nested_property_access(self):
        """Test deeply nested property access through loop and with variables."""
        template = """
        {% for item in items %}
            {% with nested=item.deep.path.here %}
                {{ nested.value }}
            {% endwith %}
        {% endfor %}
        """
        variables = extract_template_variables_full(template)
        context = build_nested_context(variables)

        # items should be a list with deep nested structure
        assert "items" in context
        item = context["items"][0]
        assert "deep" in item
        assert "path" in item["deep"]
        assert "here" in item["deep"]["path"]
        assert "value" in item["deep"]["path"]["here"]

    def test_items_with_property_access_generates_dict_value(self):
        """Test .items where value is accessed with properties generates dict[str, dict]."""
        template = """
        {% for record_type, record_data in record_groups.items %}
            <h2>{{ record_data.name }}</h2>
            {% for section_type, section_data in record_data.sections.items %}
                {{ section_data.title }}
            {% endfor %}
        {% endfor %}
        """
        variables = extract_template_variables_full(template)
        context = build_nested_context(variables)

        # record_groups should be dict (because .items)
        assert "record_groups" in context
        record_groups = context["record_groups"]
        assert isinstance(record_groups, dict)
        assert "Sample Record Group 1" in record_groups

        # record_data (the dict value) should be dict, NOT list
        # because we access .name and .sections (property access, not iteration)
        record_data = record_groups["Sample Record Group 1"]
        assert isinstance(
            record_data, dict
        ), "dict value should be dict when properties are accessed"
        assert "name" in record_data
        assert "sections" in record_data

    def test_items_with_iteration_generates_list_value(self):
        """Test .items where value is iterated generates dict[str, list]."""
        template = """
        {% for group_name, records in section_data.groupings.items %}
            <li><strong>{{ group_name }}</strong></li>
            {% for record in records %}
                <li>{{ record.name }}</li>
            {% endfor %}
        {% endfor %}
        """
        variables = extract_template_variables_full(template)
        context = build_nested_context(variables)

        # section_data.groupings should be dict (because .items)
        assert "section_data" in context
        groupings = context["section_data"]["groupings"]
        assert isinstance(groupings, dict)
        assert "Sample Grouping 1" in groupings

        # The value (records) should be a list because we iterate over it
        records = groupings["Sample Grouping 1"]
        assert isinstance(records, list), "dict value should be list when iterated"
        assert len(records) > 0
        assert "name" in records[0]

    def test_triple_nested_loops_with_deep_properties(self):
        """Test three levels of nested loops with deeply nested property access."""
        template = """
        {% for industry in industries %}
        <h2>{{ industry.name }}</h2>
        {% for trackable in industry.recent_top_trackables %}
        <p><strong>{{ trackable.name }}</strong> score: {{ trackable.score }}</p>
        {% for mention in trackable.top_mentions %}
        <p>{{ mention.text }} {{ mention.document_piece.sentiment_compound }}
        <a href="{{ mention.document_piece.document.url }}">{{ mention.document_piece.document.pretty_url }}</a></p>
        {% endfor %}
        {% endfor %}
        {% endfor %}
        """
        variables = extract_template_variables_full(template)
        context = build_nested_context(variables)

        # Check top-level structure
        assert "industries" in context
        assert isinstance(context["industries"], list)
        assert len(context["industries"]) >= 1

        industry = context["industries"][0]
        assert "name" in industry
        assert "recent_top_trackables" in industry
        assert isinstance(industry["recent_top_trackables"], list)

        trackable = industry["recent_top_trackables"][0]
        assert "name" in trackable
        assert "score" in trackable
        assert "top_mentions" in trackable
        assert isinstance(trackable["top_mentions"], list)

        # Critical: top_mentions items should have nested properties
        mention = trackable["top_mentions"][0]
        assert "text" in mention, "mention should have 'text' property"
        assert (
            "document_piece" in mention
        ), "mention should have 'document_piece' property"
        assert isinstance(mention["document_piece"], dict)
        assert "sentiment_compound" in mention["document_piece"]
        assert "document" in mention["document_piece"]
        assert "url" in mention["document_piece"]["document"]
        assert "pretty_url" in mention["document_piece"]["document"]

    def test_nested_loops_properties_not_empty(self):
        """Regression test: inner loop items should not be empty dicts."""
        template = """
        {% for group in groups %}
        {% for item in group.items %}
        {{ item.name }} {{ item.details.value }}
        {% endfor %}
        {% endfor %}
        """
        variables = extract_template_variables_full(template)
        context = build_nested_context(variables)

        assert "groups" in context
        group = context["groups"][0]
        assert "items" in group
        assert isinstance(group["items"], list)

        item = group["items"][0]
        assert item != {}, "inner loop item should not be empty"
        assert "name" in item
        assert "details" in item
        assert "value" in item["details"]

    def test_same_loop_variable_name_in_different_scopes(self):
        """Test that same loop variable name in different scopes resolves correctly."""
        template = """
        {% for item in outer_list %}
        {{ item.outer_prop }}
        {% endfor %}

        {% for item in inner_list %}
        {{ item.inner_prop }}
        {% endfor %}
        """
        variables = extract_template_variables_full(template)
        context = build_nested_context(variables)

        # Both should have their respective properties
        assert "outer_list" in context
        assert "inner_list" in context
        assert "outer_prop" in context["outer_list"][0]
        assert "inner_prop" in context["inner_list"][0]
        # Cross-contamination should NOT happen
        assert "inner_prop" not in context["outer_list"][0]
        assert "outer_prop" not in context["inner_list"][0]

    def test_same_variable_in_nested_and_sibling_loops(self):
        """Test realistic case: 'mention' used in multiple places like actual template."""
        template = """
        {% for industry in industries %}
        <h2>{{ industry.name }}</h2>
        {% for trackable in industry.recent_top_trackables %}
        <p>{{ trackable.name }}</p>
        {% for mention in trackable.top_mentions %}
        <p>{{ mention.text }} {{ mention.document_piece.sentiment }}</p>
        {% endfor %}
        {% endfor %}
        {% endfor %}

        {% for user_trackable in user_trackables %}
        <p>{{ user_trackable.trackable.name }}</p>
        {% for mention in user_trackable.mentions %}
        <p>{{ mention.document_piece.text }}</p>
        {% endfor %}
        {% endfor %}
        """
        variables = extract_template_variables_full(template)
        context = build_nested_context(variables)

        # Check industries structure
        assert "industries" in context
        industry = context["industries"][0]
        assert "name" in industry
        trackable = industry["recent_top_trackables"][0]
        assert "name" in trackable
        assert "top_mentions" in trackable

        # Critical: top_mentions should have properties from FIRST mention loop
        mention1 = trackable["top_mentions"][0]
        assert "text" in mention1, "top_mentions should have 'text' property"
        assert "document_piece" in mention1
        assert "sentiment" in mention1["document_piece"]

        # Check user_trackables structure
        assert "user_trackables" in context
        user_trackable = context["user_trackables"][0]
        assert "trackable" in user_trackable
        assert "mentions" in user_trackable

        # user_trackable.mentions should have properties from SECOND mention loop
        mention2 = user_trackable["mentions"][0]
        assert "document_piece" in mention2
        assert "text" in mention2["document_piece"]

        # Cross-contamination should NOT happen
        assert (
            "text" not in mention2
        ), "user_trackable.mentions should NOT have top-level 'text'"
