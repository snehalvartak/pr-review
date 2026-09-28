def test_export_requires_admin(client, user_token):
    resp = client.get("/admin/export", headers={"Authorization": user_token})
    assert resp.status_code == 403


def test_export_as_admin(client, admin_token):
    resp = client.get("/admin/export", headers={"Authorization": admin_token})
    assert resp.status_code == 200
