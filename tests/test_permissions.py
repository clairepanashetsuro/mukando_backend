def test_member_cannot_record_contribution(client):
    payload={'full_name':'Treasurer','email':'t@example.com','password':'StrongPass123!','group_name':'G','weekly_contribution':100}
    auth=(client.post('/api/v1/auth/signup',json=payload)).json(); h={'Authorization':f"Bearer {auth['tokens']['access_token']}"}
    m=(client.post('/api/v1/users/members',headers=h,json={'full_name':'Member','email':'m@example.com','temporary_password':'TempPass123!'})).json()
    login=(client.post('/api/v1/auth/login',json={'email':'m@example.com','password':'TempPass123!'})).json(); mh={'Authorization':f"Bearer {login['tokens']['access_token']}"}
    r=client.post('/api/v1/contributions',headers=mh,json={'member_id':m['id'],'amount':100,'paid_at':'2026-09-20'}); assert r.status_code==403
