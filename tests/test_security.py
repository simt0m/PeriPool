from tests.conftest import login


def test_csrf_blocks_post_without_token(csrf_client, csrf_seeded_data):
    """Test that a POST without a CSRF token is rejected."""
    response = csrf_client.post(
        '/login',
        data={
            'email': csrf_seeded_data['employee_email'],
            'password': 'EmployeePass123!',
        },
    )

    assert response.status_code == 400
    assert b'Security check failed' in response.data


def test_csrf_allows_post_with_valid_token(csrf_client, csrf_seeded_data):
    """Test that a POST with a valid CSRF token succeeds, proving the fixture works."""
    response = login(csrf_client, csrf_seeded_data['employee_email'], 'EmployeePass123!')

    assert response.status_code == 200
    assert b'You have been logged in' in response.data


def test_login_rejects_sql_injection_payload(client, seeded_data):
    """Test that a SQL injection style payload is handled as a normal failed login."""
    response = login(client, "' OR '1'='1' --", 'anything')

    assert response.status_code == 200
    assert b'Invalid email or password' in response.data


def test_xss_payload_is_escaped_in_output(client, seeded_data):
    """Test that a script tag submitted as input is rendered escaped, not executed."""
    login(client, seeded_data['admin_email'], 'AdminPass123!')

    payload = '<script>alert(1)</script>'

    response = client.post(
        '/admin/categories/new',
        data={'name': payload, 'description': 'test'},
        follow_redirects=True
    )

    assert response.status_code == 200
    assert payload.encode() not in response.data
    assert b'&lt;script&gt;alert(1)&lt;/script&gt;' in response.data


def test_rate_limiting_blocks_repeated_login_attempts(app, client):
    """Test that repeated failed logins eventually trigger the rate limiter."""
    app.config['LOGIN_RATE_LIMIT'] = '3 per minute'

    statuses = [
        login(client, 'nobody@example.com', 'wrong-password').status_code
        for _ in range(10)
    ]

    assert 429 in statuses


def test_admin_routes_reject_non_admin_user(client, seeded_data):
    """Test that every admin mutation route rejects a logged-in non-admin user."""
    login(client, seeded_data['employee_email'], 'EmployeePass123!')

    admin_routes = [
        '/admin/categories/new',
        f'/admin/categories/{seeded_data["category_id"]}/edit',
        '/admin/item-models/new',
        f'/admin/item-models/{seeded_data["item_model_id"]}/edit',
        f'/admin/item-models/{seeded_data["item_model_id"]}/deactivate',
        '/admin/item-units/new',
        f'/admin/item-units/{seeded_data["item_unit_id"]}/edit',
        f'/admin/item-units/{seeded_data["item_unit_id"]}/delete',
        f'/admin/users/{seeded_data["admin_id"]}/toggle-active',
    ]

    for url in admin_routes:
        response = client.post(url, data={})
        assert response.status_code == 403, f'{url} did not return 403'


def test_security_headers_present(client):
    """Test that Talisman's security headers are present on a normal response."""
    response = client.get('/')

    assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'
    assert 'Content-Security-Policy' in response.headers
