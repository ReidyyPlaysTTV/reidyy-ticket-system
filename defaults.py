"""Original application wording and community rules supplied by the project owner."""
QUESTIONS=[
'AI and Honor notice: If you attempt to cheat our applications, for example by using a pre-generated application, AI generate application, or have someone do your application for you, you will be banned from this community permanently. Do you understand?',
'Do not use any links except where specifically asked for them IE: Twitch/Streaming Link, Voice link. Note: If you exceed the maximum character count of a discord message it will turn into a link to an external text file. This will result in that question being considered unsatisfactory/failing. Do you understand?',
'In which timezone do you play primarily?', 'Whats your Twitch channel?', 'How old are you?', 'How long have you been roleplaying?', 'Have you been banned from any roleplaying communities, if so where and why?',
'Please submit a link to a clip or recording that shows your microphone sound quality meets standards. You can use https://vocaroo.com/.',
'Q1: What is roleplay? Use your own words to demonstrate an understanding of what it means.',
'Q2: On Umbra, how are you intending to reference out-of-character things like admins, reports or buttons to press?',
'Q3: What is meta-gaming? Use your own words to demonstrate an understanding of what it means.',
'Q4: Give a detailed example of a roleplay character of your own creation and demonstrate what makes them interesting',
'Q5: (How would you act in character): You are walking down the road, someone points a gun in your face, what does your character do?',
'Q6: (How would you act in character): Your friend is being robbed, what does your character do?',
'Q7: (How would you act in character): You are talking to someone on the street, they say something you find disrespectful, what does your character do?',
'Q8: (How would you act in character): Walking back to your car, you see it in the process of being towed, what does your character do?',
'Q9: (How would you act in character): You are driving down the road, a cop pulls you over and attempts to ticket you, what does your character do?',
'How do you know about Umbra?']
FORMS={'Allowlist':{'open':True,'questions':[{'text':q,'min':0,'required':True,'type':'ack' if i<2 else 'url' if i in [3,7] else 'long'} for i,q in enumerate(QUESTIONS)]}}
for title,questions in {
'Developer':['What is your timezone and availability?','What development skills and FiveM frameworks do you work with?','Share a portfolio or examples of your work (links allowed).','Why would you like to join the development team?'],
'Staff':['What is your timezone and availability?','How long have you been part of the community?','Describe your previous moderation or support experience.','How would you handle a report involving a friend?','Why would you like to join the staff team?'],
'App Reviewer':['What is your timezone and availability?','What makes a strong allowlist application?','How would you give constructive rejection feedback?','How would you handle an answer you suspect was written using AI?','Why would you like to become an application reviewer?']}.items():FORMS[title]={'open':True,'questions':[{'text':q,'min':0,'required':True,'type':'long'} for q in questions]}
RULES=[{'title':title,'body':body} for title,body in [
('Welcome to Umbra Roleplay!',"""We're excited to have you join our community. To ensure everyone has the best experience possible, we ask that you carefully read and follow the rules outlined below. Use common sense, respect your fellow players, and remember: quality roleplay always comes first.

To be a member of Umbra, you must:
• Be 18 years of age or older.
• Own a working microphone with clear audio quality.
• Be fluent in spoken English.
• Have prior experience with roleplay.

All interactions on our FiveM server and associated Discord must adhere to:
• Twitch Terms of Service
• Twitch Community Guidelines
• Discord Terms of Service
• Discord Community Guidelines

Note:
• Music played in-game must be DMCA-safe.
• Use Discord channels as intended. Keep chats in chat channels. Do not clog media or announcement spaces.

Do not DM Admins or Devs unless explicitly permitted in their Twitch status, or in emergencies."""),
('Stream sniping',"""Stream Sniping (watching a stream to gain an in-game advantage OR to locate other players) is prohibited.
• Do not be in any stream other than your own while you are active on the server.
• Being present in a stream while on the server can be considered evidence of Stream Sniping and/or Metagaming."""),
('Metagaming',"""Metagaming (using OOC info your character shouldn't know) is prohibited.
Examples:
• Discussing things that happened without your character's presence OOC on Discord and then acting on them/discussing them in RP (without learning about them in RP first).
• Watching a stream showing hidden stashes and going there IC without proper discovery.
• You hear in a Discord call that your friend's gang is getting raided. You immediately log into the server and drive over to help, even though your character has no IC way of knowing it was happening."""),
('Random Deathmatch (RDM)',"""You must have clear roleplay reasoning before harming another character. This includes on-foot and vehicle interactions.
Examples:
• You witness an armed robbery between two strangers and, trying to be a hero, immediately attack the shooter without RP buildup. (RDM)
• You’re on foot and see a gang member you don’t like. Without any words, threats, or buildup, you attack and kill them. (RDM + Initiation)"""),
('Initiation of hostilities',"""Before engaging in hostile actions, you must initiate conflict through RP.
Example:
Party 1: “Don’t move or I’ll shoot!”
Party 2: “Don't hurt me!” raises hands.
OR Party 2 (if leverage allows): “You just made your last mistake!” pulls gun → Hostilities commence."""),
('No Value of Life (NVL)',"""Your character should value survival and act accordingly.
Examples:
• Someone has a gun to your head and demands you put your hands up. You refuse or fight back when you have no leverage. (NVL)
• Getting shot and immediately acting like nothing happened, talking normally, not roleplaying your injuries. (NVL)"""),
('Powergaming',"""You cannot force outcomes on others or abuse mechanics to block RP.
Examples:
• Forcing lasting injury without player consent: /me cuts off your hand.
• You place a scene that says “Door is locked, impossible to open or break” – Do NOT expect anyone to honor this in RP. The same applies to surveillance camera scenes and props.
• Running in to a property and locking the door while actively engaged in combat."""),
('Character rules',"""• Do not copy another player’s character concept.
• No vulgar, offensive, or Twitch-breaking character names.
• Characters must be 18+ years old.
• No copyrighted characters or close imitations (eg, roleplaying a famous person that exists IRL).

Playing Multiple Characters
To prevent character bleeding we ask that you do not play more than one LEO (aka be in more than one department at a time) as well as do not play a criminal in more than one GANG at a time. This is to protect you as a community member from potential bans and to protect your RP.

Sci-Fi and Supernatural RP
Characters must remain grounded humans. You can play eccentric beliefs (e.g., a guy who thinks he's a vampire) but the server reality overrides character delusion.

Voice Changers
• Allowed only if not immersion-breaking.
• If your voice mod sounds artificial, robotic, or disruptive, you may be told to remove it.

Text or Mute RP
Not permitted. This is a Voice RP server. If you can't use VOIP, you can't play. (With the exception of medically mute players please open a ticket.)"""),
('Prohibited roleplay topics',"""The following are strictly forbidden:
• Suicide, self-harm.
• Erotic RP.
• Slavery or human trafficking.
• Playing a racist, sexist, or hate group character.
• Rape, sexual assault.
• Reenacting real-world tragedies (e.g., Covid-19, 9/11).
Note: Admins may expand this list at any time."""),
('Staying in-character (IC)',"""Remain in-character at all times.
If someone else breaks character, pivot and keep RP going. Report it later.
Do not use OOC terms like “third eye” or “G muscle” in-character. Find creative ways to express game mechanics.
Do not refer to admins as “Gods”, reports as “prayers”, etc."""),
('Exploiting and glitching',"""Report all bugs/glitches immediately.
Do not exploit bugs (e.g., glitching through walls, loot cycling).
Any gains from exploits will be wiped; punishments will follow."""),
('Server restart rules','No active crimes, robberies, or competitive activities 30 minutes before or after a scheduled server restart.'),
('Criminal group limits',"""• Maximum of 6 active players for any criminal activity.
• Turf/base defense can include anyone already present, but no extra reinforcements can be called in.
• Pre-emptively stacking backup near potential conflict areas counts as a violation."""),
('External communications',"""No using external communications (Discord, TeamSpeak, etc.) to coordinate active RP while in-server.
Allowed:
• Aligning schedules to RP together.
• Pre-planning business or organizational RP (not scenarios).
• Sharing realistic IC files/documents.
Businesses, gangs, and groups can use external servers for out-of-game community building and admin-approved planning only."""),
('Rule interpretation',"""This is not an exhaustive list of rules. Not every possible situation can be covered here. Use common sense, prioritize quality roleplay, and treat others with respect out of character.
Admins have the final say on all rule interpretations, punishments, and disputes.
Attempting to loophole, argue technicalities, or weaponize the rules against other players will not be tolerated.
If you are unsure whether something is allowed, assume it isn't — or ask an Admin beforehand.
We are here to build a strong, fun, and immersive community. Play with that spirit in mind."""),
('Robbing properties of players',"""As of 19th Dec even CLEARER GUIDELINES were published that if not followed you are opening up for a report/suspension/ban of LQRP.
1) Normal rule-following etiquette applies. Properties are not loot crates. Take something, not everything. Don't be an asshole. Pocket wiping rules apply.
2) You MUST leave a scene with SPECIFIC details that WILL lead back to you. “Person with black hair and white socks was here” is NOT enough. Give specifics.
3) Robbing people should be to generate roleplay.
4) You should have a specific reason to rob someone.
5) You should know whose place you broke into.
If not, it's LQRP and you will be pulled into a ticket. Probably suspended, maybe banned. We might just wipe your assets, since you're so okay with people losing theirs.
Thought we wouldn't have to say this — y'all are better than that.
CHAIN ROBBING IS ALSO NOT OK.""")]]
RESPONSE_TEMPLATES=[{'id':str(i),'title':title,'text':text} for i,(title,text) in enumerate([
('Accepted',"""Welcome to the Umbra community 🙂

Please make sure you read the rules before joining:
https://discord.com/channels/1359937307402174554/1359937307456569510
You’ll also find some helpful information here:
https://discord.com/channels/1359937307402174554/1359937307922399488

We’re looking forward to seeing you in the city!

Team Umbra"""),
('Denial introduction',"Hello! At this time your WL Application is being denied, but we have some feedback for your next app!"),
('AI usage issue', 'AI and Honor notice: You answered "yes" to understanding this policy and AI was detected to be heavily present in your answers.\nFeel free to resubmit your application using your own words. Continued use of AI could result in a permanent ban from this community.'),
('Microphone issue','Please ensure you submit a valid and present Vocaroo link or clip from medal/twitch that accurately represents your microphone quality. A simple copy and pasted URL link is best.'),
('OOC terminology','For 10. Q2: Your answer uses OOC terminology. Admins are not to be mentioned IC under any circumstance. This includes Gods, Angels, Government Officials etc... The same applies for reports/tickets and buttons.\nPlease see the server rules here for our policy on referencing game mechanics, admins, reports, etc. https://discord.com/channels/1359937307402174554/1359937307456569510'),
('Incomplete Q2 answer','For 10. Q2: Your response does not fully answer the question presented.'),
('Roleplay definition','Your answer does not demonstrate your understanding of "Roleplay" please review'),
('Metagaming definition','Your answer does not demonstrate your understanding of "meta-gaming" please review'),
('Character example','For 12.Q2: Your response does not give us a good idea of what makes your character interesting. What makes your character stand out from the rest?'),
('Scenario: elaborate personality',"Scenario Questions: While your overall answers fit what we're looking for they do not express any character traits/personality that help us understand how you would really act in character. Please take the time to elaborate a bit on answers."),
('Scenario: value of life',"Scenario Questions: Please take the time to elaborate a bit on answers. Keep in mind your LIFE and your friend's LIFE are potentially at risk. Feel free to frame the scene however you'd like to provide us with an idea of how your character would really act."),
('Denial closing',"We're looking forward to seeing another application from you!\n\nTeam Umbra"),
('Overall low effort','At this time your application is being denied due to overall low effort or lack of understanding. Please review our rules and elaborate on your answers in the future: https://discord.com/channels/1359937307402174554/1359937307456569510')])]
