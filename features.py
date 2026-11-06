"""Extended workflows and server-enforced access policies."""
import json,time,secrets,os,re,urllib.request,urllib.parse,threading,sqlite3
PERMISSIONS=['tickets.view','tickets.reply','tickets.claim','tickets.assign','tickets.close','tickets.priority','tickets.notes','tickets.participants','cases.view','cases.edit','applications.allowlist','applications.other','applications.availability','forms.edit','categories.edit','rules.edit','branding.edit','groups.edit','users.view','users.notes','bans.view','bans.create','bans.revoke','server.kick','server.ban','audit.view','integrations.edit','accounts.manage']
GROUPS={'allowlisted':[],'nonallowlisted':[],'reviewer':['applications.allowlist','applications.availability'],'support':['tickets.view','tickets.reply','tickets.claim','tickets.close','tickets.notes','tickets.participants'],'admin':['tickets.view','tickets.reply','tickets.claim','tickets.assign','tickets.close','tickets.priority','tickets.notes','tickets.participants','cases.view','cases.edit','users.view','users.notes','bans.view','bans.create','bans.revoke','server.kick','server.ban','applications.availability'],'management':PERMISSIONS}
def install(m):
 global M
 M=m
 oldinit=m.init
 def init():
  oldinit()
  with m.conn() as c:
   c.executescript('''CREATE TABLE IF NOT EXISTS members(id TEXT PRIMARY KEY,discord TEXT UNIQUE,name TEXT,groups_json TEXT,allowlisted INTEGER DEFAULT 0,linked INTEGER DEFAULT 1,refreshed INTEGER DEFAULT 0); CREATE TABLE IF NOT EXISTS outbox(id INTEGER PRIMARY KEY,target TEXT,text TEXT,attempts INTEGER DEFAULT 0,next_at INTEGER DEFAULT 0,status TEXT DEFAULT 'pending'); CREATE TABLE IF NOT EXISTS oauth(state TEXT PRIMARY KEY,expires INTEGER,account TEXT,mode TEXT); CREATE TABLE IF NOT EXISTS completions(ticket INTEGER,actor TEXT,at INTEGER);''')
   s=m.settings()
   if s.get('version',0)<2:
    from defaults import FORMS,RULES,RESPONSE_TEMPLATES
    s.update(responseTemplates=RESPONSE_TEMPLATES,version=2,groups=GROUPS,forms=FORMS,rulesSections=RULES,rules='\n\n'.join(x['title']+'\n'+x['body'] for x in RULES),categories={k:{'template':v,'icon':'ticket'} for k,v in s['categories'].items()},secondary='#e591cf',signatureLogo='',applicationHistory=True)
    c.execute('UPDATE settings SET data=?',(json.dumps(s),))
  for r in m.records():
   if r['kind']=='ticket':r.setdefault('priority','Normal');r.setdefault('evidence',[]);r.setdefault('participants',[])
   if r['kind']=='case':r.setdefault('reportLinks',[{'id':i,'relation':'Related'} for i in r.get('reports',[])]);r.setdefault('players',[])
   if r['kind']=='application':
    r.setdefault('history',[])
    if r['status']=='Accepted':r.setdefault('approvedAt',r['created'])
   save_record(r)
 m.init=init
 m.permissions=lambda u:set(PERMISSIONS) if 'management'in u.get('groups',[]) else set(p for g in u.get('groups',[]) for p in m.settings()['groups'].get(g,[]))
 def current(self):
  u=oldsession(self)
  if not u:return None
  with m.conn() as c:r=c.execute('SELECT * FROM members WHERE id=?',(u['id'],)).fetchone()
  if not r:return None
  if not m.DEMO and r['linked'] and time.time()-r['refreshed']>60:
   try:
    member=m.discord('guilds/'+os.environ['DISCORD_GUILD_ID']+'/members/'+r['discord']);sync_member(r['id'],r['discord'],r['name'],member.get('roles',[]))
   except Exception:
    # Fail closed if membership/roles cannot be checked.
    return None
   with m.conn() as c:r=c.execute('SELECT * FROM members WHERE id=?',(u['id'],)).fetchone()
  return {'id':r['id'],'discordId':r['discord'],'name':r['name'],'groups':json.loads(r['groups_json']),'allowlisted':bool(r['allowlisted']),'linked':bool(r['linked'])}
 oldsession=m.Handler.session;m.Handler.session=current
 oldget=m.Handler.do_GET
 def get(self):
  path=urllib.parse.urlparse(self.path).path
  if path in ['/auth/discord','/auth/link']:
   u=self.session();mode='link' if path=='/auth/link' else 'login'
   if mode=='link' and not u:return self.output({'error':'Sign in to link an account'},401)
   if not os.getenv('DISCORD_CLIENT_ID'):return self.output({'error':'Discord OAuth not configured'},503)
   state=secrets.token_urlsafe(32)
   with m.conn() as c:c.execute('INSERT INTO oauth VALUES(?,?,?,?)',(state,int(time.time())+600,u['id'] if mode=='link' else None,mode))
   url='https://discord.com/oauth2/authorize?'+urllib.parse.urlencode({'client_id':os.environ['DISCORD_CLIENT_ID'],'redirect_uri':os.environ['PUBLIC_URL']+'/auth/callback','response_type':'code','scope':'identify guilds.members.read','state':state,'prompt':'consent'})
   self.send_response(302);self.send_header('Location',url);self.send_header('Set-Cookie','oauth_state='+state+'; HttpOnly; SameSite=Lax; Path=/; Max-Age=600');self.end_headers();return
  if path=='/auth/callback':
   try:
    from http.cookies import SimpleCookie
    import hmac
    q=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query);state=q['state'][0];cookies=SimpleCookie(self.headers.get('Cookie',''))
    if not hmac.compare_digest(cookies['oauth_state'].value,state):raise ValueError('Invalid state')
    with m.conn() as c:
     flow=c.execute('SELECT * FROM oauth WHERE state=? AND expires>?',(state,time.time())).fetchone();c.execute('DELETE FROM oauth WHERE state=?',(state,))
    if not flow:raise ValueError('Expired sign-in')
    if flow['mode']=='link':
     u=self.session()
     if not u or u['id']!=flow['account']:raise ValueError('Account-link session changed')
    body=urllib.parse.urlencode({'client_id':os.environ['DISCORD_CLIENT_ID'],'client_secret':os.environ['DISCORD_CLIENT_SECRET'],'grant_type':'authorization_code','code':q['code'][0],'redirect_uri':os.environ['PUBLIC_URL']+'/auth/callback'}).encode()
    with urllib.request.urlopen(urllib.request.Request('https://discord.com/api/oauth2/token',data=body),timeout=15) as response:token=json.load(response)['access_token']
    member=m.discord('users/@me/guilds/'+os.environ['DISCORD_GUILD_ID']+'/member',token='Bearer '+token);identity=m.discord('users/@me',token='Bearer '+token)
    with m.conn() as c:existing=c.execute('SELECT id FROM members WHERE discord=?',(identity['id'],)).fetchone()
    if flow['mode']=='link' and existing and existing['id']!=flow['account']:raise ValueError('Discord account already belongs to another profile; management review is required')
    uid=flow['account'] if flow['mode']=='link' else existing['id'] if existing else secrets.token_hex(16)
    sync_member(uid,identity['id'],identity['username'],member['roles']);m.audit({'id':uid},'account.'+flow['mode'],identity['id']);headers=self.login({'id':uid})
    self.send_response(302);self.send_header('Location','/')
    for k,v in headers.items():self.send_header(k,v)
    self.end_headers();return
   except Exception:return self.output({'error':'Discord login/link failed. Check membership, account ownership and configuration.'},401)
  if path.startswith('/api/'):
   u=self.session()
   if path=='/api/session':return self.output({'user':u,'demo':m.DEMO,'permissions':list(m.permissions(u)) if u else []})
   if not u:return self.output({'error':'Sign in required'},401)
   if path=='/api/data':return self.output(view(u))
   if path=='/api/bot-status':
    if not ('applications.allowlist' in m.permissions(u) or 'applications.other' in m.permissions(u) or 'integrations.edit' in m.permissions(u)):return self.output({'error':'Forbidden'},403)
    if not os.getenv('DISCORD_BOT_TOKEN'):return self.output({'state':'Not configured'})
    try:
     bot=m.discord('users/@me');return self.output({'state':'DM service online','name':bot['username']})
    except Exception:return self.output({'state':'DM service unreachable'})
   return self.output({'error':'Not found'},404)
  oldget(self)
 m.Handler.do_GET=get
 def post(self):
  origin=self.headers.get('Origin')
  if origin and urllib.parse.urlparse(origin).netloc!=self.headers.get('Host'):return self.output({'error':'Invalid origin'},403)
  size=int(self.headers.get('Content-Length','0'))
  if size>20_000_000:return self.output({'error':'Request too large'},413)
  d=json.loads(self.rfile.read(size) or '{}');path=self.path
  if path=='/api/demo':
   if not m.DEMO:return self.output({'error':'Demo disabled'},404)
   groups=d.get('groups',[d.get('group','nonallowlisted')]);groups=['nonallowlisted' if g=='player' else g for g in groups]
   if not groups or any(g not in m.settings()['groups'] for g in groups):raise ValueError('Invalid groups')
   uid=d.get('identity','demo-'+ '-'.join(sorted(groups)))
   if not re.fullmatch(r'demo-[A-Za-z0-9_-]{1,80}',uid):raise ValueError('Invalid demo identity')
   with m.conn() as c:c.execute('INSERT INTO members(id,discord,name,groups_json,allowlisted,linked,refreshed) VALUES(?,?,?,?,?,1,?) ON CONFLICT(id) DO UPDATE SET groups_json=excluded.groups_json,allowlisted=excluded.allowlisted,linked=1,refreshed=excluded.refreshed',(uid,uid,uid,json.dumps(groups),int('allowlisted'in groups),int(time.time())))
   track_membership(uid,'allowlisted'in groups)
   return self.output({'ok':True},headers=self.login({'id':uid}))
  if path=='/api/logout':return self.output({'ok':True},headers={'Set-Cookie':'session=; Max-Age=0; HttpOnly; SameSite=Lax; Path=/'})
  u=self.session()
  if not u:return self.output({'error':'Sign in required'},401)
  if path=='/api/account/unlink':
   with m.conn() as c:c.execute('UPDATE members SET discord=NULL,linked=0,groups_json=?,allowlisted=0 WHERE id=?',(json.dumps(['nonallowlisted']),u['id']))
   m.audit(u,'account.unlink',u['id']);return self.output({'ok':True})
  if not u['linked']:return self.output({'error':'Link Discord to continue'},403)
  try:result=mutate(u,path,d)
  except PermissionError as e:return self.output({'error':str(e)},403)
  return self.output(result)
 m.Handler.post=post

def sync_member(uid,discord,name,roles):
 s=M.settings();groups=['allowlisted' if s['allowlistRole'] in roles else 'nonallowlisted']+[g for g,ids in s['roleMappings'].items() if set(ids)&set(roles) and g in s['groups']]
 if os.getenv('BOOTSTRAP_MANAGEMENT_ROLE') in roles:groups.append('management')
 with M.conn() as c:c.execute('INSERT INTO members VALUES(?,?,?,?,?,1,?) ON CONFLICT(id) DO UPDATE SET discord=excluded.discord,name=excluded.name,groups_json=excluded.groups_json,allowlisted=excluded.allowlisted,linked=1,refreshed=excluded.refreshed',(uid,discord,name,json.dumps(groups),int('allowlisted'in groups),int(time.time())))
 track_membership(uid,'allowlisted'in groups)
def track_membership(uid,allowlisted):
 for r in M.records('application'):
  if r['owner']==uid and r['type']=='Allowlist' and r.get('approvedAt'):
   if allowlisted:r.update(roleSeen=True,roleRemoved=False)
   elif r.get('roleSeen'):r['roleRemoved']=True
   save_record(r)
def save_record(r):
 d={k:v for k,v in r.items() if k not in ['id','kind','owner']};M.put(r['kind'],r['owner'],d,r['id'])
def need(u,p):
 if p not in M.permissions(u):raise PermissionError('Permission required: '+p)
def review(u,kind):return ('applications.allowlist' if kind=='Allowlist' else 'applications.other') in M.permissions(u)
def eligibility(u,key):
 f=M.settings()['forms'][key]
 if not f['open']:return 'Applications Closed'
 if key=='Allowlist' and u['allowlisted']:return 'Already Allowlisted'
 approved=[r for r in M.records('application') if r['owner']==u['id'] and r['type']==key and r.get('approvedAt')]
 if any(not(key=='Allowlist' and r.get('roleRemoved')) for r in approved):return 'Application Approved'
 return ''
def member(uid):
 with M.conn() as c:r=c.execute('SELECT id,discord,name,groups_json FROM members WHERE id=? OR discord=?',(uid,uid)).fetchone()
 return {'id':r['id'],'discordId':r['discord'],'name':r['name'],'roles':json.loads(r['groups_json'])} if r else {'id':uid,'discordId':uid,'name':uid,'roles':[]}
def resolve(discord):
 if not re.fullmatch(r'\d{15,22}|demo-[A-Za-z0-9_-]+',discord):raise ValueError('Enter a Discord user ID')
 existing=member(discord)
 with M.conn() as c:row=c.execute('SELECT id FROM members WHERE id=? OR discord=?',(discord,discord)).fetchone()
 if row:return row['id']
 uid=secrets.token_hex(16)
 with M.conn() as c:c.execute('INSERT INTO members(id,discord,name,groups_json,linked) VALUES(?,?,?,?,0)',(uid,discord,discord,'[]'))
 return uid
def queue_dm(uid,text):
 with M.conn() as c:return c.execute('INSERT INTO outbox(target,text) VALUES(?,?)',(uid,text)).lastrowid
def notifications():
 while True:
  if os.getenv('DISCORD_BOT_TOKEN'):
   with M.conn() as c:jobs=c.execute("SELECT * FROM outbox WHERE status='pending' AND next_at<=? LIMIT 5",(time.time(),)).fetchall()
   for job in jobs:
    try:
     target=member(job['target'])['discordId'];roles=M.discord('guilds/'+os.environ['DISCORD_GUILD_ID']+'/members/'+target).get('roles',[])
     if set(roles)&set(M.settings()['dmExcludedRoles']):status='excluded'
     else:
      channel=M.discord('users/@me/channels',{'recipient_id':target});M.discord('channels/'+channel['id']+'/messages',{'content':job['text'],'allowed_mentions':{'parse':[]}});status='sent'
     with M.conn() as c:c.execute('UPDATE outbox SET status=? WHERE id=?',(status,job['id']))
    except Exception:
     with M.conn() as c:c.execute('UPDATE outbox SET attempts=attempts+1,next_at=?,status=? WHERE id=?',(int(time.time())+min(3600,30*2**min(job['attempts'],7)),'failed' if job['attempts']>=7 else 'pending',job['id']))
  time.sleep(3)
def view(u):
 p=M.permissions(u);s=M.settings();result=[]
 for r in M.records():
  allowed=(r['kind']=='ticket' and ('tickets.view'in p or r['owner']==u['id'] or u['id'] in r.get('participants',[]))) or (r['kind']=='case' and 'cases.view'in p) or (r['kind']=='application' and (r['owner']==u['id'] or review(u,r['type']))) or (r['kind']=='ban' and ('bans.view'in p or r['owner']==u['id'])) or (r['kind']=='profile' and 'users.view'in p)
  if not allowed:continue
  if r['kind']=='ticket':
   r['player']=member(r['owner'])
   if 'tickets.notes'not in p:r.pop('notes',None)
   if 'tickets.view'in p:r['caseLinks']=[{'id':c['id'],'title':c['title']} for c in M.records('case') if c['id']==r.get('caseId') or any(x['id']==r['id'] for x in c.get('reportLinks',[]))]
   else:r.pop('caseId',None)
  result.append(r)
 safe={k:v for k,v in s.items() if k not in ['groups','roleMappings','dmExcludedRoles']}
 if 'groups.edit'in p or 'integrations.edit'in p:safe=s
 with M.conn() as c:
  completions=[dict(r) for r in c.execute('SELECT actor,COUNT(DISTINCT ticket) AS count FROM completions WHERE at>? GROUP BY actor',(int(time.time())-90*86400,))] if 'tickets.view'in p else []
  logs=[dict(r) for r in c.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 300')] if 'audit.view'in p else []
 return {'records':result,'settings':safe,'eligibility':{key:eligibility(u,key) for key in s['forms']},'completions':completions,'audit':logs,'permissionNames':PERMISSIONS,'integrations':{'discord':bool(os.getenv('DISCORD_CLIENT_ID')),'bot':bool(os.getenv('DISCORD_BOT_TOKEN')),'fivem':bool(os.getenv('FIVEM_BRIDGE_URL'))},'members':[member(r['owner']) for r in result]}
def mutate(u,path,d):
 now=int(time.time());s=M.settings();p=M.permissions(u)
 if path=='/api/settings':
  changes=d['changes'];mapping={'name':'branding.edit','color':'branding.edit','secondary':'branding.edit','logo':'branding.edit','signatureLogo':'branding.edit','rulesSections':'rules.edit','categories':'categories.edit','responseTemplates':'forms.edit','forms':'forms.edit','groups':'groups.edit','roleMappings':'integrations.edit','allowlistRole':'integrations.edit','dmExcludedRoles':'integrations.edit'}
  for k,v in changes.items():
   if k not in mapping:raise ValueError('Unknown setting')
   need(u,mapping[k])
   if k in ['color','secondary'] and not re.fullmatch(r'#[0-9a-fA-F]{6}',v):raise ValueError('Use a six-digit hex colour')
   if k in ['logo','signatureLogo'] and v and not v.startswith('https://'):raise ValueError('Logo must use HTTPS')
   if k=='groups':
    if v.get('management')!=PERMISSIONS:raise ValueError('Management must retain all permissions')
    if any(not isinstance(ps,list) or any(x not in PERMISSIONS for x in ps) for ps in v.values()):raise ValueError('Unknown group permission')
   if k=='categories' and not v:raise ValueError('Keep at least one category')
   if k=='forms':
    for f in v.values():
     if not f['questions']:raise ValueError('Keep at least one question')
     for q in f['questions']:
      if not q['text'].strip() or not isinstance(q['min'],int) or q['min']<0:raise ValueError('Invalid question')
   s[k]=v
  with M.conn() as c:c.execute('UPDATE settings SET data=?',(json.dumps(s),))
  M.audit(u,'settings.update',','.join(changes));return {'ok':True}
 if path=='/api/ai-check':
  r=find(d['id'],'application')
  if not review(u,r['type']):raise PermissionError('Application review permission required')
  index=int(d['index'])
  if index<0 or index>=len(r['answers']):raise ValueError('Invalid answer')
  if not os.getenv('AI_CHECK_URL'):return {'score':None,'heavy':False,'message':'No detection provider connected. A reliable authorship percentage cannot be assigned. Use follow-up questions and manual review.'}
  request=urllib.request.Request(os.environ['AI_CHECK_URL'],data=json.dumps({'text':r['answers'][index]}).encode(),headers={'Authorization':'Bearer '+os.getenv('AI_CHECK_TOKEN',''),'Content-Type':'application/json'})
  with urllib.request.urlopen(request,timeout=20) as response:result=json.load(response)
  score=result.get('score')
  if not isinstance(score,(int,float)) or not 0<=score<=100:raise ValueError('Provider returned an invalid score')
  return {'score':score,'heavy':score>65,'message':'External provider estimate, not proof of authorship. Human review is required; never auto-deny solely on this score.'}
 if path=='/api/availability':
  key=d['type']
  if not review(u,key):need(u,'applications.availability')
  s['forms'][key]['open']=bool(d['open'])
  with M.conn() as c:c.execute('UPDATE settings SET data=?',(json.dumps(s),))
  M.audit(u,'applications.availability',key);return {'ok':True}
 if path=='/api/create':
  kind=d['kind'];a=d['data'];owner=u['id']
  if kind=='ticket':
   if not a.get('title','').strip() or not a.get('text','').strip():raise ValueError('Title and message are required')
   category=a['category']
   if category not in s['categories'] and category not in ['Staff-to-player','Custom work request']:raise ValueError('Category not available')
   if a.get('target'):need(u,'tickets.participants');owner=resolve(a['target'])
   caseid=a.get('caseId')
   if caseid:need(u,'cases.edit');find(caseid,'case')
   if category=='Ban appeal':
    bans=[r for r in M.records('ban') if r['owner']==owner and r.get('active')]
    if not bans:raise ValueError('No active ban to appeal')
    if any(now<r['appealAt'] for r in bans):raise ValueError('Appeal date not reached')
   a={'title':a['title'],'category':category,'status':'Open','created':now,'claimed':None,'priority':'Normal','messages':[message(u,a['text'])],'notes':[],'participants':[],'evidence':[],'caseId':caseid}
  elif kind=='case':need(u,'cases.edit');a={'title':a['title'],'created':now,'reportLinks':[],'players':[],'notes':[]}
  elif kind=='application':
   key=a['type'];reason=eligibility(u,key)
   if reason:raise ValueError(reason)
   f=s['forms'][key];answers=a['answers']
   if len(answers)!=len(f['questions']):raise ValueError('Question count changed; reload the form')
   for text,q in zip(answers,f['questions']):
    if q.get('required',True) and not text.strip():raise ValueError('Answer all required questions')
    if text and len(text.strip())<q['min']:raise ValueError('Answer below minimum')
    if q.get('type')=='ack' and text!='Yes':raise ValueError('Acknowledge the application notices')
   previous=[r for r in M.records('application') if r['type']==key and r['owner']==owner];last=next((r for r in previous if r['status']=='Rejected'),None)
   a={'type':key,'created':now,'answers':answers,'questions':f['questions'],'status':'Submitted','attempts':len(previous),'lastRejection':last.get('reason','') if last else '', 'history':[]}
  elif kind=='profile':need(u,'users.notes');owner=resolve(a['discordId']);a={'created':now,'notes':a['notes'],'author':u['name']}
  elif kind=='ban':need(u,'bans.create');owner=resolve(a['discordId']);a={'created':now,'reason':a['reason'],'active':True,'appealAt':int(a['appealAt']),'author':u['name']}
  else:raise ValueError('Invalid record type')
  id=M.put(kind,owner,a);M.audit(u,'create.'+kind,id)
  if kind=='ticket':
   if owner!=u['id']:queue_dm(owner,'You were added to ticket #'+str(id))
   if a.get('caseId'):
    case=find(a['caseId'],'case');case['reportLinks'].append({'id':id,'relation':'Staff-to-player'});save_record(case)
  return {'id':id}
 if path=='/api/update':
  r=find(d['id']);kind=r['kind'];action=d['action']
  if kind=='ticket':
   own=r['owner']==u['id'] or u['id'] in r['participants']
   if not own:need(u,'tickets.view')
   if action in ['reply','evidence']:
    if not own:need(u,'tickets.reply')
    if r['status']=='Resolved' and 'tickets.reply'not in p:raise ValueError('Ticket closed')
    if action=='reply':
     if not d['text'].strip():raise ValueError('Empty reply')
     r['messages'].append(message(u,d['text']))
     if 'tickets.reply'in p:
      r['status']='Awaiting response'
      for target in set([r['owner']]+r['participants']):queue_dm(target,'Staff replied to ticket #'+str(r['id']))
    else:
     if not d['url'].startswith(('https://','http://')):raise ValueError('Invalid evidence link')
     r['evidence'].append({'url':d['url'],'label':d['label'],'at':now,'author':u['name']})
   elif action=='claim':
    need(u,'tickets.claim')
    if r['claimed'] and r['claimed']!=u['id']:need(u,'tickets.assign')
    r['claimed']=u['id'] if d.get('claim',True) else None
   elif action=='assign':need(u,'tickets.assign');r['claimed']=resolve(d['discordId']) if d['discordId'] else None
   elif action=='priority':
    need(u,'tickets.priority')
    if d['priority']not in ['Low','Normal','High','Urgent']:raise ValueError('Invalid priority')
    r['priority']=d['priority']
   elif action=='status':
    need(u,'tickets.close')
    if d['status']not in ['Open','Under review','Awaiting response','Resolved']:raise ValueError('Invalid status')
    if d['status']=='Resolved' and r['status']!='Resolved':
     with M.conn() as c:c.execute('INSERT INTO completions VALUES(?,?,?)',(r['id'],u['id'],now))
    r['status']=d['status']
   elif action=='note':need(u,'tickets.notes');r['notes'].append(message(u,d['text']))
   elif action=='participant':
    need(u,'tickets.participants');target=resolve(d['discordId'])
    if target not in r['participants']:r['participants'].append(target);queue_dm(target,'You were added to ticket #'+str(r['id']))
   else:raise ValueError('Unknown ticket action')
  elif kind=='case':
   need(u,'cases.edit')
   if action=='reports':
    relation=d.get('relation','Related')
    if relation not in ['Primary','Related','Duplicate','Staff-to-player']:raise ValueError('Invalid relationship')
    for id in d['ids']:
     find(id,'ticket')
     if not any(x['id']==int(id) for x in r['reportLinks']):r['reportLinks'].append({'id':int(id),'relation':relation})
   elif action=='unlink':r['reportLinks']=[x for x in r['reportLinks'] if x['id']!=int(d['reportId'])]
   elif action=='player':
    target=d['discordId'];resolve(target)
    if target not in r['players']:r['players'].append(target)
   elif action=='removePlayer':r['players']=[x for x in r['players'] if x!=d['discordId']]
   elif action=='note':r['notes'].append(message(u,d['text']))
   else:raise ValueError('Unknown case action')
  elif kind=='application':
   if not review(u,r['type']):raise PermissionError('Application review permission required')
   if action=='feedback':
    index=int(d['index'])
    if index < -1 or index>=len(r['answers']):raise ValueError('Invalid answer')
    if not d.get('text','').strip():raise ValueError('Feedback is empty')
    r.setdefault('feedback',[]).append({'index':index,'text':d['text'],'author':u['name'],'at':now})
    if d.get('notify'):r['feedback'][-1]['dmId']=queue_dm(r['owner'],r['type']+' Application #'+str(r['id'])+' feedback:\n'+d['text'])
    save_record(r);M.audit(u,'application.feedback',r['id']);return {'ok':True}
   if d['status']not in ['Under review','Accepted','Rejected']:raise ValueError('Invalid decision')
   if d['status']=='Rejected' and not d.get('reason','').strip():raise ValueError('Rejection reason required')
   r.update(status=d['status'],reason=d.get('reason',''));
   if d.get('notify'):queue_dm(r['owner'],r['type']+' Application #'+str(r['id'])+' — '+d['status']+'\n'+d.get('reason',''))
   r['history'].append({'at':now,'author':u['name'],'status':d['status'],'reason':d.get('reason','')})
   if d['status']=='Accepted':
    r['approvedAt']=r.get('approvedAt',now);r['roleSeen']=member_allowlisted(r['owner']);r['roleRemoved']=False
  elif kind=='ban':
   need(u,'bans.revoke')
   if r.get('live'):
    need(u,'server.ban')
    request=urllib.request.Request(os.environ['FIVEM_BRIDGE_URL'],data=json.dumps({'action':'unban','discordId':member(r['owner'])['discordId'],'reason':'Panel ban revoked'}).encode(),headers={'Authorization':'Bearer '+os.environ['FIVEM_BRIDGE_TOKEN'],'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=15) as response:result=json.load(response)
    if not result.get('ok'):raise ValueError('Live unban failed; panel ban unchanged')
   r['active']=False
  else:raise ValueError('Unsupported update')
  save_record(r);M.audit(u,kind+'.'+action,r['id']);return {'ok':True}
 if path=='/api/server':
  action=d['action']
  if action not in ['kick','ban']:raise ValueError('Invalid server action')
  need(u,'server.'+action)
  if not os.getenv('FIVEM_BRIDGE_URL'):raise ValueError('FiveM integration not configured')
  if action=='ban':
   need(u,'bans.create')
   if not isinstance(d.get('appealAt'),(int,float)):raise ValueError('Appeal eligibility date required')
  resolve(d['discordId'])
  if not d.get('reason','').strip():raise ValueError('Reason required')
  request=urllib.request.Request(os.environ['FIVEM_BRIDGE_URL'],data=json.dumps(d).encode(),headers={'Authorization':'Bearer '+os.environ['FIVEM_BRIDGE_TOKEN'],'Content-Type':'application/json'})
  with urllib.request.urlopen(request,timeout=15) as response:result=json.load(response)
  if result.get('ok') and action=='ban':
   need(u,'bans.create');M.put('ban',resolve(d['discordId']),{'created':now,'reason':d['reason'],'active':True,'appealAt':int(d['appealAt']),'author':u['name'],'live':True})
  M.audit(u,'server.'+action,d['discordId']);return result
 raise ValueError('Unknown endpoint')
def member_allowlisted(uid):
 with M.conn() as c:r=c.execute('SELECT allowlisted FROM members WHERE id=?',(uid,)).fetchone()
 return bool(r and r['allowlisted'])
def find(id,kind=None):
 r=next((r for r in M.records() if r['id']==int(id) and (not kind or r['kind']==kind)),None)
 if not r:raise ValueError('Record not found')
 return r
def message(u,text):return {'author':u['name'],'staff':'tickets.reply'in M.permissions(u),'text':text,'at':int(time.time()),'roles':u['groups']}
