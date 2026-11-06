"""Reidyy Ticket System. Python 3.11+, standard library only."""
import os,json,sqlite3,secrets,time,hmac,hashlib,urllib.request,urllib.parse
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from http.cookies import SimpleCookie
ROOT=Path(__file__).parent
DEMO=os.getenv('DEMO_MODE','true').lower()=='true'
SECRET=os.getenv('SESSION_SECRET') or secrets.token_hex(32)
DB=os.getenv('DATABASE_PATH',str(ROOT/'data.sqlite3'))
ROLES={'player':[],'reviewer':['applications'],'support':['tickets'],'admin':['tickets','cases','players','server'],'management':['tickets','cases','players','server','applications','settings','rules','permissions']}
def conn():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def init():
 with conn() as c:
  c.execute('CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,owner TEXT NOT NULL,data TEXT NOT NULL)')
  c.execute('CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1),data TEXT NOT NULL)')
  c.execute('CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,at INTEGER,actor TEXT,action TEXT,target TEXT)')
  if not c.execute('SELECT 1 FROM settings').fetchone():
   q=['Do you understand that cheating, AI-generated or third-party applications can lead to a permanent ban?','Do you understand that links are only allowed where requested?','In which timezone do you play primarily?','What is your Twitch channel?','How old are you?','How long have you been roleplaying?','Have you been banned from any roleplay communities? Where and why?','Microphone recording link (https://vocaroo.com/).','What is roleplay? Explain in your own words.','How will you refer to OOC things such as admins, reports and controls in RP?','What is metagaming?','Describe an original, interesting roleplay character.','Someone points a gun at you. What do you do?','Your friend is being robbed. What do you do?','Someone disrespects you in the street. What do you do?','Your car is being towed. What do you do?','A cop pulls you over and attempts to ticket you. What do you do?','How did you hear about the community?']
   forms={k:{'open':True,'questions':[{'text':x,'min':0} for x in (q if k=='Allowlist' else ['Why are you applying?','Describe your relevant experience.','What is your timezone and availability?'])]} for k in ['Allowlist','Developer','Staff','App Reviewer']}
   s={'name':'Reidyy Ticket System','color':'#b881f7','logo':'','rules':'Community rules have not yet been published. Management can add the server rules here.','categories':{'General support':'Describe your issue:','Player report':'Player ID:\nIncident time:\nWhat happened:\nEvidence:','Ban appeal':'Ban reference:\nWhy should we review your ban?'},'forms':forms,'groups':ROLES,'roleMappings':{},'allowlistRole':'','dmExcludedRoles':[]}
   c.execute('INSERT INTO settings VALUES(1,?)',(json.dumps(s),))
def settings():
 with conn() as c:return json.loads(c.execute('SELECT data FROM settings').fetchone()[0])
def records(kind=None):
 with conn() as c:
  rows=c.execute('SELECT * FROM records'+(' WHERE kind=?' if kind else '')+' ORDER BY id DESC',(kind,) if kind else ()).fetchall()
 return [{'id':r['id'],'kind':r['kind'],'owner':r['owner'],**json.loads(r['data'])} for r in rows]
def put(kind,owner,data,id=None):
 with conn() as c:
  if id:c.execute('UPDATE records SET data=? WHERE id=?',(json.dumps(data),id))
  else:id=c.execute('INSERT INTO records(kind,owner,data) VALUES(?,?,?)',(kind,owner,json.dumps(data))).lastrowid
 return id
def audit(user,action,target):
 with conn() as c:c.execute('INSERT INTO audit(at,actor,action,target) VALUES(?,?,?,?)',(int(time.time()),user['id'],action,str(target)))
def discord(path,data=None,token=None):
 body=json.dumps(data).encode() if data is not None else None
 req=urllib.request.Request('https://discord.com/api/v10/'+path,data=body,headers={'Authorization':token or 'Bot '+os.environ['DISCORD_BOT_TOKEN'],'Content-Type':'application/json','User-Agent':'ReidyyTicketSystem/1.0'})
 with urllib.request.urlopen(req,timeout=15) as r:return json.load(r)
def notify(target,text):
 if not os.getenv('DISCORD_BOT_TOKEN'):return
 try:
  member=discord('guilds/'+os.environ['DISCORD_GUILD_ID']+'/members/'+target)
  if set(member.get('roles',[]))&set(settings()['dmExcludedRoles']):return
  channel=discord('users/@me/channels',{'recipient_id':target});discord('channels/'+channel['id']+'/messages',{'content':text,'allowed_mentions':{'parse':[]}})
 except Exception as exc:
  audit({'id':'system'},'dm_failed',type(exc).__name__)
def permissions(u):
 s=settings();groups=['management'] if DEMO and u['id'].startswith('demo-management') else u.get('groups',['player'])
 return set(p for group in groups for p in s['groups'].get(group,[]))
class Handler(BaseHTTPRequestHandler):
 def output(self,data,status=200,headers=None):
  raw=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
  for k,v in (headers or {}).items():self.send_header(k,v)
  self.end_headers();self.wfile.write(raw)
 def session(self):
  try:
   cookie=SimpleCookie(self.headers.get('Cookie',''));v=cookie['session'].value;token,sig=v.rsplit('.',1)
   if not hmac.compare_digest(sig,hmac.new(SECRET.encode(),token.encode(),hashlib.sha256).hexdigest()):return None
   import base64
   u=json.loads(base64.urlsafe_b64decode(token));return u if u['expires']>time.time() else None
  except Exception:return None
 def login(self,u):
  import base64
  u['expires']=time.time()+3600*8;token=base64.urlsafe_b64encode(json.dumps(u).encode()).decode();sig=hmac.new(SECRET.encode(),token.encode(),hashlib.sha256).hexdigest()
  return {'Set-Cookie':'session='+token+'.'+sig+'; HttpOnly; SameSite=Lax; Path=/'+('; Secure' if os.getenv('PUBLIC_URL','').startswith('https:') else '')}
 def do_GET(self):
  path=urllib.parse.urlparse(self.path);query=urllib.parse.parse_qs(path.query)
  if path.path=='/auth/discord':
   if not os.getenv('DISCORD_CLIENT_ID'):return self.output({'error':'Configure Discord OAuth first'},503)
   state=secrets.token_urlsafe(24);url='https://discord.com/oauth2/authorize?'+urllib.parse.urlencode({'client_id':os.environ['DISCORD_CLIENT_ID'],'redirect_uri':os.environ['PUBLIC_URL']+'/auth/callback','response_type':'code','scope':'identify guilds.members.read','state':state})
   self.send_response(302);self.send_header('Location',url);self.send_header('Set-Cookie','oauth_state='+state+'; HttpOnly; SameSite=Lax; Path=/; Max-Age=600');self.end_headers();return
  if path.path=='/auth/callback':
   try:
    cookies=SimpleCookie(self.headers.get('Cookie',''));assert hmac.compare_digest(cookies['oauth_state'].value,query['state'][0])
    data=urllib.parse.urlencode({'client_id':os.environ['DISCORD_CLIENT_ID'],'client_secret':os.environ['DISCORD_CLIENT_SECRET'],'grant_type':'authorization_code','code':query['code'][0],'redirect_uri':os.environ['PUBLIC_URL']+'/auth/callback'}).encode()
    with urllib.request.urlopen(urllib.request.Request('https://discord.com/api/oauth2/token',data=data),timeout=15) as r:token=json.load(r)['access_token']
    u=discord('users/@me',token='Bearer '+token);member=discord('users/@me/guilds/'+os.environ['DISCORD_GUILD_ID']+'/member',token='Bearer '+token);s=settings();roles=member['roles'];groups=['player']+[g for g,ids in s['roleMappings'].items() if set(ids)&set(roles)]
    headers=self.login({'id':u['id'],'name':u['username'],'groups':groups,'allowlisted':s['allowlistRole'] in roles});self.send_response(302);self.send_header('Location','/')
    for k,v in headers.items():self.send_header(k,v)
    self.end_headers();return
   except Exception:return self.output({'error':'Discord authentication failed. Verify configuration and server membership.'},401)
  if path.path.startswith('/api/'):
   u=self.session()
   if path.path=='/api/session':return self.output({'user':u,'demo':DEMO,'permissions':list(permissions(u)) if u else []})
   if not u:return self.output({'error':'Sign in required'},401)
   p=permissions(u);s=settings()
   if path.path=='/api/data':
    items=[r for r in records() if r['kind']=='ticket' and ('tickets'in p or r['owner']==u['id'] or u['id'] in r.get('participants',[])) or r['kind']=='case' and 'cases'in p or r['kind']=='application' and (r['owner']==u['id'] or 'applications'in p and (r.get('type')=='Allowlist' or 'settings'in p)) or r['kind'] in ['profile','ban'] and ('players'in p or r['owner']==u['id'])]
    if 'tickets'not in p:
     for r in items:
      if r['kind']=='ticket':r.pop('notes',None);r.pop('caseId',None)
    safe={k:v for k,v in s.items() if k not in ['groups','roleMappings','dmExcludedRoles']};return self.output({'records':items,'settings':s if 'settings'in p else safe})
   return self.output({'error':'Not found'},404)
  file=ROOT/'public'/('index.html' if path.path=='/' else path.path.lstrip('/'))
  if not file.resolve().is_relative_to((ROOT/'public').resolve()) or not file.is_file():return self.output({'error':'Not found'},404)
  import mimetypes
  self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(file)[0] or 'text/plain');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(file.read_bytes())
 def do_POST(self):
  try:self.post()
  except (ValueError,KeyError,AssertionError) as e:self.output({'error':str(e) or 'Invalid request'},400)
  except Exception as e:self.output({'error':'Operation failed: '+type(e).__name__},500)
 def post(self):
  origin=self.headers.get('Origin');host=self.headers.get('Host')
  if origin and urllib.parse.urlparse(origin).netloc!=host:return self.output({'error':'Invalid origin'},403)
  size=int(self.headers.get('Content-Length','0'))
  if size>20_000_000:return self.output({'error':'Request too large'},413)
  d=json.loads(self.rfile.read(size) or '{}');path=self.path
  if path=='/api/demo':
   if not DEMO:return self.output({'error':'Demo disabled'},404)
   group=d.get('group','player');assert group in ROLES
   return self.output({'ok':True},headers=self.login({'id':'demo-'+group,'name':group.title(),'groups':[group],'allowlisted':False}))
  if path=='/api/logout':return self.output({'ok':True},headers={'Set-Cookie':'session=; Max-Age=0; HttpOnly; SameSite=Lax; Path=/'})
  u=self.session()
  if not u:return self.output({'error':'Sign in required'},401)
  p=permissions(u);s=settings()
  def require(perm):
   if perm not in p:raise ValueError('Permission required: '+perm)
  if path=='/api/settings':
   require('settings');assert isinstance(d['settings'],dict)
   with conn() as c:c.execute('UPDATE settings SET data=?',(json.dumps(d['settings']),))
   audit(u,'settings.update',1);return self.output({'ok':True})
  if path=='/api/create':
   kind=d['kind'];assert kind in ['ticket','case','application','profile','ban'];data=d['data'];owner=u['id'];now=int(time.time());data.update(created=now)
   if kind=='case':require('cases');data.update(reports=[],players=[],notes=[])
   if kind=='profile':require('players');owner=data['discordId']
   if kind=='ban':require('server');owner=data['discordId'];data.update(active=True,appealAt=int(data['appealAt']))
   if kind=='application':
    f=s['forms'][data['type']];assert f['open'],'Applications closed'
    past=[r for r in records('application') if r['owner']==owner and r['type']==data['type']]
    assert not (data['type']=='Allowlist' and u.get('allowlisted')),'Already allowlisted'
    assert not any(r['status']=='Accepted' for r in past) or data['type']=='Allowlist' and not u.get('allowlisted'),'Already approved'
    assert len(data['answers'])==len(f['questions'])
    for answer,q in zip(data['answers'],f['questions']):assert len(answer.strip())>=max(1,int(q['min'])),'Answer below minimum'
    rejected=next((r for r in past if r['status']=='Rejected'),None);data.update(status='Submitted',attempts=len(past),lastRejection=rejected.get('reason','') if rejected else '',questions=f['questions'])
   if kind=='ticket':
    if data.get('target'):require('tickets');owner=data.pop('target')
    if data.get('caseId'):require('cases')
    if data.get('category')=='Ban appeal':
     bans=[r for r in records('ban') if r['owner']==owner and r.get('active')];assert bans,'No active ban';assert all(now>=r['appealAt'] for r in bans),'Appeal date not reached'
    data.update(status='Open',claimed=None,messages=[{'author':u['name'],'staff':'tickets'in p,'text':data.get('text',''),'at':now}],notes=[],participants=[])
   id=put(kind,owner,data);audit(u,'create.'+kind,id)
   if kind=='ticket' and owner!=u['id']:notify(owner,'You have been added to ticket #'+str(id))
   return self.output({'id':id})
  if path=='/api/update':
   r=next((r for r in records() if r['id']==int(d['id'])),None);assert r,'Record not found';action=d['action'];now=int(time.time());kind=r['kind'];owner=r['owner']
   if kind=='ticket':
    assert 'tickets'in p or owner==u['id'] or u['id'] in r.get('participants',[]),'No access'
    if action=='reply':
     assert r['status']!='Resolved' or 'tickets'in p,'Ticket closed';assert d['text'].strip();r['messages'].append({'author':u['name'],'staff':'tickets'in p,'text':d['text'],'at':now})
     if 'tickets'in p:notify(owner,'Staff responded to ticket #'+str(r['id']))
    elif action=='note':require('tickets');r['notes'].append({'author':u['name'],'text':d['text'],'at':now})
    elif action=='claim':require('tickets');r['claimed']=u['id'] if d.get('claim',True) else None
    elif action=='status':
     require('tickets');assert d['status'] in ['Open','Under review','Awaiting response','Resolved'];r['status']=d['status']
     if r['status']=='Resolved':r.update(resolvedAt=now,resolvedBy=u['id'])
    elif action=='participant':
     require('tickets');assert d['discordId'].isdigit();r['participants'].append(d['discordId']);notify(d['discordId'],'You were added to ticket #'+str(r['id']))
    else:raise ValueError('Unknown action')
   elif kind=='case':
    require('cases')
    if action=='reports':
     ids=[int(x) for x in d['ids']];assert all(any(t['id']==i and t['kind']=='ticket' for t in records()) for i in ids);r['reports']=list(set(r['reports']+ids))
    elif action=='player':assert d['discordId'].isdigit();r['players']=list(set(r['players']+[d['discordId']]))
    elif action=='note':r['notes'].append({'author':u['name'],'text':d['text'],'at':now})
    else:raise ValueError('Unknown action')
   elif kind=='application':
    require('applications');assert r['type']=='Allowlist' or 'settings'in p;assert d['status'] in ['Under review','Accepted','Rejected'];assert d['status']!='Rejected' or d.get('reason','').strip();r.update(status=d['status'],reason=d.get('reason',''),reviewedAt=now)
   else:raise ValueError('Unsupported update')
   id=r.pop('id');r.pop('kind');r.pop('owner');put(kind,owner,r,id);audit(u,action,id);return self.output({'ok':True})
  if path=='/api/server':
   require('server');assert d['action'] in ['kick','ban'];assert os.getenv('FIVEM_BRIDGE_URL'),'FiveM bridge not configured';assert d['discordId'].isdigit();assert d['reason'].strip()
   request=urllib.request.Request(os.environ['FIVEM_BRIDGE_URL'],data=json.dumps(d).encode(),headers={'Authorization':'Bearer '+os.environ['FIVEM_BRIDGE_TOKEN'],'Content-Type':'application/json'})
   with urllib.request.urlopen(request,timeout=15) as response:result=json.load(response)
   audit(u,'server.'+d['action'],d['discordId']);return self.output(result)
  return self.output({'error':'Not found'},404)
if __name__=='__main__':
 init();print('Reidyy Ticket System: http://127.0.0.1:8000 | Demo mode:',DEMO);ThreadingHTTPServer((os.getenv('HOST','127.0.0.1'),int(os.getenv('PORT','8000'))),Handler).serve_forever()
