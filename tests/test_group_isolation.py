def test_member_is_scoped_to_treasurer_group(client):
    a={'full_name':'A','email':'a@example.com','password':'StrongPass123!','group_name':'Group A','weekly_contribution':50}
    b={'full_name':'B','email':'b@example.com','password':'StrongPass123!','group_name':'Group B','weekly_contribution':50}
    ra=(client.post('/api/v1/auth/signup',json=a)).json(); rb=(client.post('/api/v1/auth/signup',json=b)).json()
    headers={'Authorization':f"Bearer {ra['tokens']['access_token']}"}
    r=client.post('/api/v1/users/members',headers=headers,json={'full_name':'Member A','email':'membera@example.com','temporary_password':'TempPass123!'})
    assert r.status_code==200
    headers_b={'Authorization':f"Bearer {rb['tokens']['access_token']}"}
    members=(client.get('/api/v1/users/members',headers=headers_b)).json(); assert members['total']==0
