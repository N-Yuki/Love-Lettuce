#!/usr/bin/env python3
import os, sys, pickle, random, string, time, itertools

class Player:
	def __init__(self):
		# a player's hand
		self.hand = []
		# a player's discard pile
		self.discard = []
		# whether the player is in the game
		self.alive = True
		# wins
		self.score = 0
	def start(self, card):
		self.hand.clear()
		self.discard.clear()
		self.hand.append(card)
		self.alive = True
	# put the player out of game
	def kill(self):
		self.alive = False
		self.discard.extend(self.hand)
		self.hand.clear()

cardlist = [(1, 'Princess'), (1, 'Minister'), (1, 'General'), (2, 'Wizard'), (2, 'Priestess'), (2, 'Knight'), (2, 'Clown'), (5, 'Soldier')]

class LoveLetter:
	def __init__(self, nplayers):
		if nplayers not in range(2, 5):
			raise ValueError('Invalid number of players')
		self.nplayers = nplayers
		self.last_first = random.randrange(0, nplayers)
		self.players = dict((i, Player()) for i in range(nplayers))
		self.new_round()
	def new_round(self):
		# setup deck
		self.deck_init()
		# initialise
		self.setup()
		# create players
		self.player_setup()
		# reset log
		self.log = []
	def deck_init(self):
		# create deck
		self.deck = list(itertools.chain.from_iterable(map(lambda c: c[0] * [c[1]], cardlist)))
		# shuffle deck
		random.shuffle(self.deck)
		# discard 1 card
		self.deck.pop()
	def setup(self):
		# turn and phase init
		self.turn = (self.last_first + 1) % self.nplayers
		self.last_first = self.turn
		self.phase = 0
	def player_setup(self):
		# player hand and notification setup
		for i in self.players:
			self.players[i].start(self.deck.pop())
		self.notify = self.nplayers * ['']
	# the main function
	def next(self, player, pick = '', guess = ''):
		# whether the page should auto-refresh
		refresh = 'true'
		# main message
		msg = ''
		if player not in range(nplayers): # this person is not a player
			msg = 'You are an observer'
		elif self.notify[player] != '':
			msg, self.notify[player] = self.notify[player], ''
		elif player != self.turn: # it is not this player's turn
			if self.phase == 0: 
				msg = 'Another player is drawing'
			elif self.phase == 1: 
				msg = 'Another player has drawn'
			elif self.phase == 2: 
				msg = 'Another player is discarding'
			elif self.phase == 3: 
				msg = 'Another player has discarded'
			elif self.phase == 4: 
				msg = 'Another player has ended their turn'
			elif self.phase == 10: 
				msg = 'Round over'
		else: # it is the player's turn
			cur = self.players[self.turn]
			if self.phase == 0: # draw
				card = self.deck.pop()
				cur.hand.append(card)
				msg = 'You drew ' + card
			elif self.phase == 1: # post-draw
				if 'Minister' in cur.hand and self.hvalue(self.turn) >= 12:
					self.players[self.turn].kill()
					msg = 'Minister has killed you'
				msg = 'No post-draw effect'
			elif self.phase == 2: # discard
				if pick == '': # still deciding
					refresh = 'false'
					msg = 'Choose card to discard:'
					for c in cur.hand:
						msg += '<input type="submit" name="pick" value="' + c + '"/>'
					self.phase -= 1
				else: # decided
					cur.hand.remove(pick)
					cur.discard.append(pick)
					msg = 'You discarded ' + pick
			elif self.phase == 3: # discard effect
				played = cur.discard[-1]
				if played == 'Princess': # suicide discard
					self.players[self.turn].kill()
					msg = 'You discarded the Princess :('
				elif played == 'Minister' or played == 'Priestess': # boring discards
					msg = 'No effect'
				elif pick == '' or self.players[int(pick)].alive == False: # deciding target
					refresh = 'false'
					msg = 'Choose ' + played + ' target:'
					for i in self.players:
						if self.players[i].alive and (i != self.turn or played == 'Wizard'):
							msg += '<input type="submit" name="pick" value="' + str(i) + '"/>'
					self.phase -= 1
				else: # decided target
					pick = int(pick)
					target = self.players[pick]
					self.broadcast(self.turn, pick, played)
					if len(target.discard) == 0 or target.discard[-1] != 'Priestess': # only execute if target's last discard was not a Priestess
						if played == 'General':
							cur.hand, target.hand = target.hand, cur.hand
							msg = 'Swapped hands with Player ' + str(pick)
							self.notify[pick] = 'Swapped hands with Player ' + str(self.turn)
						elif played == 'Wizard':
							target.discard.extend(target.hand)
							target.hand = [self.deck.pop()]
							msg = 'Player ' + str(pick) + ' discarded their hand'
							if pick != self.turn:
								self.notify[pick] = 'Your hand was discarded by Player ' + str(self.turn)
						elif played == 'Knight':
							if self.hvalue(self.turn) > self.hvalue(pick):
								msg = 'Your ' + str(cur.hand) + ' beats their ' + str(target.hand)
								self.notify[pick] = 'Knighted by Player ' + str(self.turn) + ': Their ' + str(cur.hand) + ' beats your ' + str(target.hand)
								self.players[pick].kill()
							elif self.hvalue(self.turn) < self.hvalue(pick):
								msg = 'Your ' + str(cur.hand) + ' loses to their ' + str(target.hand)
								self.notify[pick] = 'Knighted by Player ' + str(self.turn) + ': Their ' + str(cur.hand) + ' loses to your ' + str(target.hand)
								self.players[self.turn].kill()
							else:
								msg = 'Your ' + str(cur.hand) + ' equals their ' + str(target.hand)
								self.notify[pick] = 'Knighted by Player ' + str(self.turn) + ': Their ' + str(cur.hand) + ' equals your ' + str(target.hand)
						elif played == 'Clown':
							msg = 'Their hand was: ' + str(target.hand)
							self.notify[pick] = 'Player ' + str(self.turn) + ' looked at your hand'
						elif played == 'Soldier':
							if guess == '' or guess == 'Soldier':
								refresh = 'false'
								msg = 'Name card:'
								msg += '<input type="hidden" name="pick" value="' + str(pick) + '"/>'
								deck = list(map(lambda c: c[1], cardlist))
								for c in deck:
									if c != 'Soldier':
										msg += '<input type="submit" name="guess" value="' + c + '">'
								self.phase -= 1
							elif target.hand[0] == guess:
								self.players[pick].kill()
								msg = 'You were correct'
								self.notify[pick] = 'Player ' + str(self.turn) + ' named your hand correctly'
							else:
								msg = 'You were incorrect'
								self.notify[pick] = 'Player ' + str(self.turn) + ' guessed your hand to be ' + guess
					else:
						msg = 'Effect ignored'
			elif self.phase == 4: # end turn
				self.change()
				self.phase = -1
				msg = 'End turn'
			elif self.phase == 10: # round over
				msg = 'You win the round'
				self.players[self.turn].score += 1
				self.new_round()
				self.phase -= 1
			self.phase += 1
			if self.nalive() == 1: # move to game over if only one player left
				self.change()
				self.phase = 10
		stats = ''
		for i in self.players:
			stats += 'Player ' + str(i) + ' (score=' + str(self.players[i].score) + ')' + ' Alive: ' + str(self.players[i].alive) + '<br/>'
			#stats += 'Current hand: ' + str(self.players[i].hand) + '<br/>'
			stats += 'Discards: ' + str(self.players[i].discard) + '<br/>'
		stats += '<br/>Your hand: ' + str(self.players[player].hand) + '<br/>'
		self.log.append(msg)
		resp = {'msg': stats + '<strong>' + msg + '</strong>', 'refresh': refresh, 'log': '<br/>'.join(self.log[:-11:-1])}
		return resp
	# notify players about a public event
	def broadcast(self, s, t, evt):
		for i in self.players:
			if i != s and i != t:
				self.notify[i] = 'Player ' + str(s) + ' ' + evt + 'ing Player ' + str(t)
	# count the number of players in game
	def nalive(self):
		alive = 0
		for i in self.players:
			if self.players[i].alive:
				alive += 1
		return alive
	# calculate the value of a players hand
	def hvalue(self, who):
		cvalue = {'Princess': 8, 'Minister': 7, 'General': 6, 'Wizard': 5, 'Priestess': 4, 'Knight': 3, 'Clown': 2, 'Soldier': 1}
		v = 0
		for c in self.players[who].hand:
			v += cvalue[c]
		return v
	# rotate to next player still in game
	def change(self):
		self.turn = (self.turn + 1) % self.nplayers
		while self.players[self.turn].alive == False:
			self.turn = (self.turn + 1) % self.nplayers

def lobby(env):
	# generate HTML list of rooms
	rooms = '<ul>\n\t'
	for room in os.listdir('rooms'):
		rooms += string.Template('\t<li><a href="/game?room=$room">$room</a></li>\n\t').safe_substitute(room=room)
	rooms += '</ul>'
	# generate HTML
	with open('template/lobby.html', 'r') as f:
		html = string.Template(f.read()).safe_substitute(rooms=rooms)
	return [bytes(html, 'utf-8')]

def create(env):
	# extract the GET arguments
	get = env['QUERY_STRING'].split('&')
	# default values for query
	query = {'room': hex(int(time.time()))[2:], 'players': 2}
	try: # try create game
		# parse the GET arguments
		query = dict(qc.split('=') for qc in get)
		room = query['room']
		# create game
		game = LoveLetter(int(query['players']))
		# save game state
		with open('rooms/' + room + '.pickle', 'wb') as f:
			pickle.dump(game, f)
		# redirect user to created game
		with open('template/redirect.html', 'r') as f:
			url = '/game?room=' + room
			html = string.Template(f.read()).safe_substitute(url=url)
		return [bytes(html, 'utf-8')]
	except: # send form for creating game instead
		with open('template/create.html', 'r') as f:
			html = string.Template(f.read()).safe_substitute(query)
		return [bytes(html, 'utf-8')]

def game(env):
	# extract the GET arguments
	get = env['QUERY_STRING'].split('&')
	try:
		# parse the GET arguments
		query = dict(qc.split('=') for qc in get)
		room = query['room']
		# load game state
		with open('rooms/' + room + '.pickle', 'rb') as f:
			game = pickle.load(f)
		# cast 'player' into an int, defaulting to -1
		player = int(query.get('player', -1))
		# apply action
		resp = game.next(player, query['pick'], query['guess'])
		# save game state
		with open('rooms/' + room + '.pickle', 'wb') as f:
			pickle.dump(game, f)
		# generate HTML
		with open('template/game.html', 'r') as f:
			html = string.Template(f.read()).safe_substitute(room=room, player=player, resp=resp['msg'], log=resp['log'], refresh=resp['refresh'])
		return [bytes(html, 'utf-8')]
	except:
		return invalid(env)

def play(env):
	return invalid(env)

def invalid(env):
	with open('template/404.html', 'r') as f:
		html = string.Template(f.read()).safe_substitute(env)
	return [bytes(html, 'utf-8')]

# entry point
def application(env, start_response):
	path = env['PATH_INFO']
	if path == '/':
		start_response('200 OK', [('Content-Type','text/html')])
		return lobby(env)
	elif path == '/new':
		start_response('200 OK', [('Content-Type','text/html')])
		return create(env)
	elif path == '/game':
		start_response('200 OK', [('Content-Type','text/html')])
		return game(env)
	elif path == '/play':
		start_response('200 OK', [('Content-Type','text/html')])
		return play(env)
	else:
		start_response('404 Not Found', [('Content-Type','text/html')])
		return invalid(env)
