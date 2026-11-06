import unittest,tempfile,sys,os,time,threading,json,urllib.request,urllib.error,http.cookiejar
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server,features as f
class Workflows(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();server.DB=self.tmp.name+'/test.db';server.init()
  self.manager={'id':'manager','name':'Management','groups':['management'],'allowlisted':False,'linked':True}
  self.player={'id':'123456789012345678','name':'Player','groups':['nonallowlisted'],'allowlisted':False,'linked':True}
  with server.conn() as c:c.execute('INSERT INTO members VALUES(?,?,?,?,0,1,?)',(self.player['id'],self.player['id'],'Player',json.dumps(['nonallowlisted']),int(time.time())))
  self.reviewer={'id':'reviewer','name':'Reviewer','groups':['reviewer'],'allowlisted':False,'linked':True}
 def tearDown(self):self.tmp.cleanup()
 def create(self,kind,data,u=None):return f.mutate(u or self.manager,'/api/create',{'kind':kind,'data':data})['id']
 def update(self,id,action,u=None,**kw):return f.mutate(u or self.manager,'/api/update',{'id':id,'action':action,**kw})
 def test_closed_ticket_and_notes_isolation(self):
  id=self.create('ticket',{'title':'Help','category':'General support','text':'Please help','owner':'forged','id':999},self.player)
  self.assertEqual(f.find(id)['owner'],self.player['id']);self.update(id,'note',text='Secret');self.update(id,'status',status='Resolved')
  with self.assertRaises(ValueError):self.update(id,'reply',self.player,text='Reopen')
  with self.assertRaises(ValueError):self.update(id,'evidence',self.player,url='https://example.com',label='Proof')
  self.assertNotIn('notes',f.view(self.player)['records'][0])
 def test_reviewer_and_combined_permissions(self):
  self.assertNotIn('tickets.view',server.permissions(self.reviewer))
  self.assertIn('tickets.view',server.permissions({**self.reviewer,'groups':['reviewer','support']}))
  with self.assertRaises(PermissionError):self.create('case',{'title':'No'},self.reviewer)
 def test_forms_attempts_approval_role_removal(self):
  questions=server.settings()['forms']['Allowlist']['questions'];self.assertEqual(len(questions),18)
  answers=['Yes' if q['type']=='ack' else 'A'*10000 for q in questions]
  id=self.create('application',{'type':'Allowlist','answers':answers},self.player);self.update(id,'decision',self.reviewer,status='Rejected',reason='Elaborate')
  id=self.create('application',{'type':'Allowlist','answers':answers},self.player);r=f.find(id);self.assertEqual(r['attempts'],1);self.assertEqual(r['lastRejection'],'Elaborate')
  self.update(id,'decision',self.reviewer,status='Accepted',reason='Welcome')
  self.assertEqual(f.eligibility(self.player,'Allowlist'),'Application Approved')
  f.track_membership(self.player['id'],True);f.track_membership(self.player['id'],False);self.assertEqual(f.eligibility(self.player,'Allowlist'),'')
 def test_closure_minimum_and_review_feedback(self):
  f.mutate(self.manager,'/api/availability',{'type':'Developer','open':False})
  with self.assertRaises(ValueError):self.create('application',{'type':'Developer','answers':['long']*4},self.player)
  f.mutate(self.manager,'/api/availability',{'type':'Developer','open':True})
  id=self.create('application',{'type':'Developer','answers':['answer']*4},self.player)
  with self.assertRaises(PermissionError):self.update(id,'decision',self.reviewer,status='Accepted')
  self.update(id,'feedback',index=0,text='Edited combined template',notify=True)
  self.assertEqual(f.find(id)['feedback'][0]['text'],'Edited combined template')
  with server.conn() as c:self.assertEqual(c.execute('SELECT count(*) FROM outbox').fetchone()[0],1)
 def test_cases_duplicates_and_outreach(self):
  t=self.create('ticket',{'title':'Report','category':'Player report','text':'Incident'},self.player);c=self.create('case',{'title':'Review'})
  self.update(c,'reports',ids=[t,t],relation='Duplicate');self.assertEqual(len(f.find(c)['reportLinks']),1)
  self.update(c,'player',discordId=self.player['id']);out=self.create('ticket',{'title':'Follow up','text':'Your account?','category':'Staff-to-player','target':self.player['id'],'caseId':c})
  self.assertTrue(any(l['id']==out for l in f.find(c)['reportLinks']));self.assertEqual(f.view(self.player)['records'][0]['kind'],'ticket')
  self.update(c,'unlink',reportId=t);self.assertFalse(any(l['id']==t for l in f.find(c)['reportLinks']))
 def test_appeal_dates_and_activity(self):
  b=self.create('ban',{'discordId':self.player['id'],'reason':'Rule break','appealAt':int(time.time())+1000})
  with self.assertRaises(ValueError):self.create('ticket',{'title':'Appeal','category':'Ban appeal','text':'Please review'},self.player)
  r=f.find(b);r['appealAt']=int(time.time())-1;f.save_record(r)
  t=self.create('ticket',{'title':'Appeal','category':'Ban appeal','text':'Please review'},self.player)
  self.update(t,'status',status='Resolved');self.update(t,'status',status='Open');self.update(t,'status',status='Resolved')
  self.assertEqual(f.view(self.manager)['completions'][0]['count'],1)
 def test_granular_settings_and_rules(self):
  self.assertGreater(len(server.settings()['rulesSections']),10)
  with self.assertRaises(PermissionError):f.mutate(self.reviewer,'/api/settings',{'changes':{'groups':{}}})
  self.assertEqual(len(server.settings()['responseTemplates']),13)
 def test_http_identity_and_unlink(self):
  http_server=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);threading.Thread(target=http_server.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(http_server.server_port)
  opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
  def request(path,body=None):
   data=json.dumps(body).encode() if body is not None else None
   with opener.open(urllib.request.Request(base+path,data=data,headers={'Content-Type':'application/json'})) as r:return json.load(r)
  try:
   request('/api/demo',{'group':'management'});self.assertIn('groups.edit',request('/api/session')['permissions'])
   request('/api/account/unlink',{});self.assertFalse(request('/api/session')['user']['linked'])
   with self.assertRaises(urllib.error.HTTPError):request('/api/create',{'kind':'ticket','data':{}})
  finally:http_server.shutdown();http_server.server_close()
if __name__=='__main__':unittest.main()
