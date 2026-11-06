-- Run behind a private reverse proxy; never put the shared token in a client file.
local resource = GetCurrentResourceName()
local bans = json.decode(LoadResourceFile(resource, 'bans.json') or '{}') or {}
local function saveBans() SaveResourceFile(resource, 'bans.json', json.encode(bans), -1) end
local function discordOf(src)
 for _, id in ipairs(GetPlayerIdentifiers(src)) do
  if id:sub(1,8) == 'discord:' then return id:sub(9) end
 end
end
AddEventHandler('playerConnecting', function(_, _, deferrals)
 local src = source
 deferrals.defer(); Wait(0)
 local id = discordOf(src)
 if id and bans[id] then deferrals.done('Banned: '..bans[id].reason) else deferrals.done() end
end)
SetHttpHandler(function(req, res)
 local token = GetConvar('reidyy_bridge_token', '')
 local auth = req.headers['Authorization'] or req.headers['authorization']
 if token == '' or auth ~= 'Bearer '..token then res.writeHead(403); res.send('{"error":"Forbidden"}'); return end
 if req.method ~= 'POST' then res.writeHead(405); res.send('{}'); return end
 req.setDataHandler(function(body)
  if #body > 8192 then res.writeHead(413);res.send('{}');return end
  local ok, data = pcall(json.decode, body)
  if not ok or type(data) ~= 'table' or type(data.discordId) ~= 'string' or not data.discordId:match('^%d+$') or type(data.reason) ~= 'string' then res.writeHead(400);res.send('{"error":"Invalid request"}');return end
  if data.action ~= 'kick' and data.action ~= 'ban' and data.action ~= 'unban' then res.writeHead(400);res.send('{}');return end
  if data.action == 'ban' then bans[data.discordId] = {reason=data.reason, at=os.time()};saveBans() end
  if data.action == 'unban' then bans[data.discordId] = nil;saveBans() end
  local found=false
  if data.action ~= 'unban' then
   for _, player in ipairs(GetPlayers()) do
    if discordOf(player) == data.discordId then DropPlayer(player, data.reason); found=true end
   end
  end
  res.writeHead(200, {['Content-Type']='application/json'})
  res.send(json.encode({ok=data.action ~= 'kick' or found, online=found, action=data.action}))
 end)
end)
